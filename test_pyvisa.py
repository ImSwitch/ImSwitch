import pyvisa

rm = pyvisa.ResourceManager('@py')

print(rm.list_resources())
inst = rm.open_resource('ASRL4::INSTR')
print(inst.query('str'))
