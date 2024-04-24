

import rpyc
import numpy as np
import matplotlib.pyplot as plt 

# Connect to the RPyC server
conn = rpyc.connect("localhost", 8122)
    
    
if 0:
    c = rpyc.connect("localhost", 8122)
    remote_arr = c.root.get()
    remote_np = c.root.remote_np()
    print(remote_arr.astype(remote_np.float32))
      

conn.root.setLaserActive("LED", True)
conn.root.setLaserValue("LED", 1023)
conn.root.setLiveViewActive(True)
mImage = conn.root.snapImage(True,False)


plt.imshow(mImage)
plt.show()

    
conn.close()