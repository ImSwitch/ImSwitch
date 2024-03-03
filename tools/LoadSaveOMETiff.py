import numpy as np
import tifffile
import xml.etree.ElementTree as ET


# Generate OME-XML metadata
def create_ome_xml(num_channels, num_z_slices, num_timepoints, pixel_size=(1.0, 1.0, 1.0), dtype='uint16'):
    """
    Create OME-XML metadata for an OME-TIFF file.
    pixel_size is given as (px_size_z, px_size_y, px_size_x).
    """
    # Create an XML element for OME
    ns = "http://www.openmicroscopy.org/Schemas/OME/2016-06"
    attrib = {"xmlns": ns, "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
              "xsi:schemaLocation": f"{ns} http://www.openmicroscopy.org/Schemas/OME/2016-06"}
    ome = ET.Element("OME", attrib)

    # Add Image element for each location
    for location_id in range(num_locations):
        image = ET.SubElement(ome, "Image", ID=f"Image:{location_id}", Name=f"Location_{location_id}")
        pixels = ET.SubElement(image, "Pixels", ID=f"Pixels:{location_id}",
                               DimensionOrder="XYZCT",
                               Type=dtype,
                               SizeX=str(image_width),
                               SizeY=str(image_height),
                               SizeZ=str(num_z_slices),
                               SizeC=str(num_channels),
                               SizeT=str(num_timepoints),
                               PhysicalSizeX=str(pixel_size[2]),
                               PhysicalSizeY=str(pixel_size[1]),
                               PhysicalSizeZ=str(pixel_size[0]))
        
        # Add Channel element for each channel
        for channel_id in range(num_channels):
            ET.SubElement(pixels, "Channel", ID=f"Channel:{location_id}:{channel_id}", SamplesPerPixel="1")

        # Add TiffData element for each timepoint
        for t in range(num_timepoints):
            ET.SubElement(pixels, "TiffData", FirstT=str(t), FirstC="0", FirstZ="0", PlaneCount=str(num_channels * num_z_slices))

    return ET.tostring(ome, encoding='utf-8', method='xml')



if 1:
    # Assuming your data is organized in a 5D array following the order (T, Location, Z, C, Y, X)
    # Example dimensions:
    num_timepoints = 1
    num_locations = 2
    num_channels = 3  # e.g., Laser1, Laser2, LED
    num_z_slices = 10
    image_width, image_height = 512, 512
    Nx, Ny = 3, 3

    # Create an example multi-dimensional array to represent your data
    data_shape = (num_timepoints, num_locations, num_z_slices, num_channels, image_height, image_width)
    image_data = np.random.rand(*data_shape).astype('float32')  # Replace with your actual image data

    # Flatten the data to write sequentially
    image_data_reshaped = image_data.reshape(num_timepoints * num_locations * num_z_slices * num_channels, image_height, image_width)

    # Create OME-XML metadata
    ome_xml = create_ome_xml(num_channels, num_z_slices, num_timepoints, dtype='float32')

    # Write the data to an OME-TIFF file with per-image metadata
    ome_tiff_path = 'your_data.ome.tiff'
    tiff_writer = tifffile.TiffWriter(ome_tiff_path, bigtiff=True)
    nSlices = num_timepoints * num_locations * num_z_slices * num_channels * Nx * Ny
    for t in range(num_timepoints):
        for loc in range(num_locations):
            for z in range(num_z_slices):
                for c in range(num_channels):
                    for x in range(Nx):
                        for y in range(Ny):
                            # Calculate the index in the flattened array
                            index = t * (num_locations * num_z_slices * num_channels) + loc * (num_z_slices * num_channels) + z * num_channels + c
                            # Define the metadata for this slice
                            metadata = {
                                'axes': 'YX',
                                'Position': (t, loc, z, c),
                                # Add more metadata as needed, for example:
                                'Channel': f'Channel {c}',
                                'TimePoint': t,
                                'ZSlice': z,
                                'Location': loc,
                                'XCoordinate': x,  # Assume x is defined
                                'YCoordinate': y,  # Assume y is defined
                                # Include any physical sizes or units here if necessary
                            }
                            # Write the slice with its metadata
                            print("Writing slice with metadata: ", nSlices, " ", index)
                            tiff_writer.write(image_data_reshaped[index], photometric='minisblack', metadata={'ImageDescription': str(metadata)})
            
            # Optionally, you can also add global OME-XML metadata here if needed
            tiff_writer._write_image_description(ome_xml)


# Path to your OME-TIFF file
ome_tiff_path = 'your_data.ome.tiff'

# Read the OME-TIFF file and extract OME-XML metadata
with tifffile.TiffFile(ome_tiff_path) as tiff_file:
    ome_xml = tiff_file.ome_metadata  # This is a string of XML data

# Parse the OME-XML metadata
ome_root = ET.fromstring(ome_xml)

# Define a namespace dictionary to handle the OME namespace
namespaces = {'ome': 'http://www.openmicroscopy.org/Schemas/OME/2016-06'}

# Example: Extract all image IDs and their names
for image in ome_root.findall('ome:Image', namespaces):
    image_id = image.get('ID')
    image_name = image.get('Name')
    print(f"Image ID: {image_id}, Name: {image_name}")

# Example: Extract details from the Pixels element of the first image
pixels = ome_root.find('.//ome:Image/ome:Pixels', namespaces)
if pixels is not None:
    size_x = pixels.get('SizeX')
    size_y = pixels.get('SizeY')
    size_z = pixels.get('SizeZ')
    pixel_type = pixels.get('Type')
    print(f"Pixels SizeX: {size_x}, SizeY: {size_y}, SizeZ: {size_z}, Pixel Type: {pixel_type}")

# You can extend this approach to extract other metadata, such as Channels, Planes, etc.



## works:
with tifffile.TiffFile(ome_tiff_path) as tiff_file:
    for page in tiff_file.pages:
        # Assuming metadata is stored in ImageDescription or similar
        metadata_str = page.tags['ImageDescription'].value
        series = tiff_file.series[0]  # Get the first series
        image_data = series.asarray()  # Load the image data as a numpy array

        # Parse the metadata string to extract coordinates (implement parsing based on your format)
        x_coordinate, y_coordinate = parse_metadata_for_coordinates(metadata_str)
        # Now, x_coordinate and y_coordinate contain the location info

