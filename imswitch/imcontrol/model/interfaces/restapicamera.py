import requests
import json
from PIL import Image
from io import BytesIO
import numpy as np
import socket


class RestPiCamera():
    def __init__(self, host, port=80):
        self. base_uri = f"{host}:{port}"
        self.host = host
        self.port = port 
        self.SensorWidth = -1
        self.SensorHeight = - 1
        self.is_connected = self.isConnected()  

        self.SensorWidth, self.SensorHeight = self.get_resolution_preview()

    def isConnected(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if len(self.host.split("http://")) > 0:
            host = self.host.split("http://")[-1]
        else:
            host = self.host
        is_up = False
        try:
            s.connect((host, int(self.port)))
            s.settimeout(2)
            s.shutdown(2)
            is_up = True
        except:
            pass
        return is_up

    def get_json(self, path, payload=None):
        """Perform an HTTP GET request and return the JSON response"""
        if self.is_connected:
            if not path.startswith("http"):
                path = self.base_uri + path
            if payload is not None:
                r = requests.get(path, payload)
            else:
                r = requests.get(path)
                
            r.raise_for_status()
            return r.json()
        else:
            return None

    def post_json(self, path, payload={}):
        """Make an HTTP POST request and return the JSON response"""
        if self.is_connected:
            if not path.startswith("http"):
                path = self.base_uri + path
            r = requests.post(path, json=payload)
            r.raise_for_status()
            r = r.json()
            return r
        else:
            return None

    def set_iso(self, iso):
        path = '/picamera/iso'
        payload = {
            "iso": iso
        }
        return_message = self.post_json(path, payload)
        print(return_message)

    def get_iso(self):
        # do homing of the robot
        path = '/picamera/iso'
        return_message = self.get_json(path)
        print(return_message)

    # DP 04/2024: unit approach to unit of exposure time is missing
    def set_exposuretime(self, exposuretime):
        path = '/picamera/exposuretime'
        payload = {
            "exposuretime": exposuretime
        }
        return_message = self.post_json(path, payload)
        print(return_message)

    def get_exposuretime(self):
        # do homing of the robot
        path = '/picamera/exposuretime'
        return_message = self.get_json(path)
        print(return_message)

    def get_snap(self):
        path = '/picamera/singleframe'
        r = requests.get(self.base_uri + path)
        r.raise_for_status()
        image = Image.open(BytesIO(r.content))
        return np.asarray(image)

    def get_resolution_preview(self):
        # do homing of the robot
        path = '/picamera/resolution_preview'
        return_message = self.get_json(path)
        Nx, Ny = return_message["Nx"], return_message["Ny"]
        return Nx, Ny
        
    def get_preview(self):
        path = '/picamera/singleframe'
        r = requests.get(self.base_uri + path)
        r.raise_for_status()
        image = Image.open(BytesIO(r.content))
        return np.asarray(image)

    def start_live(self):
        path = '/picamera/startstream'
        payload = {}
        return_message = self.post_json(path, payload)
        return return_message

    def stop_live(self):
        path = '/picamera/stopstream'
        payload = {}
        return_message = self.post_json(path, payload)
        return return_message

if __name__ == "__main__":
    host = "http://0.0.0.0"
    port = "5000"

    rc = RestPiCamera(host, port)
    print(rc.get_iso())
    print(rc.get_snap())
