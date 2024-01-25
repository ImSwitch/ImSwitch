#!pip install websocket-client
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
                if isinstance(msg, LineData):
                    self.process_line(msg.frame, msg.line, msg.channel, msg.data)
                elif isinstance(msg, ImagingExperimentEndData):
                    print('End data:', msg.intensity_file)
                else:
                    self.error_mode = True
                    print('Received unknown message type!!')

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
            if message_type == 0:
                # LineData
                frame, line, channel, data_length = struct.unpack_from('<IIII', binary_data, y + 1)
                y += 17 + data_length * 4
                data = struct.unpack_from('<' + 'I' * data_length, binary_data, y - data_length * 4)
                messages.append(LineData(frame, line, channel, data))
            else:
                self.error_mode = True
                print('Received unknown message type!!')
        return messages

    def process_line(self, frame, line, channel, data):
        # Implement your own logic here
        pass

class LineData:
    def __init__(self, frame, line, channel, data):
        self.frame = frame
        self.line = line
        self.channel = channel
        self.data = data

class ImagingExperimentEndData:
    def __init__(self, intensity_file):
        self.intensity_file = intensity_file

# Usage
if __name__ == "__main__":
    ws_client = WebSocketClient()
    ws_client.connect()
