import asyncio
from imjoy import api
import numpy as np
from imjoy_rpc.hypha import connect_to_server

# Now that pydantic is installed, we can safely import it
from pydantic import BaseModel, Field

class MoveByDistanceInput(BaseModel):
    """Move the stage by a specified distance, the unit of distance is millimeters, so you need to input the distance in millimeters."""
    x: float = Field(description="Move the stage along X axis.")
    y: float = Field(description="Move the stage along Y axis.")
    z: float = Field(description="Move the stage along Z axis.")

class SnapImageInput(BaseModel):
    """Snap an image from microscope."""
    exposure: int = Field(description="Set the microscope camera's exposure time. and the time unit is ms, so you need to input the time in miliseconds.")

class SetIlluminationInput(BaseModel):
    """Set the illumination of the microscope."""
    channel: int = Field(description="Set the channel of the illumination. The value should choosed from this list: BF LED matrix full=0, Fluorescence 405 nm Ex=11, Fluorescence 488 nm Ex=12, Fluorescence 638 nm Ex=13, Fluorescence 561 nm Ex  =14, Fluorescence 730 nm Ex=15.")
    intensity: float = Field(description="Set the intensity of the illumination. The value should be between 0 and 100; ")

class HomeStage(BaseModel):
    """Home the stage."""
    home: int = Field(description="Home the stage.")

class ZeroStage(BaseModel):
    """Move the stage to the zero position. Before putting sample on the stage, you also need to zero the stage."""
    zero: bool = Field(description="Zero the stage.")

class MoveToPositionInput(BaseModel):
    """Move the stage to a specified position, the unit of distance is millimeters. The limit of """
    x: float = Field(description="Move the stage to the specified position along X axis.")
    y: float = Field(description="Move the stage to the specified position along Y axis.")
    z: float = Field(description="Move the stage to the specified position along Z axis.")


async def move_stage_by_distance(kwargs):
    config = MoveByDistanceInput(**kwargs)
    #squid_svc.move_by_distance(config.x, config.y, config.z)
    print(config.x, config.y, config.z)
    return "Moved the stage!"

async def home_stage(kwargs):
    config = HomeStage(**kwargs)
    ##squid_svc.home_z()
    ##squid_svc.home_x()
    ##squid_svc.home_y()
    return "Homed the stage!"

async def zero_stage(kwargs):
    config = ZeroStage(**kwargs)
    ##squid_svc.zero_z()
    ##squid_svc.zero_x()
    ##squid_svc.zero_y()
    return "Zeroed the stage!"

async def move_to_position(kwargs):
    config = MoveToPositionInput(**kwargs)
    ##squid_svc.move_to_position(config.x, config.y, config.z)
    return "Moved the stage to the specified position!"

async def set_illumination(kwargs):
    config = SetIlluminationInput(**kwargs)
    ##squid_svc.set_illumination(config.channel, config.intensity)
    return "Set the illumination!"

async def register_extension():
    server_url = "https://chat.bioimage.io"
    try:
        import asyncio
        from imjoy_rpc.hypha import connect_to_server, login
        token = await login({"server_url": server_url})
        server = await connect_to_server({"server_url": server_url, "token": token})
        svc = await server.register_service(chatbot_extension)
        print(f"Extension service registered with id: {svc.id}, you can visit the service at: {server_url}/public/apps/bioimageio-chatbot-client/chat?extension={svc.id}")
    except Exception as e:
        print(f"Failed to register extension: {e}")


async def snap_image(kwargs):
    config = SnapImageInput(**kwargs)
    import numpy as np
    squid_image = np.random.randnint(0, 255, (512, 512))
    #squid_image = await #squid_svc.snap()
    viewer = await api.createWindow(type="itk-vtk-viewer", src="https://kitware.github.io/itk-vtk-viewer/app")
    await viewer.setImage(squid_image)
    return "Here is the image"


async def get_schema():
    return {
        "move_by_distance": MoveByDistanceInput.schema(),
        "snap_image": SnapImageInput.schema(),
        "home_stage": HomeStage.schema(),
        "zero_stage": ZeroStage.schema(),
        "move_to_position": MoveToPositionInput.schema(),
        "set_illumination": SetIlluminationInput.schema(),
    }

chatbot_extension = {
    "_rintf": True,
    "type": "bioimageio-chatbot-extension",
    "id": "UC2_microscope",
    "name": "Squid Microscope Control",
    "description": "Control the microscope based on the user's request. Now you can move the microscope stage, and snap an image.",
    "get_schema": get_schema,
    "tools": {
        "move_by_distance": move_stage_by_distance,
        "snap_image": snap_image,
        "home_stage": home_stage,
        "zero_stage": zero_stage,
        "move_to_position": move_to_position,
        "set_illumination": set_illumination,
    }
}

# Run the async function using asyncio
import asyncio
loop = asyncio.get_event_loop()
loop.create_task(register_extension())
loop.run_forever()