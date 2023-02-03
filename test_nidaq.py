
import nidaqmx
import nidaqmx._lib
import nidaqmx.constants

import numpy as np

name = 'testTask'
line = 'Dev1/port0/line1'
acquisitionType = nidaqmx.constants.AcquisitionType.FINITE
#source = r'20MHzTimebase'
#source = None
source = 'OnboardClock'
rate = 100000
#rate = 20000000
sampsInScan = 100000
tasklen = sampsInScan
starttrig = False

#print(nidaqmx.Task("ScanDOTask").in_stream)
#print(f'Create DO task: {name}')
#print(line)

#dotask = nidaqmx.Task(name)
#dotask.do_channels.add_do_chan(line)
#dotask.timing.cfg_samp_clk_timing(source=source, rate=rate, sample_mode=acquisitionType, samps_per_chan=sampsInScan)

#print(f'Created DO task: {name}')

signal = True * np.ones(tasklen, dtype=bool)

# write signal to task
#dotask.write(signal, auto_start=True, timeout=20)
#print('Task started')
#dotask.wait_until_done()
#dotask.stop()
#dotask.close()
#print('Task finished')


nidev = nidaqmx.system.device.Device('Dev1')
#print(nidev.accessory_product_nums)
nsys = nidaqmx.system.System.local()
print(nsys.tasks.task_names)
print(list(nsys.devices))