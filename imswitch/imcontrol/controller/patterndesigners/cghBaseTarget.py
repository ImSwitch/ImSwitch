from abc import ABC, abstractmethod
from imswitch.imcommon.model import initLogger
import traceback

class TargetBase(ABC):
    """
    Base class for all CGH targets.
    """
    target_type: str = None # to be defined in sub-class

    def __init__(self,section_size=None,**params):
        self.__logger = initLogger(self)

        if self.target_type is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define target_type"
            )
        
        
        self.section_size = section_size

        self.params = params
        self.update_params()
        self.array = None               # computed target
        self.name = None                # custom name with all parameters defined for each target
        self.feedback_count = 0         # feedback round counter
        self.analysis_history = []      # list of dicts from analyze_result()
        self.analysis_performed = False
        self.analysis_prm = {}          # to be set with default parameters in sub-class constructor

        self.conversion_factor_dict = None   # dict {"x:" value, "y:" value}

        # Build target and create its custom name (sub-class methods)
        self.array = self.build()
        self.name = self.create_target_name()

    
    # ---- feedback properties ----- #
    @property
    def supports_feedback(self) -> bool:
        """By default: target type does NOT support adaptive correction."""
        return False
    
    
    # ---- calibration properties ----- #
    @property
    def needs_calibration(self) -> bool:
        """By default: target type does NOT need calibration."""
        return False
    
    @property
    def calib_params(self):
        """ List of parameters needed to perform calibration as a list of tuple:
            [
            ("param_name, default, ptype"),
            ("param_name, default, ptype"),
            ]
        Must be defined in child class if needs_calibration=True.
        """
        return None
    
    # ---- general methods ----- #

    def build(self):
        if self.needs_calibration:
            c = self.conversion_factor_dict
            if not c or not isinstance(c,dict):
                self.__logger.warning("skipping build, conversion facot misssing")
                return None
            # if not c:
            #     msg = f"[{self.__class__.__name__}] needs conversion factor."
            #     raise ValueError(msg)
            # if not isinstance(c,dict):
            #     msg = f"conversion_factor_dict should be a dict"
            #     raise TypeError(msg)
            # if c.get("x") is None or c.get("y") is None:
            #     msg = f"conversion_factor_dict should be a dict with 'x' and 'y' keys"
            #     raise ValueError(msg)
        
        array = self._build_impl()
        return array
    
    @abstractmethod
    def _build_impl(self):
        """ Specific target build, which children class should implement.
        Returns a 2D array representing the target."""
        pass

    @abstractmethod
    def create_target_name(self):
        """Return string name for the target."""
        pass
    

    def update_params(self, **new_params) -> bool:
        """
        Update target parameters only if they changed.
        If changed and feedback allowed: reset feedback.
        Returns True if parameters were updated, False otherwise.
        """

        changed = False

        for key, new_val in new_params.items():
            old_val = self.params.get(key)

            if old_val != new_val:
                changed = True
                self._set_param(key, new_val)

        if changed and self.supports_feedback:
            self.reset_feedback()

        return changed
    
    def _set_param(self, key, value):
        """
        Default behavior: directly update params.
        Subclasses can override this to route specific params through setters.
        """
        self.params[key] = value

    # ----- feedback related ----- *

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
            msg = f"[{self.__class__.__name__}] Feedback not supported."
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
            msg = f"[{self.__class__.__name__}] Feedback not supported."
            self.__logger.error(msg)
            return False, msg

        if not self.analysis_performed:
            msg = f"[{self.__class__.__name__}] Cannot adapt: no analysis performed."
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

    def _adapt_target_impl(self, *args, **kwargs):
        """Subclasses with feedback support must implement this."""
        pass
    
    def _analyze_result_impl(self, *args, **kwargs):
        """Subclasses with feedback support must implement this."""
        pass

    def _feedback_reset(self, *args, **kwargs):
        """Optional method for additional feedback reset features."""
        pass

        
    # ----- calibration related ----- *
    
    def calibrate(self,calib_values):
        if not self.needs_calibration:
            self.__logger.error(f"Target {self.target_type} does not allow calibration.")
            return None
        
        try:
            conv_factor_dict = self._calibration_impl(calib_values)
            self.conv_factor = conv_factor_dict
            return conv_factor_dict
        except Exception as e:
            self.__logger.error(f"Calibration failed: {e}")
            return None

    def _calibration_impl(self, calib_values): 
        """Subclasses with calibration should implement their target-specific 
        calibration logic. Should return conversion factor dictionnary based on 
        calib_values."""
        pass