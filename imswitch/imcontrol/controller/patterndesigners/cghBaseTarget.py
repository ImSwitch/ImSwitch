from abc import ABC, abstractmethod
from imswitch.imcommon.model import initLogger
import traceback
import numpy as np
from .slmSectionCalibration import SLMSectionCalibration

_UNSET = object()

class TargetBase(ABC):
    """
    Base class for all CGH targets.
    """

    target_type: str = None 
    target_params = []

    _supports_feedback = False
    _needs_calibration = False
    _auto_update_param = False
    _needs_section_size = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        
        if getattr(cls, "target_type", None) is None:
            return
        
        # check that children defines target_params
        prm = cls.__dict__.get("target_params",None)
        if prm is None or not isinstance(prm, list) or len(prm)==0:
            raise TypeError(
                f"{cls.__name__} must define target_params as a non-empty list."
            )

        # Enforce feedback implementation if the child declares feedback support.
        if getattr(cls, "_supports_feedback", False):
            for method_name in ("_analyze_result_impl", "_adapt_target_impl"):
                child_method = getattr(cls, method_name, None)
                base_method = getattr(TargetBase, method_name)

                if child_method is base_method:
                    raise TypeError(
                        f"{cls.__name__} has _supports_feedback=True "
                        f"but does not implement {method_name}()."
                    )

    def __init__(self,section_size=None,section_calibration=None,**params):
        self.__logger = initLogger(self)

        if self.target_type is None:
            raise NotImplementedError(
                f"{self._target_type} must define target_type"
            )
        
        self.section_size = self._coerce_section_size(section_size)

        if isinstance(section_calibration,SLMSectionCalibration):
            self.section_calibration = section_calibration
        elif isinstance(section_calibration, dict):
            self.section_calibration = SLMSectionCalibration.from_dict(section_calibration)
        else:
            self.section_calibration=None
        

        self.feedback_count = 0         # feedback round counter
        self.analysis_history = []      # list of dicts from analyze_result()
        self.analysis_performed = False
        self.analysis_prm = {}          # to be set with default parameters in sub-class constructor

        # init params
        self.params = {}
        self.init_params(params)

        # build array and target name
        self.name=None
        self.array=None
        self.rebuild()


    # ----- Properties ----- #
    @property
    def supports_feedback(self) -> bool:
        """By default: target type does NOT support adaptive correction."""
        return self._supports_feedback

    @property
    def needs_calibration(self) -> bool:
        """By default: target type does NOT need calibration."""
        return self._needs_calibration
    
    @property
    def needs_section_size(self) -> bool:
        """By default: target type does NOT need the section_size."""
        return self._needs_section_size
    
    @property
    def has_valid_section_calibration(self):
        return self.section_calibration is not None and self.section_calibration.is_valid()
    

    # --- Runtime context from controller: section size, calibration --- #
    def set_section_calibration(self, section_calibration, rebuild=True) -> bool:
        """ Set section calibration, rebuild if needed, and returns boolean flag 
        indicating if this led to changes and new build of the target. """
        if not self.needs_calibration:
            return False
        
        calibration = SLMSectionCalibration.from_dict(section_calibration)
        old = (
            self.section_calibration.to_dict()
            if self.section_calibration is not None
            else None
        )
        new = calibration.to_dict()
        if old == new:
            return False

        self.section_calibration = calibration
        
        if rebuild:
            self.rebuild()

        return True

    def set_section_size(self, section_size, rebuild=True) -> bool:
        """ Set section sizerebuild if needed, and returns boolean flag 
        indicating if this led to changes and new build of the target. """

        if not self.needs_section_size:
            return False
        
        section_size = self._coerce_section_size(section_size)
        
        if section_size is None:
            raise ValueError(
                f"{self.target_type} requires a valid section_size."
            )
        
        if self.section_size == section_size:
            return False

        self.section_size = section_size
        
        if rebuild:
            self.rebuild()
        return True
    
    @staticmethod
    def _coerce_section_size(section_size):
        if section_size is None:
            return None
        if len(section_size) != 2:
            raise ValueError(f"section_size must be (height, width), got {section_size}")

        height = int(section_size[0])
        width = int(section_size[1])
        if height <= 0 or width <= 0:
            raise ValueError(f"section_size must be positive, got {section_size}")
        return height, width


    # ---- general methods ----- #
    def build(self) -> np.ndarray:
        """ Build target array, calling child class implementation. """
        if self.needs_calibration and not self.has_valid_section_calibration:    
                msg = f"{self.target_type} needs calibration but calibration not valid"
                raise ValueError(msg)
        if self.needs_section_size and self.section_size is None:
                msg = f"{self.target_type} needs section size but section size is None"
                raise ValueError(msg)

        array = self._build_impl()
        return array
    
    def rebuild(self):
        """Rebuild target array and name."""
        self.array = self.build()
        self.name = self.create_target_name()
        return self.array
    
    def _set_param(self, key, value):
        """
        Route through a property setter when one exists.
        Otherwise update self.params directly.
        """
        descriptor = getattr(type(self), key, None)

        if isinstance(descriptor, property) and descriptor.fset is not None:
            setattr(self, key, value)
        else:
            self.params[key] = value

    def init_params(self,params):
        self.params = dict(params)
        for key, value in params.items():
            self._set_param(key, value)

    def update_params(self, new_section_size=_UNSET, new_calibration=_UNSET, **new_params) -> bool:
        """
        Update target parameters only if they changed.
        If changed and feedback allowed: reset feedback.
        Returns True if parameters were updated, False otherwise.
        """

        calib_changed = False
        section_size_changed = False
        params_changed = False

        if self.needs_section_size and new_section_size is not _UNSET:
            section_size_changed = self.set_section_size(new_section_size, 
                                                         rebuild=False)

        if self.needs_calibration and new_calibration is not _UNSET:
            calib_changed = self.set_section_calibration(new_calibration, 
                                                         rebuild=False)

        for key, new_val in new_params.items():
            old_val = self.params.get(key)

            if old_val != new_val:
                params_changed = True
                self._set_param(key, new_val)
        
        changed = params_changed or calib_changed or section_size_changed
        if changed:
            self._on_target_changed(params_changed,section_size_changed,calib_changed)
            if self.supports_feedback:
                self.reset_feedback()
            self.rebuild()

        return changed
    
    def update_single_param(self,param_name,value):
        """ Update a single parameter with value and returns boolean indicating
        if value changed or not. Triggers rebuild if value changed. """
        if param_name not in self.params:
            self.__logger.error(f"Trying to update {param_name} which doesn't exist"
                                f" for target {self.target_type}.")
            return False
        
        old_val = self.params.get(param_name)
        if old_val!=value:
            self._set_param(param_name,value)
            self._on_target_changed()
            if self.supports_feedback:
                self.reset_feedback()
            self.rebuild()
            return True
        else:
            return False
    
    def get_target_params(self):
        return self.params


    # ----- feedback related ----- 
    def analyze_result(self, experimental_result,params=None,show_plot=True):
        """
        Template method:
            1. Check support for feedback
            2. Updates self.analysis_prm with params
            2. Call subclass implementation
            3. If success, set `self.analysis_performed` to True and updates `self.analysis_history`
            4. return success boolean + optional msg
        """
        if not self.supports_feedback:
            msg = f"[{self._target_type}] Feedback not supported."
            self.__logger.error(msg)
            return False, msg

        if params is not None:
            self.update_analyze_prm(params)

        try:
            analysis = self._analyze_result_impl(experimental_result,show_plot)

            # if analysis_performed still True, it means "adapt_target" did not run yet,
            # so we replace last analysis result with new ones. Otherwise we append.
            if self.analysis_performed and len(self.analysis_history)!=0: 
                self.analysis_history[-1] = analysis
            else:
                self.analysis_history.append(analysis)

            self.analysis_performed = True
            return True, None

        except Exception as e:
            self.__logger.error(traceback.format_exc())
            return False, e

    def update_analyze_prm(self,params):
        """ Updates analysis parameters with `params` (only updates existing keys) """
        for k in self.analysis_prm:
            if k in params:
                self.analysis_prm[k] = params[k]

    def adapt_target(self, *args, **kwargs):
        """
        Template method:
            1. Check support for feedback
            2. Check analysis has been done
            3. Call subclass implementation (returning new target array or None if Failed)
            4. If sucess, updates `self.array` with new target, and:
                        - updates `self.feedback_count` (+1 if success)
                        - call create_target_name to update name w/ feedback_count
                        - set `self.analysis_performed` to False.
            5. return success boolean + optional msg
        """
        if not self.supports_feedback:
            msg = f"[{self._target_type}] Feedback not supported."
            self.__logger.error(msg)
            return False, msg

        if not self.analysis_performed:
            msg = f"[{self._target_type}] Cannot adapt: no analysis performed."
            self.__logger.warning(msg)
            return False, msg

        # Delegate custom logic to subclass
        new_target,msg = self._adapt_target_impl(*args, **kwargs)

        if new_target is not None:
            self.array = new_target
            self.feedback_count += 1
            self.name = self.create_target_name()
            self.analysis_performed = False
            return True, None
        else:
            return False, msg

    def reset_feedback(self):
        """Clear feedback and rebuild."""
        if self.supports_feedback:
            self.feedback_count = 0
            self.analysis_history.clear()
            self.array = self.build()
            self.name = self.create_target_name()
            self._feedback_reset()

                
        
    # ----- Hooks for subclasses ----- 
    @abstractmethod
    def _build_impl(self) -> np.ndarray:
        """ Specific target build, which children class should implement.
        Returns a 2D array representing the target."""
        pass

    @abstractmethod
    def create_target_name(self) -> str:
        """Return string name for the target."""
        pass

    def _on_target_changed(self,*args,**kwargs):
        """
        For target-specific changes that needs to be done before calling rebuild().
        """
        pass


    def _adapt_target_impl(self, *args, **kwargs):
        """Subclasses with feedback support must implement this."""
        pass
    
    def _analyze_result_impl(self, *args, **kwargs):
        """Subclasses with feedback support must implement this."""
        pass

    def _feedback_reset(self, *args, **kwargs):
        """Optional method for additional feedback reset features."""
        pass