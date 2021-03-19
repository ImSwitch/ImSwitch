import pyvisa

rm = pyvisa.ResourceManager()

print(rm.list_resources())
inst = rm.open_resource('COM6')
print(inst.query('?readsn'))