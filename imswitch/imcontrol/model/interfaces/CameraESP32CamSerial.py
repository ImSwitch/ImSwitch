import time
from imswitch.imcommon.model import initLogger
from threading import Thread
import numpy as np
import serial.tools.list_ports
import base64
from PIL import Image
import io

class CameraESP32CamSerial:
    def __init__(self):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # many to be purged
        self.model = "ESP32Camera"
        self.shape = (0, 0)

        self.isConnected = False

        # camera parameters
        self.framesize = 100
        self.exposure_time = 0
        self.analog_gain = 0

        self.SensorWidth = 320
        self.SensorHeight = 240
        
        self.manufacturer = 'Espressif'
        
        self.frame = np.ones((self.SensorHeight,self.SensorWidth))
        self.isRunning = False
        
        # string to send data to camera
        self.newCommand = ""
        self.exposureTime = -1
        self.gain = -1

        self.serialdevice = self.connect_to_usb_device()

    def connect_to_usb_device(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.manufacturer == self.manufacturer or port.manufacturer=="Microsoft":
                try:
                    ser = serial.Serial(port.device, baudrate=2000000, timeout=1)
                    print(f"Connected to device: {port.description}")
                    return ser
                except serial.SerialException:
                    print(f"Failed to connect to device: {port.description}")
        print("No matching USB device found.")
        return None

    def put_frame(self, frame):
        self.frame = frame
        return frame

    def start_live(self):
        self.isRunning = True
        self.mThread = Thread(target=self.startStreamingThread) 
        self.mThread.start()

    def stop_live(self):
        self.isRunning = False
        self.mThread.join()
        try:self.serialdevice.close()
        except:pass

    def suspend_live(self):
        self.isRunning = False

    def prepare_live(self):
        pass

    def close(self):
        try:self.serialdevice.close()
        except:pass

    def setPropertyValue(self, property_name, property_value):
        # Check if the property exists.
        if property_name == "gain":
            self.set_analog_gain(property_value)
        elif property_name == "exposure":
            self.set_exposure_time(property_value)
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value

    def getPropertyValue(self, property_name):
        # Check if the property exists.
        if property_name == "gain":
            property_value = self.gain
        elif property_name == "exposure":
            property_value = self.exposureTime
        else:
            self.__logger.warning(f'Property {property_name} does not exist')
            return False
        return property_value


    def set_exposure_time(self, exposureTime):
        self.newCommand = "t"+str(exposureTime)
        self.exposureTime = exposureTime

    def set_analog_gain(self, gain):
        self.newCommand = "g"+str(gain)
        self.gain = gain
        
    def getLast(self):
        return self.frame

    def startStreamingThread(self):
        # if we have never connected anything we should return and not always try to reconnecnt
        if self.serialdevice is None:
            return
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
                
                
    def getLastChunk(self):
        return self.frame

    def setROI(self, hpos, vpos, hsize, vsize):
        return #hsize = max(hsize, 256)  # minimum ROI
        
        
        
        

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