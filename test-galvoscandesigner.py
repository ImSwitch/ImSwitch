from imswitch.imcontrol.model.signaldesigners.GalvoScanDesigner import GalvoScanDesigner
from imswitch.imcontrol.model.signaldesigners.PointScanTTLCycleDesigner import PointScanTTLCycleDesigner
from imswitch.imcontrol.view.guitools.ViewSetupInfo import ViewSetupInfo
from imswitch.imcontrol.model.SetupInfo import ScanInfo, PositionerInfo

import matplotlib.pyplot as plt


# SET 1 - XYRT
parameterDict11 = {'target_device': ['ND-GalvoX', 'ND-GalvoY', 'Mock-Repeat', 'Mock-Timelapse', 'ND-PiezoZ'],
                 'axis_length': [0.7, 0.7, 1.0, 1.0, 1.0],
                 'axis_step_size': [0.1, 0.1, 1.0, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['ND-GalvoX', 'ND-GalvoY', 'None', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}
ttlparameterDict1 = {'target_device': ['640'], 'TTL_sequence': ['h1'], 'TTL_sequence_axis': ['None'], 'sequence_time': 2e-05}
ttlparameterDict1 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['ND-GalvoX'], 'sequence_time': 2e-05}
ttlparameterDict1 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['ND-GalvoY'], 'sequence_time': 2e-05}
ttlparameterDict1 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['Mock-Repeat'], 'sequence_time': 2e-05}
ttlparameterDict1 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1,h1'], 'TTL_sequence_axis': ['Mock-Timelapse'], 'sequence_time': 2e-05}
ttlparameterDict1 = {'target_device': ['640'], 'TTL_sequence': ['l1'], 'TTL_sequence_axis': ['Mock-Timelapse'], 'sequence_time': 2e-05}

