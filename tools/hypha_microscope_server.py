import os 
import logging

import pyqtgraph.dockarea as dock
import time

import argparse
import asyncio
import fractions
import cv2
import numpy as np
#from av import VideoFrame
from imjoy_rpc.hypha import login, connect_to_server, register_rtc_service
#from imjoy_rpc.hypha.sync import register_rtc_service
#import aiortc
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription, RTCConfiguration

from aiortc.contrib.media import MediaPlayer, MediaRelay, MediaStreamTrack
from aiortc.rtcrtpsender import RTCRtpSender
from av import VideoFrame
import fractions
import json
import webbrowser
import imswitchclient.ImSwitchClient as imc 
#import UC2_control.UC2_chatbot as chatbot


current_x, current_y = 0,0

# !pip install imswitchclient
UC2Controller= imc.ImSwitchClient(host="localhost", isHttps=True, port=8001)

class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self):
        super().__init__()  # don't forget this!
        self.count = 0


    async def recv(self):
        # Read frame from UC2 controller
        rgb_img = snap()
        # Create the video frame
        new_frame = VideoFrame.from_ndarray(rgb_img, format="bgr24")
        new_frame.pts = self.count # frame.pts
        self.count+=1
        new_frame.time_base = fractions.Fraction(1, 1000)
        await asyncio.sleep(1)
        return new_frame


async def send_status(data_channel, workspace=None, token=None):
    """
    Send the current status of the microscope to the client. User can dump information of the microscope to a json data.
    ----------------------------------------------------------------
    Parameters
    ----------
    data_channel : aiortc.DataChannel
        The data channel to send the status to.
    workspace : str, optional
        The workspace to use. The default is None.
    token : str, optional
        The token to use. The default is None.

    Returns
    -------
    None.
    """
    while True:
        if data_channel and data_channel.readyState == "open":
            global current_x, current_y
            current_x, current_y, current_z, current_theta, is_illumination, _ = get_status()
            UC2_status = {"x": current_x, "y": current_y, "z": current_z, "theta": current_theta, "illumination": is_illumination}
            data_channel.send(json.dumps(UC2_status))
        await asyncio.sleep(1)  # Wait for 1 second before sending the next update


def move_by_distance(x,y,z, context=None):
    """
    Move the stage by a distance in x,y,z axis.
    ----------------------------------------------------------------
    Parameters
    ----------
    x : float
        The distance to move in x axis.
    y : float
        The distance to move in y axis.
    z : float
        The distance to move in z axis.
    context : dict, optional
            The context is a dictionary contains the following keys:
                - login_url: the login URL
                - report_url: the report URL
                - key: the key for the login
    """
    UC2Controller.navigationController.move_x(x)
    while UC2Controller.microcontroller.is_busy():
        time.sleep(0.005)
    UC2Controller.navigationController.move_y(y)
    while UC2Controller.microcontroller.is_busy():
        time.sleep(0.005)
    UC2Controller.navigationController.move_z(z)
    while UC2Controller.microcontroller.is_busy():
        time.sleep(0.005)
    print(f'The stage moved ({x},{y},{z})mm through x,y,z axis')


        
def move_to_position(x,y,z, context=None):
    """
    Move the stage to a position in x,y,z axis.
    ----------------------------------------------------------------
    Parameters
    ----------
    x : float
        The distance to move in x axis.
    y : float
        The distance to move in y axis.
    z : float
        The distance to move in z axis.
    context : dict, optional
            The context is a dictionary contains keys:
                - login_url: the login URL
                - report_url: the report URL
                - key: the key for the login
            For detailes, see: https://ha.amun.ai/#/

    """
    UC2Controller.navigationController.move_x_to(x)
    while UC2Controller.microcontroller.is_busy():
        time.sleep(0.005)
    UC2Controller.navigationController.move_y_to(y)
    while UC2Controller.microcontroller.is_busy():
        time.sleep(0.005)
    UC2Controller.navigationController.move_z_to(z)
    while UC2Controller.microcontroller.is_busy():
        time.sleep(0.005)
    print(f'The stage moved to position ({x},{y},{z})mm')


def get_status(context=None):
    """
    Get the current status of the microscope.
    ----------------------------------------------------------------
    Parameters
    ----------
        context : dict, optional
            The context is a dictionary contains keys:
                - login_url: the login URL
                - report_url: the report URL
                - key: the key for the login
            For detailes, see: https://ha.amun.ai/#/

    Returns
    -------
    current_x : float
        The current position of the stage in x axis.
    current_y : float
        The current position of the stage in y axis.
    current_z : float
        The current position of the stage in z axis.
    current_theta : float
        The current position of the stage in theta axis.
    is_illumination_on : bool
        The status of the bright field illumination.

    """
    mPositions = UC2Controller.positionersManager.getPosition()
    current_x, current_y, current_z, current_theta = mPositions["X"], mPositions["Y"], mPositions["Z"], mPositions["A"]
    is_illumination_on = True # TODO: Not implemented yet UC2Controller.liveController.illumination_on
    scan_channel = '' # TODO: Not implemented yet UC2Controller.multipointController.selected_configurations
    return current_x, current_y, current_z, current_theta, is_illumination_on,scan_channel

