import nidaqmx
import numpy as np
import time

def __createLineDOTask(name, lines, acquisitionType, source, rate, sampsInScan=1000, reference_trigger='ai/StartTrigger'):
    """ Simplified function to create a digital output task """
    dotask = nidaqmx.Task(name)

    lines = np.atleast_1d(lines)

    for line in lines:
        dotask.do_channels.add_do_chan('Dev1/port0/line%s' % line)
    dotask.timing.cfg_samp_clk_timing(source=source, rate=rate,
                                        sample_mode=acquisitionType,
                                        samps_per_chan=sampsInScan)
    dotask.triggers.start_trigger.cfg_dig_edge_start_trig(reference_trigger)
    return dotask

#allchannels = nidaqmx.system._collections.physical_channel_collection.PhysicalChannelCollection('Dev1')
#print(allchannels.channel_names())
line = 1
acquisitionTypeFinite = nidaqmx.constants.AcquisitionType.FINITE
dotask = __createLineDOTask('test', line, acquisitionTypeFinite, '100kHzTimebase', 100000)

signal = True * np.ones(100, dtype=bool)

dotask.write(signal, auto_start=True)
time.sleep(3)
dotask.close()
#dotask.start()
