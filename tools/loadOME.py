import tifffile
import os
import xml.etree.ElementTree as ET

file_name = "test_2023-09-19T20_19_04.ome.tif"
file_path = os.path.join('C:\\Users\\UC2\\Documents\\ImSwitchConfig\\histoController\\', file_name)
with tifffile.TiffFile(file_path) as tif:
    ome_metadata = tif.ome_metadata
    images = tif.series
    root = ET.fromstring(ome_metadata)

    datas = {}
    # Navigate and extract information
    for image in root.findall('{http://www.openmicroscopy.org/Schemas/OME/2016-06}Image'):
        image_name = image.get('Name')
        pixels = image.find('{http://www.openmicroscopy.org/Schemas/OME/2016-06}Pixels')
        
        physical_size_x = pixels.get('PhysicalSizeX')
        physical_size_y = pixels.get('PhysicalSizeY')
        
        plane = pixels.find('{http://www.openmicroscopy.org/Schemas/OME/2016-06}Plane')
        position_x = plane.get('PositionX')
        position_y = plane.get('PositionY')
        
        datas[image_name]= {
            "pixX":physical_size_x,
            "pixY":physical_size_y,
            "posX":position_x, 
            "posY":position_y}
        if 0:
            print(f"Image Name: {image_name}")
            print(f"Physical Size X: {physical_size_x} µm")
            print(f"Physical Size Y: {physical_size_y} µm")
            print(f"Position X: {position_x}")
            print(f"Position Y: {position_y}")
            print("-" * 50)

   
    for idx, image in enumerate(images):
        # Retrieve image data
        img_data = image.asarray()
        datas[image.name]["data"] = img_data