def snap(context=None):
    """
    Get the current frame from the camera.
    ----------------------------------------------------------------
    Parameters
    ----------
    context : dict, optional
        The context is a dictionary contains keys:
            - login_url: the login URL
            - report_url: the report URL
            - key: the key for the login
        For detailes, see: https://ha.amun.ai/#/

    Returns
    -------
    rgb_img : numpy.ndarray
        The current frame from the camera transfered to RGB image.
    """
    gray_image = UC2Controller.recordingManager.snapNumpyToFastAPI()
    rgb_image = cv2.cvtColor(gray_image, cv2.COLOR_GRAY2RGB)
    return rgb_image


def open_illumination(context=None):
    """
    Turn on the bright field illumination.
    ----------------------------------------------------------------
    Parameters
    ----------
    context : dict, optional
        The context is a dictionary contains keys:
            - login_url: the login URL
            - report_url: the report URL
            - key: the key for the login
        For detailes, see: https://ha.amun.ai/#/
    """
    UC2Controller.lasersManager.setValue(255)
    UC2Controller.lasersManager.setEnable(True)

def close_illumination(context=None):
    """
    Turn off the bright field illumination.
    ----------------------------------------------------------------
    Parameters
    ----------
    context : dict, optional
        The context is a dictionary contains keys:
            - login_url: the login URL
            - report_url: the report URL
            - key: the key for the login
        For detailes, see: https://ha.amun.ai/#/
    """
    UC2Controller.lasersManager.setValue(0)
    UC2Controller.lasersManager.setEnable(False)

def scan_well_plate(context=None):
    """
    Scan the well plate accroding to pre-defined position list.
    ----------------------------------------------------------------
    Parameters
    ----------
    context : dict, optional
        The context is a dictionary contains keys:
            - login_url: the login URL
            - report_url: the report URL
            - key: the key for the login
        For detailes, see: https://ha.amun.ai/#/
    """
    print("Start scanning well plate")
    # TODO: Not implemented yet
    # UC2Controller.scan_well_plate(action_ID='Test')

def stop_scan(context=None):
    """
    Stop the well plate scanning.
    ----------------------------------------------------------------
    Parameters
    ----------
    context : dict, optional
        The context is a dictionary contains keys:
            - login_url: the login URL
            - report_url: the report URL
            - key: the key for the login
        For detailes, see: https://ha.amun.ai/#/
    """
    print("Stop scanning well plate")
    pass
    # TODO: Not implemented yet


async def start_service(service_id, workspace=None, token=None):
    client_id = service_id + "-client"
    token = await login({"server_url": "https://ai.imjoy.io",})

    print(f"Starting service...")
    server = await connect_to_server(
        {
            "client_id": client_id,
            "server_url": "https://ai.imjoy.io",
            "workspace": workspace,
            "token": token,
        }
    )
    
    async def on_init(peer_connection):
        @peer_connection.on("track")
        def on_track(track):
            print(f"Track {track.kind} received")

            peer_connection.addTrack(
                VideoTransformTrack()
            )
         
            @track.on("ended")
            async def on_ended():
                print(f"Track {track.kind} ended")
    
        data_channel = peer_connection.createDataChannel("microscopeStatus")
        # Start the task to send stage position periodically
        asyncio.create_task(send_status(data_channel))

    await server.register_service(
        {
            "id": "microscope-control-UC2",
            "config":{
                "visibility": "public",
                "run_in_executor": True,
                "require_context": True,   
            },
            "type": "echo",
            "move_by_distance": move_by_distance,
            "snap": snap,
            "off_illumination": close_illumination,
            "on_illumination": open_illumination,
            "scan_well_plate": scan_well_plate,
            "stop_scan": stop_scan,
            
        }
    )
    
    await register_rtc_service(
        server,
        service_id=service_id,
        config={
            "visibility": "public",
            # "ice_servers": ice_servers,
            "on_init": on_init,
        },
    )
    

    print(
        f"Service (client_id={client_id}, service_id={service_id}) started successfully, available at https://ai.imjoy.io/{server.config.workspace}/services"
    )
    print(f"You can access the webrtc stream at https://aicell-lab.github.io/UC2-control/?service_id={service_id}")
    
    #await chatbot.connect_server("https://ai.imjoy.io")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="WebRTC demo for video streaming"
    )
    parser.add_argument("--service-id", type=str, default="UC2-control", help="The service id")
    parser.add_argument("--verbose", "-v", action="count")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    loop = asyncio.get_event_loop()
    loop.create_task(start_service(
        args.service_id,
        workspace=None,
        token=None,
    ))

    

    loop.run_forever()