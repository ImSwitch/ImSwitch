import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets, QtGui
from pyqtgraph.parametertree import Parameter, ParameterTree

from imswitch.imcontrol.view import guitools as guitools

def remove_none(obj):
  if isinstance(obj, (list, tuple, set)):
    return type(obj)(remove_none(x) for x in obj if x is not None)
  elif isinstance(obj, dict):
    return type(obj)((remove_none(k), remove_none(v))
      for k, v in obj.items() if k is not None and v is not None)
  else:
    return obj

slmFrame = pg.GraphicsLayoutWidget()
slmParameterTree = ParameterTree()
generalparams = [{'name': 'general', 'type': 'group', 'children': [
                    {'name': 'radius', 'type': 'float', 'value': 100, 'limits': (0, 600), 'step': 1,
                    'suffix': 'px'},
                    {'name': 'sigma', 'type': 'float', 'value': 35, 'limits': (1, 599), 'step': 0.1,
                    'suffix': 'px'}
                    ]}]
slmParameterTree.p = pg.parametertree.Parameter.create(name='params', type='group',children=generalparams)
slmParameterTree.setParameters(slmParameterTree.p, showTop=False)
slmParameterTree._writable = True

aberParameterTree = ParameterTree()
aberlim = 2
aberparams = [{'name': 'left', 'type': 'group', 'children': [
    {'name': 'tilt', 'type': 'float', 'value': 0.1, 'limits': (-aberlim, aberlim),
        'step': 0.01},
    {'name': 'tip', 'type': 'float', 'value': 0.2, 'limits': (-aberlim, aberlim),
        'step': 0.01},
    {'name': 'defocus', 'type': 'float', 'value': 0.3, 'limits': (-aberlim, aberlim),
        'step': 0.01},
    {'name': 'spherical', 'type': 'float', 'value': 0.4, 'limits': (-aberlim, aberlim),
        'step': 0.01},
    {'name': 'verticalComa', 'type': 'float', 'value': 0.5,
        'limits': (-aberlim, aberlim), 'step': 0.01},
    {'name': 'horizontalComa', 'type': 'float', 'value': 0.6,
        'limits': (-aberlim, aberlim), 'step': 0.01},
    {'name': 'verticalAstigmatism', 'type': 'float', 'value': 0.7,
        'limits': (-aberlim, aberlim), 'step': 0.01},
    {'name': 'obliqueAstigmatism', 'type': 'float', 'value': 0.8,
        'limits': (-aberlim, aberlim), 'step': 0.01}
]},
                    {'name': 'right', 'type': 'group', 'children': [
                        {'name': 'tilt', 'type': 'float', 'value': 0.9,
                        'limits': (-aberlim, aberlim), 'step': 0.01},
                        {'name': 'tip', 'type': 'float', 'value': 1.0,
                        'limits': (-aberlim, aberlim), 'step': 0.01},
                        {'name': 'defocus', 'type': 'float', 'value': 1.1,
                        'limits': (-aberlim, aberlim), 'step': 0.01},
                        {'name': 'spherical', 'type': 'float', 'value': 1.2,
                        'limits': (-aberlim, aberlim), 'step': 0.01},
                        {'name': 'verticalComa', 'type': 'float', 'value': 1.3,
                        'limits': (-aberlim, aberlim), 'step': 0.01},
                        {'name': 'horizontalComa', 'type': 'float', 'value': 1.4,
                        'limits': (-aberlim, aberlim), 'step': 0.01},
                        {'name': 'verticalAstigmatism', 'type': 'float', 'value': 1.5,
                        'limits': (-aberlim, aberlim), 'step': 0.01},
                        {'name': 'obliqueAstigmatism', 'type': 'float', 'value': 1.6,
                        'limits': (-aberlim, aberlim), 'step': 0.01}
                    ]}]

aberParameterTree.p = pg.parametertree.Parameter.create(name='params', type='group',
                                                                children=aberparams)
aberParameterTree.setParameters(aberParameterTree.p, showTop=False)
aberParameterTree._writable = True



#print(slmParameterTree)
#print(slmParameterTree.p.getValues())
#orddict = slmParameterTree.p.getValues()
#print(orddict["general"])

print(slmParameterTree.p.getValues()["general"][1]["radius"][0])
print(slmParameterTree.p.getValues()["general"][1]["sigma"][0])

print(aberParameterTree.p.getValues()["left"][1]["tilt"][0])
print(aberParameterTree.p.getValues()["left"][1]["tip"][0])
print(aberParameterTree.p.getValues()["left"][1]["defocus"][0])
print(aberParameterTree.p.getValues()["left"][1]["spherical"][0])
print(aberParameterTree.p.getValues()["left"][1]["verticalComa"][0])
print(aberParameterTree.p.getValues()["left"][1]["horizontalComa"][0])
print(aberParameterTree.p.getValues()["left"][1]["verticalAstigmatism"][0])
print(aberParameterTree.p.getValues()["left"][1]["obliqueAstigmatism"][0])

print(aberParameterTree.p.getValues()["right"][1]["tilt"][0])
print(aberParameterTree.p.getValues()["right"][1]["tip"][0])
print(aberParameterTree.p.getValues()["right"][1]["defocus"][0])
print(aberParameterTree.p.getValues()["right"][1]["spherical"][0])
print(aberParameterTree.p.getValues()["right"][1]["verticalComa"][0])
print(aberParameterTree.p.getValues()["right"][1]["horizontalComa"][0])
print(aberParameterTree.p.getValues()["right"][1]["verticalAstigmatism"][0])
print(aberParameterTree.p.getValues()["right"][1]["obliqueAstigmatism"][0])