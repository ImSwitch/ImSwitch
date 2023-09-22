#conda install openjdk=11.0.15=h57928b3_0 -c conda-forge -y
from ashlar.scripts import ashlar
import os

file_name = "test_2023-09-19T20_19_04.ome.tif"
collected_tiles_file = os.path.join('C:\\Users\\UC2\\Documents\\ImSwitchConfig\\histoController\\', file_name)
ashlar_output_file = os.path.join('C:\\Users\\UC2\\Documents\\ImSwitchConfig\\histoController\\', file_name+"_processed.tif")

maximum_shift_microns = 50

ashlar.main(['', collected_tiles_file, '-o', ashlar_output_file, '--pyramid', '-m%s' % maximum_shift_microns])