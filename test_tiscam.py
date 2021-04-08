from pyicic import IC_ImagingControl
import numpy as np
import matplotlib.pyplot as plt


def grabFrame(cam):
    cam.reset_frame_ready()  # reset frame ready flag
    cam.send_trigger()
    # self.cam.wait_til_frame_ready(0)  # wait for frame ready due to trigger
    frame = cam.get_image_data()
    # Prev: averaging the RGB image to a grayscale. Very slow for the big camera (2480x2048).
    #frame = np.average(frame, 2)
    # New: just take the R-component, this should anyway contain most information in both cameras. Change this if we want to look at another color, like GFP!
    frame = np.array(frame[0], dtype='float64')
    # Check if below is giving the right dimensions out
    frame = np.reshape(frame,(2048,2448,3))[:,:,0]
    return frame


ic_ic = IC_ImagingControl.IC_ImagingControl()
ic_ic.init_library()
cam_names = ic_ic.get_unique_device_names()
print(cam_names)
model = cam_names[1]
cam = ic_ic.get_device(model)

cam.open()
print(cam.get_image_description())

cam.colorenable = 0
cam.gain.auto = False
cam.exposure.auto = False
cam.enable_continuous_mode(True)
cam.start_live(show_display=False)

print(cam.list_property_names())
#cam.gain = 100
print(cam.gain.value)
cam.show_property_dialog()
print(cam.gain.value)

#shape = (cam.get_image_description()[0], cam.get_image_description()[1])

img = grabFrame(cam)
print(np.shape(img))
print(np.max(img))
#plt.plot(img)
#plt.show()

