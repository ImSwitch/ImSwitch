import websocket
import struct
import threading
import time
import numpy as np
import cv2

class FLIMWebsocketClient:
    def __init__(self, url='ws://localhost:3030/data', reconnect_interval=5):
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.socket = None
        self.error_mode = False
        self.mImage = None
        self.width = 0
        self.height = 0

    def setImageDimensions(self, width, height):
        self.width = width
        self.height = height
        self.mImage = np.zeros((self.width, self.height))
        self.callback_linedata = None

    def connect(self):
        def on_message(ws, message):
            if self.error_mode:
                return
            binary_data = bytearray(message)
            for msg in self.deserialize_binary_message(binary_data):
                self.process_message(msg)

        def on_error(ws, error):
            print('WebSocket error:', error)
            self.error_mode = True
            ws.close()

        def on_close(ws, close_status_code, close_msg):
            print('WebSocket closed with code:', close_status_code)
            time.sleep(self.reconnect_interval)
            self.connect()

        def on_open(ws):
            print('WebSocket connected')

        self.socket = websocket.WebSocketApp(self.url,
                                             on_open=on_open,
                                             on_message=on_message,
                                             on_error=on_error,
                                             on_close=on_close)
        wst = threading.Thread(target=self.socket.run_forever)
        wst.daemon = True
        wst.start()

    def deserialize_binary_message(self, binary_data):
        messages = []
        y = 0
        while y < len(binary_data) - 1:
            message_type = binary_data[y]
            y += 1
            if message_type == 0:
                # LineData
                frame, line, channel, data_length = struct.unpack_from('<IIII', binary_data, y)
                y += 16
                data = struct.unpack_from('<' + 'I' * data_length, binary_data, y)
                y += data_length * 4
                messages.append(LineData(frame, line, channel, data))
            elif message_type == 1:
                # CurveData
                frame, channel, data_length = struct.unpack_from('<III', binary_data, y)
                y += 12
                data = struct.unpack_from('<' + 'I' * data_length, binary_data, y)
                y += data_length * 4
                messages.append(CurveData(frame, channel, data))
            elif message_type == 2:
                # CalibrationData
                frame, channel, harmonic = struct.unpack_from('<III', binary_data, y)
                y += 12
                phase, modulation = struct.unpack_from('<dd', binary_data, y)
                y += 16
                messages.append(CalibrationData(frame, channel, harmonic, phase, modulation))
            elif message_type == 3:
                # PhasorData
                frame, channel, harmonic, g_data_rows, g_data_row_length = struct.unpack_from('<IIIII', binary_data, y)
                y += 20
                g_data = []
                for _ in range(g_data_rows):
                    g_row = struct.unpack_from('<' + 'd' * g_data_row_length, binary_data, y)
                    g_data.append(g_row)
                    y += g_data_row_length * 8
                s_data_rows, s_data_row_length = struct.unpack_from('<II', binary_data, y)
                y += 8
                s_data = []
                for _ in range(s_data_rows):
                    s_row = struct.unpack_from('<' + 'd' * s_data_row_length, binary_data, y)
                    s_data.append(s_row)
                    y += s_data_row_length * 8
                messages.append(PhasorData(frame, channel, harmonic, g_data, s_data))
            elif message_type == 4:
                # ImagingExperimentEndData
                string_length = struct.unpack_from('<I', binary_data, y)[0]
                y += 4
                if string_length == 0:
                    intensity_file = None
                else:
                    intensity_file = binary_data[y:y+string_length].decode('utf-8')
                    y += string_length
                messages.append(ImagingExperimentEndData(intensity_file))
            else:
                self.error_mode = True
                print('Received unknown message type!!')
        return messages

    def process_message(self, msg):
        if isinstance(msg, LineData):
            self.process_line_data(msg)
        elif isinstance(msg, CurveData):
            self.process_curve_data(msg)
        elif isinstance(msg, CalibrationData):
            self.process_calibration_data(msg)
        elif isinstance(msg, PhasorData):
            self.process_phasor_data(msg)
        elif isinstance(msg, ImagingExperimentEndData):
            self.process_imaging_experiment_end_data(msg)

    def setcallback_linedata(self, callback):
        self.callback_linedata = callback

    def process_line_data(self, msg):
        # Implement your logic for LineData here
        print("Received LineData:", msg.frame, msg.line, msg.channel, msg.data)
        nLines = int(np.sqrt(len(msg.data)))

        if self.mImage is not None:
            try:
                self.mImage[msg.line] = msg.data
            except:
                pass

        if self.callback_linedata is not None:
            self.callback_linedata(self.mImage)

    def process_curve_data(self, msg):
        # Implement your logic for CurveData here
        print("Received CurveData:", msg.frame, msg.channel, msg.data)
        pass

    def process_calibration_data(self, msg):
        # Implement your logic for CalibrationData here
        print("Received CalibrationData:", msg.frame, msg.channel, msg.harmonic, msg.phase, msg.modulation)
        pass

    def process_phasor_data(self, msg):
        # Implement your logic for PhasorData here
        print("Received PhasorData:", msg.frame, msg.channel, msg.harmonic, msg.g_data, msg.s_data)
        pass

    def process_imaging_experiment_end_data(self, msg):
        # Implement your logic for ImagingExperimentEndData here
        # Example: print("Experiment ended, intensity file:", msg.intensity_file)
        print("Experiment ended, intensity file:", msg.intensity_file)
        pass
class LineData:
    def __init__(self, frame, line, channel, data):
        self.frame = frame
        self.line = line
        self.channel = channel
        self.data = data

class CurveData:
    def __init__(self, frame, channel, data):
        self.frame = frame
        self.channel = channel
        self.data = data

class CalibrationData:
    def __init__(self, frame, channel, harmonic, phase, modulation):
        self.frame = frame
        self.channel = channel
        self.harmonic = harmonic
        self.phase = phase
        self.modulation = modulation

class PhasorData:
    def __init__(self, frame, channel, harmonic, g_data, s_data):
        self.frame = frame
        self.channel = channel
        self.harmonic = harmonic
        self.g_data = g_data
        self.s_data = s_data

class ImagingExperimentEndData:
    def __init__(self, intensity_file):
        self.intensity_file = intensity_file

def display_image(img):
    cv2.imshow('image', img)
    cv2.waitKey(1)

# Usage
if __name__ == "__main__":
    flim_ws = FLIMWebsocketClient()
    flim_ws.connect()

    # set image dimensions
    flim_ws.setImageDimensions(256, 256)
    flim_ws.setcallback_linedata(display_image)


    # wait for the socket to connect before sending data
    while not flim_ws.socket or not flim_ws.socket.sock or not flim_ws.socket.sock.connected:
        time.sleep(0.1)

    time.sleep(60)
