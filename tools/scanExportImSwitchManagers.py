import pkgutil
import inspect
import importlib

def categorize_classes(found_classes):
    categorized = {
        "DetectorManager": [],
        "LaserManager": [],
        "LEDMatrixManager": [],
        "PositionerManager": [],
        "StandsManager": [],
        "RotatorManager": [],
        "SuperScanManager": [],
        "SignalInterface": []
    }
    
    # Iterate over the found classes and their parents
    for class_path, parents in found_classes.items():
        # Check if any of the manager classes are in the parents list
        for manager in categorized.keys():
            if manager in parents:
                # Append the class (with its path) to the corresponding category
                categorized[manager].append(class_path)
                break  # Assume each class belongs to only one category for simplicity
    
    return categorized

def list_classes_and_parents(package, package_name=None, package_prefix="manager"):
    found_classes = {}
    if package_name is None:
        package_name = package.__name__
    
    # Iterate over all modules and sub-packages in the given package
    for finder, modname, ispkg in pkgutil.walk_packages(package.__path__, prefix=package.__name__+'.'):
        # For a sub-package, recursively call this function
        if ispkg:
            subpackage = importlib.import_module(modname)
            found_classes.update(list_classes_and_parents(subpackage, package_name=modname))
        else:
            # Import the module
            try:
                module = importlib.import_module(modname)
            except Exception as e:
                #print(f"Error importing {modname}: {e}")
                continue
            # Iterate over all members of the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Filter classes that are defined in this module (to avoid imported ones)
                if obj.__module__.startswith(package_name):
                    if obj.__module__.lower().find(package_prefix)>=0:
                        #print(obj.__module__)
                        # Get parent classes excluding 'object'
                        parents = [base.__name__ for base in inspect.getmro(obj) if base.__name__ != 'object' and base.__module__.startswith(package_name)]
                        found_classes[obj.__module__ + "." + name] = parents
                    

    return found_classes

# Example usage:
# First, import the package you're interested in
import imswitch
# Then, call the function with the package as argument
classes_and_parents = list_classes_and_parents(imswitch, "manager")
categorized_classes = categorize_classes(classes_and_parents)


for manager, classes in categorized_classes.items():
    print(f"{manager}:")
    for cls in classes:
        print(f"  - {cls}")
        
        
'''RESULT'''

allManagers = {
   "DetectorManager":[
      "imswitch.imcontrol.model.managers.detectors.APDManager.APDManager",
      "imswitch.imcontrol.model.managers.detectors.DetectorManager.DetectorManager",
      "imswitch.imcontrol.model.managers.detectors.AVManager.AVManager",
      "imswitch.imcontrol.model.managers.detectors.BaslerManager.BaslerManager",
      "imswitch.imcontrol.model.managers.detectors.ESP32CamManager.ESP32CamManager",
      "imswitch.imcontrol.model.managers.detectors.ESP32SerialCamManager.ESP32SerialCamManager",
      "imswitch.imcontrol.model.managers.detectors.GXPIPYManager.GXPIPYManager",
      "imswitch.imcontrol.model.managers.detectors.HamamatsuManager.HamamatsuManager",
      "imswitch.imcontrol.model.managers.detectors.HikCamManager.HikCamManager",
      "imswitch.imcontrol.model.managers.detectors.JetsonCamManager.JetsonCamManager",
      "imswitch.imcontrol.model.managers.detectors.OFMCamManager.OFMCamManager",
      "imswitch.imcontrol.model.managers.detectors.OpenCVCamManager.OpenCVCamManager",
      "imswitch.imcontrol.model.managers.detectors.PCOManager.PCOManager",
      "imswitch.imcontrol.model.managers.detectors.PhotometricsManager.PhotometricsManager",
      "imswitch.imcontrol.model.managers.detectors.PiCamManager.PiCamManager",
      "imswitch.imcontrol.model.managers.detectors.TEMPLATECamManager.TEMPLATECamManager",
      "imswitch.imcontrol.model.managers.detectors.TISManager.TISManager",
      "imswitch.imcontrol.model.managers.detectors.ThorCamSciManager.ThorCamSciManager",
      "imswitch.imcontrol.model.managers.detectors.ThorCamSciManager__.ThorCamSciManager",
      "..."
   ],
   "LaserManager":[
      "imswitch.imcontrol.model.managers.lasers.AAAOTFLaserManager.AAAOTFLaserManager",
      "imswitch.imcontrol.model.managers.lasers.LaserManager.LaserManager",
      "imswitch.imcontrol.model.managers.lasers.Cobolt0601LaserManager.Cobolt0601LaserManager",
      "imswitch.imcontrol.model.managers.lasers.LantzLaserManager.LantzLaserManager",
      "imswitch.imcontrol.model.managers.lasers.CoboltLaserManager.CoboltLaserManager",
      "imswitch.imcontrol.model.managers.lasers.CoolLEDLaserManager.CoolLEDLaserManager",
      "imswitch.imcontrol.model.managers.lasers.ESP32LEDLaserManager.ESP32LEDLaserManager",
      "imswitch.imcontrol.model.managers.lasers.ESP32LightSheetManager.ESP32LightsheetManager",
      "imswitch.imcontrol.model.managers.lasers.PyMicroscopeLaserManager.PyMicroscopeLaserManager",
      "imswitch.imcontrol.model.managers.lasers.SQUIDLaserManager.SQUIDLaserManager",
      "imswitch.imcontrol.model.managers.lasers.SQUIDLedManager.SQUIDLedManager",
      "imswitch.imcontrol.model.managers.lasers.VirtualLaserManager.VirtualLaserManager"
   ],
   "LEDMatrixManager":[
      "imswitch.imcontrol.model.managers.LEDMatrixs.ESP32LEDMatrixManager.ESP32LEDMatrixManager",
      "imswitch.imcontrol.model.managers.LEDMatrixs.LEDMatrixManager.LEDMatrixManager"
   ],
   "PositionerManager":[
      "imswitch.imcontrol.model.managers.positioners.ESP32StageManager.ESP32StageManager",
      "imswitch.imcontrol.model.managers.positioners.PositionerManager.PositionerManager",
      "imswitch.imcontrol.model.managers.positioners.MHXYStageManager.MHXYStageManager",
      "imswitch.imcontrol.model.managers.positioners.MockPositionerManager.MockPositionerManager",
      "imswitch.imcontrol.model.managers.positioners.OFMStageManager.OFMStageManager",
      "imswitch.imcontrol.model.managers.positioners.PiezoconceptZManager.PiezoconceptZManager",
      "imswitch.imcontrol.model.managers.positioners.VirtualStageManager.VirtualStageManager"
   ],
   "StandsManager":[
      
   ],
   "RotatorManager":[
      
   ],
   "SuperScanManager":[
      "imswitch.imcontrol.model.managers.ScanManagerBase.ScanManagerBase",
      "imswitch.imcontrol.model.managers.ScanManagerMoNaLISA.ScanManagerMoNaLISA",
      "imswitch.imcontrol.model.managers.ScanManagerPointScan.ScanManagerPointScan",
      "imswitch.imcontrol.model.managers.ScanManager.ScanManager",
      "imswitch.imcontrol.model.managers.ScanManager.SuperScanManager",
      "imswitch.imcontrol.model.managers.ScanManagerBase.SuperScanManager"
   ],
   "SignalInterface":[
      
   ]
}