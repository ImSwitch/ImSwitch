import os  
from typing import Union

def findZarrArrayPath(rootpath: str) -> Union[str, None]:
    # check if root contains .zarray
    if os.path.exists(os.path.join(rootpath, ".zarray")):
        return rootpath
    
    # check if a subdirectory in root contains .zarray
    if os.path.isdir(rootpath):
        for entry in os.listdir(rootpath):
            subpath = os.path.join(rootpath, entry)
            if os.path.isdir(subpath) and os.path.exists(os.path.join(subpath, ".zarray")): 
                return subpath
    
    return None
