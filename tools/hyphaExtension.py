import asyncio
from imjoy_rpc.hypha import connect_to_server, login
import numpy as np


def move_stage(config):
    print(config["x"], config["y"], config["z"])
    return {"result": "success"}

def snap_image(config):
    print(config["snap"])
    mImage = np.random.rand(512, 512)
    # return the image as a base64 encoded string
    import base64
    import io
    import matplotlib.pyplot as plt
    buf = io.BytesIO()
    plt.imsave(buf, mImage, cmap='gray')
    buf.seek(0)
    mImage = base64.b64encode(buf.read()).decode('utf-8')
    return {"result": "success", "image": mImage}
    
def get_schema():
    return {
        "move_stage": {
            "type": "object",
            "title": "MoveStage",
            "description": "Move the microscope stage",
            "properties": {
                "x": {
                    "type": "number",
                    "description": "Move the stage along X axis in relative physical coordinates."
                },
                "y": {
                    "type": "number",
                    "description": "Move the stage along Y axis in relative physical coordinates."
                },
                "z": {
                    "type": "number",
                    "description": "Move the stage along Z axis in relative physical coordinates."
                }
            }
        },
       "snap_image": {
            "type": "object",
            "title": "SnapImage",
            "description": "Capture an image",
            "properties": {
                "snap": {
                    "type": "boolean",
                    "description": "Capture an image."
                }
            }
        }
    }


chatbot_extension = {
    "id": "UC2_microscope",
    "type": "bioimageio-chatbot-extension",
    "name": "UC2 Control Microscope",
    "description": "This exkension allows you to control the UC2 microscope, capture images, move the stage and turn on/off illumination.",
    "get_schema": get_schema,
    "tools": {
        "move_stage": move_stage,
        "snap_image": snap_image
    }
}

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

# Run the async function using asyncio
import asyncio
loop = asyncio.get_event_loop()
loop.create_task(register_extension())
loop.run_forever()