parameterDict12 = {'target_device': ['ND-GalvoX', 'ND-GalvoY', 'Mock-Repeat', 'Mock-Timelapse', 'ND-PiezoZ'],
                 'axis_length': [0.5, 0.5, 3.0, 1.0, 1.0],
                 'axis_step_size': [0.1, 0.1, 1.0, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['ND-GalvoX', 'ND-GalvoY', 'Mock-Repeat', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}

parameterDict13 = {'target_device': ['ND-GalvoX', 'ND-GalvoY', 'Mock-Repeat', 'Mock-Timelapse', 'ND-PiezoZ'],
                 'axis_length': [0.5, 0.5, 3.0, 3.0, 1.0],
                 'axis_step_size': [0.1, 0.1, 1.0, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['ND-GalvoX', 'ND-GalvoY', 'Mock-Repeat', 'Mock-Timelapse', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}

# SET 2 - RXYT
parameterDict21 = {'target_device': ['Mock-Repeat', 'ND-GalvoY', 'ND-GalvoX', 'Mock-Timelapse', 'ND-PiezoZ'],
                 'axis_length': [3.0, 0.5, 1.0, 1.0, 1.0],
                 'axis_step_size': [1.0, 0.1, 1.0, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['Mock-Repeat', 'ND-GalvoY', 'None', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}
ttlparameterDict2 = {'target_device': ['640'], 'TTL_sequence': ['h1'], 'TTL_sequence_axis': ['None'], 'sequence_time': 2e-05}
ttlparameterDict2 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['Mock-Repeat'], 'sequence_time': 2e-05}
ttlparameterDict2 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['ND-GalvoY'], 'sequence_time': 2e-05}
ttlparameterDict2 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1,h1'], 'TTL_sequence_axis': ['ND-GalvoX'], 'sequence_time': 2e-05}
ttlparameterDict2 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1,h1'], 'TTL_sequence_axis': ['Mock-Timelapse'], 'sequence_time': 2e-05}
ttlparameterDict2 = {'target_device': ['640'], 'TTL_sequence': ['l1'], 'TTL_sequence_axis': ['Mock-Timelapse'], 'sequence_time': 2e-05}

parameterDict22 = {'target_device': ['Mock-Repeat', 'ND-GalvoY', 'ND-GalvoX', 'Mock-Timelapse', 'ND-PiezoZ'],
                 'axis_length': [3.0, 0.5, 0.5, 1.0, 1.0],
                 'axis_step_size': [1.0, 0.1, 0.1, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['Mock-Repeat', 'ND-GalvoY', 'ND-GalvoX', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}

parameterDict23 = {'target_device': ['Mock-Repeat', 'ND-GalvoY', 'ND-GalvoX', 'Mock-Timelapse', 'ND-PiezoZ'],
                 'axis_length': [3.0, 0.5, 0.5, 3.0, 1.0],
                 'axis_step_size': [1.0, 0.1, 0.1, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['Mock-Repeat', 'ND-GalvoY', 'ND-GalvoX', 'Mock-Timelapse', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}

# SET 3 - XRYT
parameterDict31 = {'target_device': ['ND-GalvoY', 'Mock-Repeat', 'ND-GalvoX', 'Mock-Timelapse', 'ND-PiezoZ'],
                 'axis_length': [0.5, 3.0, 1.0, 1.0, 1.0],
                 'axis_step_size': [0.1, 1.0, 1.0, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['ND-GalvoY', 'Mock-Repeat', 'None', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}
ttlparameterDict3 = {'target_device': ['640'], 'TTL_sequence': ['h1'], 'TTL_sequence_axis': ['None'], 'sequence_time': 2e-05}
ttlparameterDict3 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['ND-GalvoY'], 'sequence_time': 2e-05}
ttlparameterDict3 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['Mock-Repeat'], 'sequence_time': 2e-05}
ttlparameterDict3 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['ND-GalvoX'], 'sequence_time': 2e-05}
ttlparameterDict3 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1,h1'], 'TTL_sequence_axis': ['Mock-Timelapse'], 'sequence_time': 2e-05}
ttlparameterDict3 = {'target_device': ['640'], 'TTL_sequence': ['l1'], 'TTL_sequence_axis': ['Mock-Timelapse'], 'sequence_time': 2e-05}

parameterDict32 = {'target_device': ['ND-GalvoY', 'Mock-Repeat', 'ND-GalvoX', 'Mock-Timelapse', 'ND-PiezoZ'],
                 'axis_length': [0.5, 3.0, 0.5, 1.0, 1.0],
                 'axis_step_size': [0.1, 1.0, 0.1, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['ND-GalvoY', 'Mock-Repeat', 'ND-GalvoX', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}

parameterDict33 = {'target_device': ['ND-GalvoY', 'Mock-Repeat', 'ND-GalvoX', 'Mock-Timelapse', 'ND-PiezoZ'],
                 'axis_length': [0.5, 3.0, 0.5, 3.0, 1.0],
                 'axis_step_size': [0.1, 1.0, 0.1, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['ND-GalvoY', 'Mock-Repeat', 'ND-GalvoX', 'Mock-Timelapse', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}

# SET 4 - XRTY
parameterDict41 = {'target_device': ['ND-GalvoY', 'Mock-Repeat', 'Mock-Timelapse', 'ND-GalvoX', 'ND-PiezoZ'],
                 'axis_length': [0.5, 3.0, 1.0, 1.0, 1.0],
                 'axis_step_size': [0.1, 1.0, 1.0, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['ND-GalvoY', 'Mock-Repeat', 'None', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}
ttlparameterDict4 = {'target_device': ['640'], 'TTL_sequence': ['h1'], 'TTL_sequence_axis': ['None'], 'sequence_time': 2e-05}
ttlparameterDict4 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['ND-GalvoY'], 'sequence_time': 2e-05}
ttlparameterDict4 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['Mock-Repeat'], 'sequence_time': 2e-05}
ttlparameterDict4 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['Mock-Timelapse'], 'sequence_time': 2e-05}
ttlparameterDict4 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1,h1'], 'TTL_sequence_axis': ['ND-GalvoX'], 'sequence_time': 2e-05}
ttlparameterDict4 = {'target_device': ['640'], 'TTL_sequence': ['l1'], 'TTL_sequence_axis': ['ND-GalvoX'], 'sequence_time': 2e-05}

parameterDict42 = {'target_device': ['ND-GalvoY', 'Mock-Repeat', 'Mock-Timelapse', 'ND-GalvoX', 'ND-PiezoZ'],
                 'axis_length': [0.5, 3.0, 3.0, 1.0, 1.0],
                 'axis_step_size': [0.1, 1.0, 1.0, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['ND-GalvoY', 'Mock-Repeat', 'Mock-Timelapse', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}

parameterDict43 = {'target_device': ['ND-GalvoY', 'Mock-Repeat', 'Mock-Timelapse', 'ND-GalvoX', 'ND-PiezoZ'],
                 'axis_length': [0.5, 3.0, 3.0, 0.5, 1.0],
                 'axis_step_size': [0.1, 1.0, 1.0, 0.1, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['ND-GalvoY', 'Mock-Repeat', 'Mock-Timelapse', 'ND-GalvoX', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}


# SET 5 - RTXY
parameterDict51 = {'target_device': ['Mock-Repeat', 'Mock-Timelapse', 'ND-GalvoY', 'ND-GalvoX', 'ND-PiezoZ'],
                 'axis_length': [3.0, 3.0, 1.0, 1.0, 1.0],
                 'axis_step_size': [1.0, 1.0, 1.0, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['Mock-Repeat', 'Mock-Timelapse', 'None', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}
ttlparameterDict5 = {'target_device': ['640'], 'TTL_sequence': ['h1'], 'TTL_sequence_axis': ['None'], 'sequence_time': 2e-05}
ttlparameterDict5 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['Mock-Repeat'], 'sequence_time': 2e-05}
ttlparameterDict5 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['Mock-Timelapse'], 'sequence_time': 2e-05}
ttlparameterDict5 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['ND-GalvoY'], 'sequence_time': 2e-05}
ttlparameterDict5 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1,h1'], 'TTL_sequence_axis': ['ND-GalvoX'], 'sequence_time': 2e-05}
ttlparameterDict5 = {'target_device': ['640'], 'TTL_sequence': ['l1'], 'TTL_sequence_axis': ['ND-GalvoX'], 'sequence_time': 2e-05}

parameterDict52 = {'target_device': ['Mock-Repeat', 'Mock-Timelapse', 'ND-GalvoY', 'ND-GalvoX', 'ND-PiezoZ'],
                 'axis_length': [3.0, 3.0, 0.5, 1.0, 1.0],
                 'axis_step_size': [1.0, 1.0, 0.1, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['Mock-Repeat', 'Mock-Timelapse', 'ND-GalvoY', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}

parameterDict53 = {'target_device': ['Mock-Repeat', 'Mock-Timelapse', 'ND-GalvoY', 'ND-GalvoX', 'ND-PiezoZ'],
                 'axis_length': [3.0, 3.0, 0.5, 0.5, 1.0],
                 'axis_step_size': [1.0, 1.0, 0.1, 0.1, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['Mock-Repeat', 'Mock-Timelapse', 'ND-GalvoY', 'ND-GalvoX', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}

# SET 6 - RXTY
parameterDict61 = {'target_device': ['Mock-Repeat', 'ND-GalvoY', 'Mock-Timelapse', 'ND-GalvoX', 'ND-PiezoZ'],
                 'axis_length': [3.0, 0.5, 1.0, 1.0, 1.0],
                 'axis_step_size': [1.0, 0.1, 1.0, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['Mock-Repeat', 'ND-GalvoY', 'None', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}
ttlparameterDict6 = {'target_device': ['640'], 'TTL_sequence': ['h1'], 'TTL_sequence_axis': ['None'], 'sequence_time': 2e-05}
ttlparameterDict6 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['Mock-Repeat'], 'sequence_time': 2e-05}
ttlparameterDict6 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['ND-GalvoY'], 'sequence_time': 2e-05}
ttlparameterDict6 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1'], 'TTL_sequence_axis': ['Mock-Timelapse'], 'sequence_time': 2e-05}
ttlparameterDict6 = {'target_device': ['640'], 'TTL_sequence': ['l1,h1,l1,h1'], 'TTL_sequence_axis': ['ND-GalvoX'], 'sequence_time': 2e-05}
ttlparameterDict6 = {'target_device': ['640'], 'TTL_sequence': ['l1'], 'TTL_sequence_axis': ['ND-GalvoX'], 'sequence_time': 2e-05}

parameterDict62 = {'target_device': ['Mock-Repeat', 'ND-GalvoY', 'Mock-Timelapse', 'ND-GalvoX', 'ND-PiezoZ'],
                 'axis_length': [3.0, 0.5, 3.0, 1.0, 1.0],
                 'axis_step_size': [1.0, 0.1, 1.0, 1.0, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['Mock-Repeat', 'ND-GalvoY', 'Mock-Timelapse', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}

parameterDict63 = {'target_device': ['Mock-Repeat', 'ND-GalvoY', 'Mock-Timelapse', 'ND-GalvoX', 'ND-PiezoZ'],
                 'axis_length': [3.0, 0.5, 3.0, 0.5, 1.0],
                 'axis_step_size': [1.0, 0.1, 1.0, 0.1, 1.0],
                 'axis_centerpos': [0.0, 0.0, 0.0, 0.0, 0.0],
                 'axis_startpos': [[0], [0], [0], [0], [0]],
                 'scan_dim_target_device': ['Mock-Repeat', 'ND-GalvoY', 'Mock-Timelapse', 'ND-GalvoX', 'None', 'None'],
                 'sequence_time': 2e-05,
                 'phase_delay': 100.0,
                 'd3step_delay': 0.0}


setupInfo = ViewSetupInfo(positioners={'ND-GalvoX': PositionerInfo(analogChannel='Dev1/ao0', digitalLine=None, managerName='NidaqPositionerManager', managerProperties={'conversionFactor': 17.44, 'minVolt': -10, 'maxVolt': 10, 'vel_max': 0.1, 'acc_max': 0.0001}, axes=['X'], isPositiveDirection=True, forPositioning=False, forScanning=True, resetOnClose=True),
                                       'ND-GalvoY': PositionerInfo(analogChannel='Dev1/ao1', digitalLine=None, managerName='NidaqPositionerManager', managerProperties={'conversionFactor': 16.63, 'minVolt': -10, 'maxVolt': 10, 'vel_max': 0.1, 'acc_max': 0.0001}, axes=['Y'], isPositiveDirection=True, forPositioning=False, forScanning=True, resetOnClose=True),
                                       'ND-PiezoZ': PositionerInfo(analogChannel='Dev1/ao2', digitalLine=None, managerName='NidaqPositionerManager', managerProperties={'conversionFactor': 1.0, 'minVolt': 0, 'maxVolt': 10, 'vel_max': 0.1, 'acc_max': 0.0001}, axes=['Z'], isPositiveDirection=True, forPositioning=False, forScanning=True, resetOnClose=True),
                                       'Mock-Timelapse': PositionerInfo(analogChannel=None, digitalLine=None, managerName='MockPositionerManager', managerProperties={'conversionFactor': 1, 'minVolt': 0, 'maxVolt': 200, 'vel_max': 1000, 'acc_max': 1000}, axes=['M-TM'], isPositiveDirection=True, forPositioning=False, forScanning=True, resetOnClose=True),
                                       'Mock-Repeat': PositionerInfo(analogChannel=None, digitalLine=None, managerName='MockPositionerManager', managerProperties={'conversionFactor': 1, 'minVolt': 0, 'maxVolt': 200, 'vel_max': 1000, 'acc_max': 1000}, axes=['M-RE'], isPositiveDirection=True, forPositioning=False, forScanning=True, resetOnClose=True)},
                                       scan=ScanInfo(scanWidgetType='PointScan', scanDesigner='GalvoScanDesigner', scanDesignerParams={}, TTLCycleDesigner='PointScanTTLCycleDesigner', TTLCycleDesignerParams={}, sampleRate=100000, maxScanTimeMin=10, lineClockLine=None, frameStartClockLine=None, frameEndClockLine=None))

scanDesigner = GalvoScanDesigner()
ttlDesigner = PointScanTTLCycleDesigner()

# TODO: NOW WORKS FOR ALL SEQ_AXIS, AND ALL NUMBER OF DIMENSIONS, FOR ARBITRARY SCAN DIMENSION ORDER (SMOOTH, STEP, MOCK). LINE AND FRAME CLOCKS ALSO WORK.
# NEXT: FIX APD READING ALONG THE SAME LINES - TRY ON MICROSCOPE
for signalset in range(1,7):
    if signalset == 1:
        parameterDicts = [parameterDict11, parameterDict12, parameterDict13]
        ttlparameterDict = ttlparameterDict1
    elif signalset == 2:
        parameterDicts = [parameterDict21, parameterDict22, parameterDict23]
        ttlparameterDict = ttlparameterDict2
    elif signalset == 3:
        parameterDicts = [parameterDict31, parameterDict32, parameterDict33]
        ttlparameterDict = ttlparameterDict3
    elif signalset == 4:
        parameterDicts = [parameterDict41, parameterDict42, parameterDict43]
        ttlparameterDict = ttlparameterDict4
    elif signalset == 5:
        parameterDicts = [parameterDict51, parameterDict52, parameterDict53]
        ttlparameterDict = ttlparameterDict5
    elif signalset == 6:
        parameterDicts = [parameterDict61, parameterDict62, parameterDict63]
        ttlparameterDict = ttlparameterDict6

    rep = 0
    while rep < 3:
        plt.ion()
        plt.figure(1)
        _, _, scanInfoDict = scanDesigner.make_signal(parameterDicts[rep], setupInfo)
        ttlDesigner.make_signal(ttlparameterDict, setupInfo, scanInfoDict)
        plt.show(block=True)
        rep +=1

if False:
    _, _, scanInfoDict = scanDesigner.make_signal(parameterDict2, setupInfo)
    ttlDesigner.make_signal(ttlparameterDict2, setupInfo, scanInfoDict)

    _, _, scanInfoDict = scanDesigner.make_signal(parameterDict3, setupInfo)
    ttlDesigner.make_signal(ttlparameterDict3, setupInfo, scanInfoDict)

    _, _, scanInfoDict = scanDesigner.make_signal(parameterDict4, setupInfo)
    ttlDesigner.make_signal(ttlparameterDict4, setupInfo, scanInfoDict)