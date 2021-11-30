import pygame
from pygame.locals import *

pygame.init()
screen = pygame.display.set_mode((400,300))

positioner = api.imcontrol.getPositionerNames()

axis = "Z"

while True:
	for event in pygame.event.get():
		if event.type == KEYDOWN:
			if event.key == pygame.K_DOWN:
				print("Down")
				api.imcontrol.movePositioner(positioner[0], axis, 20)

			if event.key == pygame.K_UP:
				print("Up")
				api.imcontrol.movePositioner(positioner[0], axis, -20)
				
			if event.key == pygame.K_RIGHT:
				api.imcontrol.movePositioner(positioner[0], axis, 100)
				
			if event.key == pygame.K_LEFT:
				api.imcontrol.movePositioner(positioner[0], axis, -100)
				
			if event.type == pygame.QUIT:
				pygame.quit()
				exit()
