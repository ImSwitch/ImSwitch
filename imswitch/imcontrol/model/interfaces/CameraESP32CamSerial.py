import time
from imswitch.imcommon.model import initLogger
from threading import Thread
import numpy as np
import serial.tools.list_ports
import base64
from PIL import Image
import io
import math

class CameraESP32CamSerial:
    def __init__(self, port=None):
        super().__init__()
        self.__logger = initLogger(self, tryInheritParent=True)

        # many to be purged
        self.port = port
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
        
        self.waitForNextFrame = True


        self.serialdevice = self.connect_to_usb_device()

    def connect_to_usb_device(self):
        if self.port is not None:
            try:
                ser = serial.Serial(self.port.device, baudrate=2000000, timeout=1)
                self.__logger.debug("Succesfully connected to previously set port")
                return ser
            except:
                pass

        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.manufacturer == self.manufacturer or port.manufacturer=="Microsoft":
                try:
                    ser = serial.Serial(port.device, baudrate=2000000, timeout=1)
                    ser.write_timeout = 1
                    self.__logger.debug(f"Connected to device: {port.description}")
                    return ser
                except serial.SerialException:
                    self.__logger.debug(f"Failed to connect to device: {port.description}")
        self.__logger.debug("No matching USB device found.")
        return None

    def calculate_base64_length(self, width, height):
        """Calculate the length of a base64 string for an image of given dimensions."""
        num_bytes = width * height
        base64_length = math.ceil((num_bytes * 4) / 3)
        # ensure length is multiple of 4
        base64_length = base64_length + (4 - base64_length % 4) % 4
        return base64_length

    def initCam(self):
        """Initialize the camera."""
        # adjust exposure time
        self.serialdevice.write(('t10\n').encode())
        while(self.serialdevice.read()):
            pass

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
        # Calculate the length of the base64 string
        base64_length = self.calculate_base64_length(self.SensorWidth, self.SensorHeight)
        lineBreakLength = 2
        waitForNextFrame = True
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
                frame_size = 320 * 240
        
                # Read the base64 string from the serial port
                lineBreakLength = 2
                base64_image_string  = self.serialdevice.read(base64_length+lineBreakLength)

                # Decode the base64 string into a 1D numpy array
                image_bytes = base64.b64decode(base64_image_string)
                image_1d = np.frombuffer(image_bytes, dtype=np.uint8)

                # Reshape the 1D array into a 2D image
                frame = image_1d.reshape(self.SensorHeight, self.SensorWidth)
                                
                frame_bytes = self.serialdevice.read(frame_size)
                frame_flat = np.frombuffer(frame_bytes, dtype=np.uint8)
                
                # Display the image
                if waitForNextFrame:
                    waitForNextFrame = False

                else:
                    # publish frame frame
                    self.frame = frame_flat.reshape((240, 320))
                
                '''
                # find 0,1,0,1... pattern to sync
                pattern = (0,1,0,1,0,1,0,1,0,1)
                window_size = len(pattern)
                for i in range(len(frame_flat) - window_size + 1):
                    # Check if the elements in the current window match the pattern
                    if np.array_equal(frame_flat[i:i+window_size], pattern):
                        break
                '''                

                nFrame += 1
                
            except Exception as e:
                # try to reconnect 
                #print(e) # most of the time "incorrect padding of the bytes "
                nFrame = 0
                nTrial+=1

                # Clear the serial buffer
                while(self.serialdevice.read()):
                    pass
                # Re-initialize the camera
                self.initCam()
                waitForNextFrame = True
                
                # Attempt a hard reset every 20 errors
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
        
        
        
        
''' ESP CODE
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
  Serial.setTimeout(20);
  cameraInit();
}

int Nx = 320;
int Ny = 240;
int Nroi = 50;
int x = 320 / 2;
int y = 240 / 2;
bool isStreaming = true;

/* setting expsorue time: t1000
setting gain: g1
getting frame: \n
restarting: r0 */
void loop()
{
  // Check for incoming serial commands
  if (Serial.available() > 0)
  {
    String command = Serial.readString(); // Read the command until a newline character is received
    if (command.length() > 1 && command.charAt(0) == 't')
    {
      // exposure time
      int value = command.substring(1).toInt(); // Extract the numeric part of the command and convert it to an integer
      // Use the value as needed
      // Apply manual settings for the camera
      sensor_t *s = esp_camera_sensor_get();
      s->set_gain_ctrl(s, 0);     // auto gain off (1 or 0)
      s->set_exposure_ctrl(s, 0); // auto exposure off (1 or 0)
      s->set_aec_value(s, value); // set exposure manually (0-1200)
    }
    else if (command.length() > 1 && command.charAt(0) == 'g')
    {
      // gain
      int value = command.substring(1).toInt(); // Extract the numeric part of the command and convert it to an integer

      // Apply manual settings for the camera
      sensor_t *s = esp_camera_sensor_get();
      s->set_gain_ctrl(s, 0);     // auto gain off (1 or 0)
      s->set_exposure_ctrl(s, 0); // auto exposure off (1 or 0)
      s->set_agc_gain(s, value);  // set gain manually (0 - 30)
    }
    else if (command.length() > 0 && command.charAt(0) == 'r')
    {
      // restart
      ESP.restart();
    }
    else
    {
      flushSerial();
      // capture image and return
      grabImage();
    }

    flushSerial();
  }
}

void flushSerial()
{
  // flush serial
  while (Serial.available() > 0)
  {
    char c = Serial.read();
  }
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

  config.pixel_format = PIXFORMAT_GRAYSCALE; // PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_QVGA;        // for streaming}

  config.fb_count = 1;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK)
  {
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  s->set_hmirror(s, 1);
  s->set_vflip(s, 1);

  // enable manual camera settings
  s->set_gain_ctrl(s, 0);     // auto gain off (1 or 0)
  s->set_exposure_ctrl(s, 0); // auto exposure off (1 or 0)
  s->set_aec_value(s, 100);   // set exposure manually (0-1200)
  s->set_agc_gain(s, 0);      // set gain manually (0 - 30)
}
void grabImage()
{
  camera_fb_t *fb = NULL;
  fb = esp_camera_fb_get();

  if (!fb || fb->format != PIXFORMAT_GRAYSCALE) // PIXFORMAT_JPEG)
  {
    Serial.println("Failed to capture image");
    ESP.restart();
  }
  else
  {
    // Modify the first 10 pixels of the buffer to indicate framesync 
    // PRoblem: The reference frame will move over time at random places 
    // It'S not clear if this is an issue on the client or server side
    // Solution: To align for it we intoduce a known pattern that we can search for
    // in order to align for this on the client side
    // (actually something funky goes on here: We don't even need to align for that on the client side if we introduce these pixels..)
    for(int i = 0; i < 10; i++){
    fb->buf[i] = i % 2;  // Alternates between 0 and 1
    }
    // delay(40);

    // String encoded = base64::encode(fb->buf, fb->len);
    // Serial.write(encoded.c_str(), encoded.length());
    Serial.write(fb->buf, fb->len);
    //Serial.println();
  }

  esp_camera_fb_return(fb);
}
'''
