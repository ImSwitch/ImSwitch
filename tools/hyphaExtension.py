import asyncio
from imjoy_rpc.hypha import connect_to_server, login

def get_schema():
    return {
        "my_tool": {
            "type": "object",
            "properties": {
                "my_param": {
                    "type": "number",
                    "description": "This is my parameter"
                }
            }
        }
    }

def my_tool(config):
    print(config["my_param"])
    return {"result": "success"}

chatbot_extension = {
    "id": "my-extension111",
    "type": "bioimageio-chatbot-extension",
    "name": "My Extension BD",
    "description": "This is my extension",
    "get_schema": get_schema,
    "tools": {
        "my_tool": my_tool
    }
}

async def register_extension():
    server_url = "https://chat.bioimage.io"
    try:
        server = await connect_to_server({"server_url": server_url})
        svc = await server.register_service(chatbot_extension)
        print(f"Extension service registered with id: {svc.id}, you can visit the service at: {server_url}/public/apps/bioimageio-chatbot-client/chat?extension={svc.id}")
    except Exception as e:
        print(f"Failed to register extension: {e}")

# Run the async function using asyncio
if __name__ == "__main__":
    asyncio.run(register_extension())
    input()
