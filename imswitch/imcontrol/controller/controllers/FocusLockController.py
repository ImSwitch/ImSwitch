import time

import numpy as np
from time import perf_counter
import scipy.ndimage as ndi
from skimage.feature import peak_local_max

import numpy as np
import matplotlib.pyplot as plt
import tifffile as tif
import serial
import time
import serial.tools.list_ports
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import base64
import io
import serial.tools.list_ports
import threading

from imswitch.imcommon.framework import Thread, Timer
from imswitch.imcommon.model import initLogger
from ..basecontrollers import ImConWidgetController


class FocusLockController(ImConWidgetController):
    """Linked to FocusLockWidget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        if self._setupInfo.focusLock is None:
            return

        self.camera = self._setupInfo.focusLock.camera
        if self.camera == "ESP32":
            self.isESP32 = True
        else:
            self.isESP32 = False
        self.positioner = self._setupInfo.focusLock.positioner
        self.updateFreq = self._setupInfo.focusLock.updateFreq
        self.cropFrame = (self._setupInfo.focusLock.frameCropx,
                          self._setupInfo.focusLock.frameCropy,
                          self._setupInfo.focusLock.frameCropw,
                          self._setupInfo.focusLock.frameCroph)
        
        if self.isESP32:
            # Create an instance of the ESP32CameraThread class
            self.ESP32Camera = ESP32CameraThread('Espressif')

            # Start the thread
            self.ESP32Camera.startStreaming()
        else:
            self._master.detectorsManager[self.camera].crop(*self.cropFrame)
        self._widget.setKp(self._setupInfo.focusLock.piKp)
        self._widget.setKi(self._setupInfo.focusLock.piKi)

        # Connect FocusLockWidget buttons
        self._widget.kpEdit.textChanged.connect(self.unlockFocus)
        self._widget.kiEdit.textChanged.connect(self.unlockFocus)

        self._widget.lockButton.clicked.connect(self.toggleFocus)
        self._widget.camDialogButton.clicked.connect(self.cameraDialog)
        self._widget.focusCalibButton.clicked.connect(self.focusCalibrationStart)
        self._widget.calibCurveButton.clicked.connect(self.showCalibrationCurve)

        self._widget.zStackBox.stateChanged.connect(self.zStackVarChange)
        self._widget.twoFociBox.stateChanged.connect(self.twoFociVarChange)
        
        self._widget.sigSliderExpTValueChanged.connect(self.setExposureTime)
        self._widget.sigSliderGainValueChanged.connect(self.setGain)


        self.setPointSignal = 0
        self.locked = False
        self.aboutToLock = False
        self.zStackVar = False
        self.twoFociVar = False
        self.noStepVar = True
        self.focusTime = 1000 / self.updateFreq  # focus signal update interval (ms)
        self.zStepLimLo = 0
        self.aboutToLockDiffMax = 0.4
        self.lockPosition = 0
        self.currentPosition = 0
        self.lastPosition = 0
        self.buffer = 40
        self.currPoint = 0
        self.setPointData = np.zeros(self.buffer)
        self.timeData = np.zeros(self.buffer)

        if not self.isESP32: self._master.detectorsManager[self.camera].startAcquisition()
        self.__processDataThread = ProcessDataThread(self)
        self.__focusCalibThread = FocusCalibThread(self)

        self.timer = Timer()
        self.timer.timeout.connect(self.update)
        self.timer.start(int(self.focusTime))
        self.startTime = perf_counter()

    def __del__(self):
        self.__processDataThread.quit()
        self.__processDataThread.wait()
        self.__focusCalibThread.quit()
        self.__focusCalibThread.wait()
        self.ESP32Camera.stopStreaming()
        if hasattr(super(), '__del__'):
            super().__del__()

    def unlockFocus(self):
        if self.locked:
            self.locked = False
            self._widget.lockButton.setChecked(False)
            self._widget.focusPlot.removeItem(self._widget.focusLockGraph.lineLock)

    def toggleFocus(self):
        self.aboutToLock = False
        if self._widget.lockButton.isChecked():
            zpos = self._master.positionersManager[self.positioner].get_abs()
            self.lockFocus(zpos)
            self._widget.lockButton.setText('Unlock')
        else:
            self.unlockFocus()
            self._widget.lockButton.setText('Lock')

    def cameraDialog(self):
        if not self.isESP32: self._master.detectorsManager[self.camera].openPropertiesDialog()

    def setGain(self, gain):
        self.ESP32Camera.setGain(gain)

    def setExposureTime(self, exposureTime):
        self.ESP32Camera.setExposureTime(exposureTime)
        
    def focusCalibrationStart(self):
        self.__focusCalibThread.start()

    def showCalibrationCurve(self):
        self._widget.showCalibrationCurve(self.__focusCalibThread.getData())

    def zStackVarChange(self):
        if self.zStackVar:
            self.zStackVar = False
        else:
            self.zStackVar = True

    def twoFociVarChange(self):
        if self.twoFociVar:
            self.twoFociVar = False
        else:
            self.twoFociVar = True

    def update(self):
        # get data
        img = self.__processDataThread.grabCameraFrame()
        self.setPointSignal = self.__processDataThread.update(self.twoFociVar)
        # move
        if self.locked:
            value_move = self.updatePI()
            if self.noStepVar and abs(value_move) > 0.002:
                self._master.positionersManager[self.positioner].move(value_move, 0)
        elif self.aboutToLock:
           self.aboutToLockUpdate()
        # udpate graphics
        self.updateSetPointData()
        self._widget.camImg.setImage(img)
        if self.currPoint < self.buffer:
            self._widget.focusPlotCurve.setData(self.timeData[1:self.currPoint],
                                                self.setPointData[1:self.currPoint])
        else:
            self._widget.focusPlotCurve.setData(self.timeData, self.setPointData)
    
    def aboutToLockUpdate(self):
        self.aboutToLockDataPoints = np.roll(self.aboutToLockDataPoints,1)
        self.aboutToLockDataPoints[0] = self.setPointSignal
        averageDiff = np.std(self.aboutToLockDataPoints)
        if averageDiff < self.aboutToLockDiffMax:
            zpos = self._master.positionersManager[self.positioner].get_abs()
            self.lockFocus(zpos)
            self.aboutToLock = False

    def updateSetPointData(self):
        if self.currPoint < self.buffer:
            self.setPointData[self.currPoint] = self.setPointSignal
            self.timeData[self.currPoint] = perf_counter() - self.startTime
        else:
            self.setPointData = np.roll(self.setPointData, -1)
            self.setPointData[-1] = self.setPointSignal
            self.timeData = np.roll(self.timeData, -1)
            self.timeData[-1] = perf_counter() - self.startTime
        self.currPoint += 1

    def updatePI(self):
        if not self.noStepVar:
            self.noStepVar = True
        self.currentPosition = self._master.positionersManager[self.positioner].get_abs()
        self.stepDistance = np.abs(self.currentPosition - self.lastPosition)
        distance = self.currentPosition - self.lockPosition
        move = self.pi.update(self.setPointSignal)
        self.lastPosition = self.currentPosition

        if abs(distance) > 5 or abs(move) > 3:
            self._logger.warning(f'Safety unlocking! Distance to lock: {distance:.3f}, current move step: {move:.3f}.')
            self.unlockFocus()
        elif self.zStackVar:
            if self.stepDistance > self.zStepLimLo:
                self.unlockFocus()
                self.aboutToLockDataPoints = np.zeros(5)
                self.aboutToLock = True
                self.noStepVar = False
        return move

    def lockFocus(self, zpos):
        if not self.locked:
            kp = float(self._widget.kpEdit.text())
            ki = float(self._widget.kiEdit.text())
            self.pi = PI(self.setPointSignal, 0.001, kp, ki)
            self.lockPosition = zpos
            self.locked = True
            self._widget.focusLockGraph.lineLock = self._widget.focusPlot.addLine(
                y=self.setPointSignal, pen='r'
            )
            self._widget.lockButton.setChecked(True)
            self.updateZStepLimits()

    def updateZStepLimits(self):
        self.zStepLimLo = 0.001 * float(self._widget.zStepFromEdit.text())


class ProcessDataThread(Thread):
    def __init__(self, controller, *args, **kwargs):
        self._controller = controller
        super().__init__(*args, **kwargs)
        

    def grabCameraFrame(self):
        if not self._controller.isESP32:
            detectorManager = self._controller._master.detectorsManager[self._controller.camera]
            self.latestimg = detectorManager.getLatestFrame()
        else: 
            try:
                self.latestimg = self._controller.ESP32Camera.grabLatestFrame()
            except:
                self.latestimg = np.zeros((self._controller.ESP32Camera.Ny,self._controller.ESP32Camera.Nx))
            
            
            
        # 1.5 swap axes of frame (depending on setup, make this a variable in the json)
        if self._controller._setupInfo.focusLock.swapImageAxes:
            self.latestimg = np.swapaxes(self.latestimg,0,1)
        return self.latestimg

    def update(self, twoFociVar):

        if self._controller.isESP32:
            imagearraygf = ndi.filters.gaussian_filter(self.latestimg, 5)
            # mBackground = np.mean(mStack, (0)) #np.ones(mStack.shape[1:])# 
            mBackground = ndi.filters.gaussian_filter(self.latestimg,15)
            mFrame = imagearraygf/mBackground # mStack/mBackground
            massCenterGlobal=np.max(np.mean(mFrame**2, 1))/np.max(np.mean(mFrame**2, 0))
            
        else:
            # Gaussian filter the image, to remove noise and so on, to get a better center estimate
            imagearraygf = ndi.filters.gaussian_filter(self.latestimg, 7)

            # Update the focus signal
            if twoFociVar:
                allmaxcoords = peak_local_max(imagearraygf, min_distance=60)
                size = allmaxcoords.shape
                maxvals = np.zeros(size[0])
                maxvalpos = np.zeros(2)
                for n in range(0, size[0]):
                    if imagearraygf[allmaxcoords[n][0], allmaxcoords[n][1]] > maxvals[0]:
                        if imagearraygf[allmaxcoords[n][0], allmaxcoords[n][1]] > maxvals[1]:
                            tempval = maxvals[1]
                            maxvals[0] = tempval
                            maxvals[1] = imagearraygf[allmaxcoords[n][0], allmaxcoords[n][1]]
                            tempval = maxvalpos[1]
                            maxvalpos[0] = tempval
                            maxvalpos[1] = n
                        else:
                            maxvals[0] = imagearraygf[allmaxcoords[n][0], allmaxcoords[n][1]]
                            maxvalpos[0] = n
                xcenter = allmaxcoords[maxvalpos[0]][0]
                ycenter = allmaxcoords[maxvalpos[0]][1]
                if allmaxcoords[maxvalpos[1]][1] < ycenter:
                    xcenter = allmaxcoords[maxvalpos[1]][0]
                    ycenter = allmaxcoords[maxvalpos[1]][1]
                centercoords2 = np.array([xcenter, ycenter])
            else:
                centercoords = np.where(imagearraygf == np.array(imagearraygf.max()))
                centercoords2 = np.array([centercoords[0][0], centercoords[1][0]])

            subsizey = 50
            subsizex = 50
            xlow = max(0, (centercoords2[0] - subsizex))
            xhigh = min(1024, (centercoords2[0] + subsizex))
            ylow = max(0, (centercoords2[1] - subsizey))
            yhigh = min(1280, (centercoords2[1] + subsizey))

            imagearraygfsub = imagearraygf[xlow:xhigh, ylow:yhigh]
            massCenter = np.array(ndi.measurements.center_of_mass(imagearraygfsub))
            # add the information about where the center of the subarray is
            massCenterGlobal = massCenter[1] + centercoords2[1]  # - subsizey - self.sensorSize[1] / 2
        return massCenterGlobal


class FocusCalibThread(Thread):
    def __init__(self, controller, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._controller = controller

    def run(self):
        self.signalData = []
        self.positionData = []
        self.fromVal = float(self._controller._widget.calibFromEdit.text())
        self.toVal = float(self._controller._widget.calibToEdit.text())
        self.scan_list = np.round(np.linspace(self.fromVal, self.toVal, 20), 2)
        for z in self.scan_list:
            self._controller._master.positionersManager[self._controller.positioner].setPosition(z, 0)
            time.sleep(0.5)
            self.focusCalibSignal = self._controller.setPointSignal
            self.signalData.append(self.focusCalibSignal)
            self.positionData.append(self._controller._master.positionersManager[self._controller.positioner].get_abs())
        self.poly = np.polyfit(self.positionData, self.signalData, 1)
        self.calibrationResult = np.around(self.poly, 4)
        self.show()

    def show(self):
        cal_nm = np.round(1000 / self.poly[0], 1)
        calText = f'1 px --> {cal_nm} nm'
        self._controller._widget.calibrationDisplay.setText(calText)

    def getData(self):
        data = {
            'signalData': self.signalData,
            'positionData': self.positionData,
            'poly': self.poly
        }
        return data


class PI:
    """Simple implementation of a discrete PI controller.
    Taken from http://code.activestate.com/recipes/577231-discrete-pid-controller/
    Author: Federico Barabas"""
    def __init__(self, setPoint, multiplier=1, kp=0, ki=0):
        self._kp = multiplier * kp
        self._ki = multiplier * ki
        self._setPoint = setPoint
        self.multiplier = multiplier
        self.error = 0.0
        self._started = False

    def update(self, currentValue):
        """ Calculate PI output value for given reference input and feedback.
        Using the iterative formula to avoid integrative part building. """
        self.error = self.setPoint - currentValue
        if self.started:
            self.dError = self.error - self.lastError
            self.out = self.out + self.kp * self.dError + self.ki * self.error
        else:
            # This only runs in the first step
            self.out = self.kp * self.error
            self.started = True
        self.lastError = self.error
        return self.out

    def restart(self):
        self.started = False

    @property
    def started(self):
        return self._started

    @started.setter
    def started(self, value):
        self._started = value

    @property
    def setPoint(self):
        return self._setPoint

    @setPoint.setter
    def setPoint(self, value):
        self._setPoint = value

    @property
    def kp(self):
        return self._kp

    @kp.setter
    def kp(self, value):
        self._kp = value

    @property
    def ki(self):
        return self._ki

    @ki.setter
    def ki(self, value):
        self._ki = value
        





class ESP32CameraThread(object):
    # attention a threading class won't work in windows!!! #FIXME:
    def __init__(self, manufacturer):
        self.manufacturer = manufacturer
        self.serialdevice = None
        self.Nx, self.Ny = 320,240
        self.frame = np.zeros((self.Ny,self.Nx))

        # string to send data to camera
        self.newCommand = ""
        self.exposureTime = -1
        self.gain = -1

    def setExposureTime(self, exposureTime):
        self.newCommand = "t"+str(exposureTime)
        self.exposureTime = exposureTime

    def setGain(self, gain):
        self.newCommand = "g"+str(gain)
        self.gain = gain

    def connect_to_usb_device(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.manufacturer == self.manufacturer or port.manufacturer=="Microsoft":
                try:
                    ser = serial.Serial(port.device, baudrate=2000000, timeout=1)
                    ser.write_timeout=.5
                    print(f"Connected to device: {port.description}")
                    return ser
                except serial.SerialException:
                    print(f"Failed to connect to device: {port.description}")
        print("No matching USB device found.")
        return None

    def startStreaming(self):
        self.isRunning = True
        self.mThread = threading.Thread(target=self.startStreamingThread) 
        self.mThread.start()
 
    def stopStreaming(self):
        self.isRunning = False
        self.mThread.join()
        try:self.serialdevice.close()
        except:pass

    def startStreamingThread(self):
        self.serialdevice = self.connect_to_usb_device()
        nFrame = 0
        nTrial = 0
        while self.isRunning:
            try:

                # send new comamand to change camera settings, reset command    
                if not self.newCommand == "":
                    self.serialdevice.write((self.newCommand+' \n').encode())
                    self.newCommand = ""

                # request new image
                self.serialdevice.write((' \n').encode())
                    
                # don't read to early
                time.sleep(.05)
                # readline of camera
                imageB64 = self.serialdevice.readline()

                # decode byte stream
                image = np.array(Image.open(io.BytesIO(base64.b64decode(imageB64.decode()))))
                self.frame = np.mean(image,-1)

                nFrame += 1
                
            except Exception as e:
                # try to reconnect 
                #print(e) # most of the time "incorrect padding of the bytes "
                nFrame = 0
                nTrial+=1
                try:
                    self.serialdevice.flushInput()
                    self.serialdevice.flushOutput()
                except:
                    pass
                if nTrial > 10 and type(e)==serial.serialutil.SerialException:
                    try:
                        # close the device - similar to hard reset
                        self.serialdevice.setDTR(False)
                        self.serialdevice.setRTS(True)
                        time.sleep(.1)
                        self.serialdevice.setDTR(False)
                        self.serialdevice.setRTS(False)
                        time.sleep(.5)
                        #self.serialdevice.close()
                    except: pass
                    self.serialdevice = self.connect_to_usb_device()
                    nTrial = 0
                
                
    def grabLatestFrame(self):
        return self.frame


# Do other work in the main thread if needed
# ...

# Wait for the thread to complete (optional)
# ESP32Camera.join()



# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


'''
Code for the ESP32 XIAO

#include "esp_camera.h"
#include <base64.h>

#define BAUD_RATE 2000000

#define PWDN_GPIO_NUM -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 10
#define SIOD_GPIO_NUM 40
#define SIOC_GPIO_NUM 39

#define Y9_GPIO_NUM 48
#define Y8_GPIO_NUM 11
#define Y7_GPIO_NUM 12
#define Y6_GPIO_NUM 14
#define Y5_GPIO_NUM 16
#define Y4_GPIO_NUM 18
#define Y3_GPIO_NUM 17
#define Y2_GPIO_NUM 15
#define VSYNC_GPIO_NUM 38
#define HREF_GPIO_NUM 47
#define PCLK_GPIO_NUM 13

#define LED_GPIO_NUM 21

void grabImage();
void cameraInit();


void setup()
{
  Serial.begin(BAUD_RATE);

  cameraInit();
}

bool isCROP = false;
int Nx = 320;
int Ny = 240;
int Nroi = 50;
int x = 320 / 2;
int y = 240 / 2;
bool isStreaming = true;

void crop_image(camera_fb_t *fb, unsigned short cropLeft, unsigned short cropRight, unsigned short cropTop, unsigned short cropBottom)
{
  unsigned int maxTopIndex = cropTop * fb->width * 2;
  unsigned int minBottomIndex = ((fb->width * fb->height) - (cropBottom * fb->width)) * 2;
  unsigned short maxX = fb->width - cropRight; // In pixels
  unsigned short newWidth = fb->width - cropLeft - cropRight;
  unsigned short newHeight = fb->height - cropTop - cropBottom;
  size_t newJpgSize = newWidth * newHeight * 2;

  unsigned int writeIndex = 0;
  // Loop over all bytes
  for (int i = 0; i < fb->len; i += 2)
  {
    // Calculate current X, Y pixel position
    int x = (i / 2) % fb->width;

    // Crop from the top
    if (i < maxTopIndex)
    {
      continue;
    }

    // Crop from the bottom
    if (i > minBottomIndex)
    {
      continue;
    }

    // Crop from the left
    if (x <= cropLeft)
    {
      continue;
    }

    // Crop from the right
    if (x > maxX)
    {
      continue;
    }

    // If we get here, keep the pixels
    fb->buf[writeIndex++] = fb->buf[i];
    fb->buf[writeIndex++] = fb->buf[i + 1];
  }

  // Set the new dimensions of the framebuffer for further use.
  fb->width = newWidth;
  fb->height = newHeight;
  fb->len = newJpgSize;
}

void loop()
{
  // Check for incoming serial commands
  if (Serial.available() > 0)
  {
    String command = Serial.readStringUntil('\n'); // Read the incoming command until a newline character is encountered

    // Parse the received command into x and y coordinates
    int delimiterIndex = command.indexOf(','); // Find the index of the comma delimiter
    if (delimiterIndex != -1)
    {
      String xString = command.substring(0, delimiterIndex);  // Extract the x coordinate substring
      String yString = command.substring(delimiterIndex + 1); // Extract the y coordinate substring

      x = xString.toInt(); // Convert the x coordinate string to an integer
      y = yString.toInt(); // Convert the y coordinate string to an integer

      // Do something with the x and y coordinates
      // For example, you can print them:
      Serial.print("Received coordinates: ");
      Serial.print("x = ");
      Serial.print(x);
      Serial.print(", y = ");
      Serial.println(y);
    }
  }
  if (isStreaming)
    grabImage();
}

void cameraInit()
{

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  // config.frame_size = FRAMESIZE_QVGA;
  // config.pixel_format = PIXFORMAT_JPEG; // for streaming
  // config.pixel_format = PIXFORMAT_RGB565; // for face detection/recognition
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  if (isCROP)
  {
    config.pixel_format = PIXFORMAT_RGB565;
    config.frame_size = FRAMESIZE_SXGA;
    config.fb_count = 2;
  }
  else
  {
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size = FRAMESIZE_VGA; // for streaming}

    config.fb_count = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK)
  {
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  s->set_hmirror(s, 1);
  s->set_vflip(s, 1);
}
void grabImage()
{

  camera_fb_t *fb = esp_camera_fb_get();
  if (isCROP)
  {

    // Crop image (frame buffer, cropLeft, cropRight, cropTop, cropBottom)
    unsigned short cropLeft = x - Nroi / 2;
    unsigned short cropRight = x + Nroi / 2;
    unsigned short cropTop = y - Nroi / 2;
    unsigned short cropBottom = y + Nroi / 2;

    crop_image(fb, 550, 450, 100, 190);
    // crop_image(fb, cropLeft, cropRight, cropTop, cropBottom);
    //  Create a buffer for the JPG in psram
    uint8_t *jpg_buf = (uint8_t *)heap_caps_malloc(200000, MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);

    if (jpg_buf == NULL)
    {
      printf("Malloc failed to allocate buffer for JPG.\n");
    }
    else
    {
      size_t jpg_size = 0;

      // Convert the RAW image into JPG
      // The parameter "31" is the JPG quality. Higher is better.
      fmt2jpg(fb->buf, fb->len, fb->width, fb->height, fb->format, 31, &jpg_buf, &jpg_size);
      printf("Converted JPG size: %d bytes \n", jpg_size);
      String encoded = base64::encode(jpg_buf, jpg_size);
      Serial.write(encoded.c_str(), encoded.length());
      Serial.println();
    }
  }
  else
  {

    if (!fb || fb->format != PIXFORMAT_JPEG)
    {
      Serial.println("Failed to capture image");
    }
    else
    {
      delay(40);

      String encoded = base64::encode(fb->buf, fb->len);
      Serial.write(encoded.c_str(), encoded.length());
      Serial.println();
    }

    esp_camera_fb_return(fb);
  }
}

'''