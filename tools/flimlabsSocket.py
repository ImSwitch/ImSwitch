import websocket
import struct
import threading
import time

class WebSocketClient:
    def __init__(self, url='ws://localhost:3030/data', reconnect_interval=5):
        self.url = url
        self.reconnect_interval = reconnect_interval
        self.socket = None
        self.error_mode = False

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
                frame, line, channel, data_length = struct.unpack_from('<IIII', binary_data, y)
                y += 16
                data = struct.unpack_from('<' + 'I' * data_length, binary_data, y)
                y += data_length * 4
                messages.append(LineData(frame, line, channel, data))
            elif message_type == 1:
                # Similar unpacking for CurveData
                pass
            elif message_type == 2:
                # Similar unpacking for CalibrationData
                pass
            elif message_type == 3:
                # Similar unpacking for PhasorData
                pass
            elif message_type == 4:
                # Similar unpacking for ImagingExperimentEndData
                pass
            else:
                self.error_mode = True
                print('Received unknown message type!!')
        return messages

    def process_message(self, msg):
        if isinstance(msg, LineData):
            # Process LineData
            pass
        elif isinstance(msg, CurveData):
            # Process CurveData
            pass
        # ... other cases for different message types ...

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

# Usage
if __name__ == "__main__":
    ws_client = WebSocketClient()
    ws_client.connect()
