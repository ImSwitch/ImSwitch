import nidaqmx

print(nidaqmx.system._collections.device_collection.DeviceCollection.device_names)
test = nidaqmx.system._collections.physical_channel_collection.PhysicalChannelCollection(nidaqmx.system._collections.device_collection.DeviceCollection.device_names)

print(test.channel_names)