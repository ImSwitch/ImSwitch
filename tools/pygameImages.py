
## -*- coding: utf-8 -*-
"""
Created on Mon Jan 24 17:29:43 2022

@author: wanghaoran
"""

import pygame
import time
from os import listdir
from os.path import isfile, join
import numpy as np


mypath = "C:\\Users\\admin\\Downloads\\2024_01_model_validation\\"
myimg = [f for f in listdir(mypath) if isfile(join(mypath, f))]
myimg.sort()
running = True
display = pygame.display.set_mode([1920,1080],pygame.FULLSCREEN,display = 0) #config
pygame.mouse.set_visible(False)
mytime = 0.03
##########################

for i in range(10):#np.size(myimg)):
    #myimg = 'D:\\DLP2000\\screenshot' + str(i+1).zfill(3) + '.png'
    surf = pygame.image.load(str(mypath+'/'+myimg[i]))
    display.blit(surf,(0,0)) #image reso 1920x1080
    #display.blit(surf,(320,28)) #image reso 1280x1024
    pygame.display.update()
    #surf.draw()         
    print(i)    
    time.sleep(mytime)
    pygame.event.pump() #allow pygame to handle internal actions
    print(myimg[i])
    #pygame.display.update()

pygame.display.quit()
