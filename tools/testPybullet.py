#%%
import pybullet
import pybullet_data
import os

#%%
pybullet.connect(pybullet.GUI)
pybullet.resetSimulation()
pybullet.setAdditionalSearchPath(pybullet_data.getDataPath())
plane = pybullet.loadURDF("plane.urdf")
#%%
robot = pybullet.loadURDF("/Users/bene/Downloads/kuka_experimental/kuka_kr210_support/urdf/kr210l150.urdf", [0, 0, 0], useFixedBase=1)
position, orientation = pybullet.getBasePositionAndOrientation(robot)
print(orientation)
pybullet.getNumJoints(robot)
joint_index = 2

#%%
joint_info = pybullet.getJointInfo(robot, joint_index)
name, joint_type, lower_limit, upper_limit = \
    joint_info[1], joint_info[2], joint_info[8], joint_info[9]
name, joint_type, lower_limit, upper_limit

#%%
pybullet.setGravity(0, 0, -9.81)   # everything should fall down
pybullet.setTimeStep(0.0001)       # this slows everything down, but let's be accurate...
pybullet.setRealTimeSimulation(0)  # we want to be faster than real time :)



# %%
pybullet.setJointMotorControlArray(
    robot, range(6), pybullet.POSITION_CONTROL,
    targetPositions=[0.1] * 6)

# %%
for _ in range(10000):
    pybullet.stepSimulation()
# %%
pybullet.resetSimulation()
plane = pybullet.loadURDF("plane.urdf")
robot = pybullet.loadURDF("kuka_experimental/kuka_kr210_support/urdf/kr210l150.urdf",
                          [0, 0, 0], useFixedBase=1)  # use a fixed base!
pybullet.setGravity(0, 0, -9.81)
pybullet.setTimeStep(0.0001)
pybullet.setRealTimeSimulation(0)
# %%
