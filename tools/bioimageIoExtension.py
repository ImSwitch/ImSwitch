from imjoy_rpc import api
from pydantic import BaseModel, Field

    
class MoveStageInput(BaseModel):
    """Move the microscope stage"""
    x: float = Field(..., description="x offset")
    y: float = Field(..., description="y offset")

class SnapImageInput(BaseModel):
    """Move the microscope stage"""
    exposure: float = Field(..., description="exposure time")

async def move_stage(kwargs):
    config = MoveStageInput(**kwargs)
    print(config.x, config.y)

    return "success"

async def snap_image(kwargs):
    config = SnapImageInput(**kwargs)
    print(config.exposure)
    await api.showDialog(src="https://bioimage.io")
    return "success"

async def setup():
    chatbot = await api.createWindow(src="https://bioimage.io/chat", name="BioImage.IO Chatbot")
    
    def get_schema():
        return {
            "move_stage": MoveStageInput.schema(),
            "snap_image": SnapImageInput.schema()
        }

    extension = {
        "_rintf": True,
        "id": "uc2-control",
        "name": "UC2 Microscope Control",
        "description": "Contorl the uc2 microscope....",
        "get_schema": get_schema,
        "tools": {
            "move_stage": move_stage,
            "snap_image": snap_image,
        }
    }
    await chatbot.registerExtension(extension)

api.export({"setup": setup})
