# %% [markdown]
# ## Prompting tasks using LangChain
# In this notebook we demonstrate how to prompt for executing tasks using chatGPT and [LangChain](https://github.com/hwchase17/langchain). Using English language, we ask for doing something with data, and LangChain will execute the task.

# %%
# !pip install https://github.com/openUC2/imswitchclient/archive/refs/heads/main.zip
from langchain.tools import tool
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.utilities import SerpAPIWrapper
from langchain.agents import initialize_agent
from langchain.agents import AgentType
from langchain.tools import tool
from imswitchclient import ImSwitchClient
import numpy as np
import time
import matplotlib.pyplot as plt

# %%
tools = []


# Define the Microscope class
class Microscope:
    def __init__(self):
        self.client = ImSwitchClient()
        self.initialPosition = self.get_initial_position()

    def get_initial_position(self):
        positioner_name = self.client.positionersManager.getAllDeviceNames()[0]
        currentPositions = self.client.positionersManager.getPositionerPositions()[positioner_name]
        return (currentPositions["X"], currentPositions["Y"], currentPositions["Z"])

    def move_to_initial_position(self):
        positioner_name = self.client.positionersManager.getAllDeviceNames()[0]
        self.client.positionersManager.movePositioner(positioner_name, "X", self.initialPosition[0], is_absolute=True, is_blocking=True)
        self.client.positionersManager.movePositioner(positioner_name, "Y", self.initialPosition[1], is_absolute=True, is_blocking=True)

    def capture_image_at_position(self, x_offset, y_offset):
        positioner_name = self.client.positionersManager.getAllDeviceNames()[0]
        x_new = self.initialPosition[0] + x_offset
        y_new = self.initialPosition[1] + y_offset
        self.client.positionersManager.movePositioner(positioner_name, "X", x_new, is_absolute=True, is_blocking=True)
        self.client.positionersManager.movePositioner(positioner_name, "Y", y_new, is_absolute=True, is_blocking=True)
        time.sleep(0.5)  # Wait for any vibrations to settle
        image = self.client.recordingManager.snapNumpyToFastAPI()
        plt.imshow(image)
        plt.show()
        return image

# Append a new tool that uses the Microscope class
@tools.append
@tool
def capture_microscope_image(xy_coordinates:list):
    """Captures an image at the specified offset from the initial microscope position."""
    x_offset, y_offset = xy_coordinates
    microscope = Microscope()
    return microscope.capture_image_at_position(x_offset, y_offset)


# %%
@tools.append
@tool
def upper_case(text:str):
    """Useful for making a text uppercase or capital letters."""
    return text.upper()

@tools.append
@tool
def lower_case(text:str):
    """Useful for making a text lowercase or small letters."""
    return text.lower()

@tools.append
@tool
def reverse(text:str):
    """Useful for making reversing order of a text."""
    return text[::-1]

# %% [markdown]
# We create some memory and a large language model based on OpenAI's chatGPT.

# %%
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

llm=ChatOpenAI(temperature=0, api_key="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")

# %% [markdown]
# Given the list of tools, the large language model and the memory, we can create an agent.

# %%
agent = initialize_agent(
    tools, 
    llm, 
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, 
    memory=memory,
    handle_parsing_errors=True
)
#%% 
moutput = agent.run("Can you go to position X/Y 100,1000 and take an image?")
print(moutput)


# %%
agent.run("Hi, I am Robert")

# %% [markdown]
# This agent can then respond to prompts.

# %%
agent.run("Hi, I am Robert")

# %% [markdown]
# As it has memory, it can remind information we gave it earlier.

# %%
agent.run("What's my name?")

# %% [markdown]
# And we can use English language to apply one of the functions above.

# %%
agent.run("Can you reverse my name?")

# %% [markdown]
# Multiple tasks can also be chained.

# %%
agent.run("Do you know my name reversed and upper case?")

# %% [markdown]
# ## Exercise
# Add a `print('Hello world')` to the function `reverse`, rerun the entire notebook and execue the last cell above multiple times. Is the `Hello world` printed every time? If not, why?

# %%



