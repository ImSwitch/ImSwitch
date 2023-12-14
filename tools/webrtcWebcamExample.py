# webcam_sender.py
import cv2
import asyncio
import socketio

sio = socketio.Client()

class SignalingClient:

    def __init__(self, server_url):
        self.sio = sio
        self.server_url = server_url
        self.sio.connect(self.server_url)

    def send(self, message):
        self.sio.emit('message', message)

    def on(self, event, handler_function):
        self.sio.on(event, handler_function)
        
from aiortc import RTCPeerConnection, VideoStreamTrack

class CameraVideoStreamTrack(VideoStreamTrack):
    def __init__(self, camera_id=0):
        super().__init__()
        self.cap = cv2.VideoCapture(camera_id)

    async def recv(self):
        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Error reading from camera")
        return frame

async def send_video():
    signaling = SignalingClient("https://p84s3h7i7y-496ff2e9c6d22116-8000-colab.googleusercontent.com:8000")
    pc = RTCPeerConnection()

    pc.addTrack(CameraVideoStreamTrack())

    # Connect signaling
    await signaling.connect()
    await signaling.send_offer(pc)
    await pc.wait_closed()

if __name__ == "__main__":
    asyncio.run(send_video())
