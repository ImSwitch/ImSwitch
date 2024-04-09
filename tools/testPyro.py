#%%
import Pyro5.api
from _serialize import register_serializers

#%%
register_serializers()
ipaddress = "0.0.0.0"
#ipaddress = "192.168.2.121"
#ipaddress = "192.168.2.162"
uri = 'PYRO:ImSwitchServer@'+ipaddress+':54333'
imswitchServer = Pyro5.api.Proxy(uri)

#%%
#imswitchServer.exec("ViewController", "liveview", [True])
#imswitchServer.exec("ViewController", "liveview", [False])
imswitchServer.movePositioner(positionerName=None, axis="X", dist=1000) 
imswitchServer.move(positionerName=None, axis="Y", dist=1000) 
image = imswitchServer.get_image()
# %%