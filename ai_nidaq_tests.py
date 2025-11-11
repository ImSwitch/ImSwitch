import pprint
import time
import nidaqmx
from nidaqmx.constants import VoltageUnits

def main():
    pp = pprint.PrettyPrinter(indent=4)

    with nidaqmx.Task("test") as task:
        """ch = task.ai_channels.add_ai_voltage_chan("Dev1/ai1")
        ch.__setattr__("ai_voltage_units", VoltageUnits.FROM_TEDS) # volts
        in_stream = task.in_stream"""
        task.ai_channels.add_ai_voltage_chan("Dev1/ai1")


        while True:
            print("1 Channel N Samples Read Raw: ")
            data = task.read(10)
            # data = in_stream.read(number_of_samples_per_channel=8)
            pp.pprint(data)
            time.sleep(0.2)



if __name__ == "__main__":
    main()