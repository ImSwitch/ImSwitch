import os
import threading
from datetime import datetime
import time
import cv2
import matplotlib.pyplot as plt
import numpy as np
import scipy
import scipy.ndimage as ndi
import scipy.signal as signal
import skimage.transform as transform
import tifffile as tif

from imswitch.imcommon.framework import Signal, Thread, Worker, Mutex, Timer
from imswitch.imcommon.model import dirtools, initLogger, APIExport
from skimage.registration import phase_cross_correlation
from ..basecontrollers import ImConWidgetController

class ROIScanController(ImConWidgetController):
    """Linked to ROIScanWidget."""

    sigImageReceived = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = initLogger(self)

        self.roiscanTask = None
        self.roiscanStack = np.ones((1,1,1))


        # connect GUI
        self._widget.upButton.clicked.connect(lambda: self.move_stage(0, 1, 0))
        self._widget.downButton.clicked.connect(lambda: self.move_stage(0, -1, 0))
        self._widget.leftButton.clicked.connect(lambda: self.move_stage(-1, 0, 0))
        self._widget.rightButton.clicked.connect(lambda: self.move_stage(1, 0, 0))
        self._widget.plusButton.clicked.connect(lambda: self.move_stage(0, 0, 1))
        self._widget.minusButton.clicked.connect(lambda: self.move_stage(0, 0, -1))
        self._widget.saveButton.clicked.connect(self.save_coordinates)
        self._widget.deleteButton.clicked.connect(self.delete_selected_coordinates)
        self._widget.gotoButton.clicked.connect(self.go_to_selected_coordinates)
        self._widget.startButton.clicked.connect(self.start_experiment)
        self._widget.stopButton.clicked.connect(self.stop_experiment)
        
        # select detectors
        allDetectorNames = self._master.detectorsManager.getAllDeviceNames()
        self.detector = self._master.detectorsManager[allDetectorNames[0]]
        
        # select lasers and add to gui
        allLaserNames = self._master.lasersManager.getAllDeviceNames()
        
        # select stage
        self.stages = self._master.positionersManager[self._master.positionersManager.getAllDeviceNames()[0]]
        self.isRoiscanRunning = False
        
        self.sigImageReceived.connect(self.displayImage)

    def move_stage(self, x, y, z):
        if x != 0:
            self.stages.move(value=x*100, axis="X", is_absolute=False, is_blocking=False)
        if y != 0:
            self.stages.move(value=y*100, axis="Y", is_absolute=False, is_blocking=False)
        if z != 0:
            self.stages.move(value=z*100, axis="Z", is_absolute=False, is_blocking=False)
            

    def displayImage(self):
        # a bit weird, but we cannot update outside the main thread
        name = "ROIScan Stack"
        self._widget.setImage(np.uint16(self.roiscanStack ), colormap="gray", name=name, pixelsize=(1,1), translation=(0,0))

    # Additional methods for specific actions
    def save_coordinates(self):
        # Get the current XYZ coordinates (replace with actual values from the controller)
        # has to be done in background 
        def save_coordinatesThread():
            xyzpositions = self.stages.getPosition()
            x = xyzpositions["X"]
            y = xyzpositions["Y"]
            z = xyzpositions["Z"]
            
            # Create a new item for the list
            coordinate_id = self._widget.coordinatesList.count() + 1
            item_text = f"ID: {coordinate_id}, X: {x}, Y: {y}, Z: {z}"
            self._widget.coordinatesList.addItem(item_text)
        threading.Thread(target=save_coordinatesThread).start()
        
    def delete_selected_coordinates(self):
        # Get the currently selected item
        selected_item = self._widget.coordinatesList.currentItem()
        
        # If an item is selected, delete it from the list
        if selected_item:
            row = self._widget.coordinatesList.row(selected_item)
            self._widget.coordinatesList.takeItem(row)
            

    def go_to_selected_coordinates(self):
        # Get the currently selected item
        selected_item = self._widget.coordinatesList.currentItem()
        
        # If an item is selected, parse the coordinates and move to that location
        if selected_item:
            item_text = selected_item.text()
            _, x, y, z = [float(val.split(":")[1].strip()) for val in item_text.split(",")]
            
            # move x
            self.stages.move(value=x, axis="X", is_absolute=True, is_blocking=True)
            # move y
            self.stages.move(value=y, axis="Y", is_absolute=True, is_blocking=True)
            # move z
            self.stages.move(value=z, axis="Z", is_absolute=True, is_blocking=True)

    def start_experiment(self):
        # Retrieve and pass parameters to start the experiment
        self._logger.debug("Starting roi scanning.")
        self._widget.infoText.setText("Starting roi scanning.")
        try:
            experimentName = self._widget.experimentNameField.text()
            nTimes = int(self._widget.numberOfScansField.text())
            tPeriod = int(self._widget.timeIntervalField.text())
            self._widget.startButton.setEnabled(False)
            self._widget.stopButton.setEnabled(True)
            self._widget.startButton.setText("Running")
            self._widget.stopButton.setText("Stop") 
            self._widget.stopButton.setStyleSheet("background-color: red")
            self._widget.startButton.setStyleSheet("background-color: green")
            self.performScanningRecording(nTimes, tPeriod, experimentName)
        except:
            self._widget.infoText.setText("Error: Enter values")
            
        

    def stop_experiment(self):
        # Stop the experiment
        self.isRoiscanRunning = False
        self._widget.startButton.setEnabled(True)
        self._widget.stopButton.setEnabled(False)
        self._widget.startButton.setText("Start")
        self._widget.stopButton.setText("Stopped")
        self._widget.stopButton.setStyleSheet("background-color: green")
        self._widget.startButton.setStyleSheet("background-color: red")
        self._logger.debug("ROI scanning stopped.")
        
    def performScanningRecording(self, nTimes, tPeriod, experimentName):
        if not self.isRoiscanRunning:
            self.isRoiscanRunning = True
            if self.roiscanTask is not None:
                self.roiscanTask.join()
                del self.roiscanTask
            self.roiscanTask = threading.Thread(target=self.roiscanThread, args=(nTimes, tPeriod, experimentName))
            self.roiscanTask.start()
            
    def roiscanThread(self, nTimes, tPeriod, experimentName):
        # move to all coordinates in the list and take an image 
        self._logger.debug("ROI scanning thread started.")
        
        # get all coordinates from coordinatesList
        coordinates = []
        for i in range(self._widget.coordinatesList.count()):
            item_text = self._widget.coordinatesList.item(i).text()
            _, x, y, z = [float(val.split(":")[1].strip()) for val in item_text.split(",")]
            coordinates.append((x, y, z))
            
        # move to all coordinates and take an image
        iImage = 0
        currentTime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        t0 = time.time()
        for i in range(nTimes):
            allFrames = []
            for coordinate in coordinates:
                self._widget.infoText.setText("Taking image at "+str(coordinate) + " ("+str(iImage)+"/"+str(nTimes)+")")
                # move x
                self.stages.move(value=coordinate[0], axis="X", is_absolute=True, is_blocking=True)
                # move y
                self.stages.move(value=coordinate[1], axis="Y", is_absolute=True, is_blocking=True)
                # move z
                self.stages.move(value=coordinate[2], axis="Z", is_absolute=True, is_blocking=True)
                
                # take an image
                mImage = self.detector.getLatestFrame()
                allFrames.append(mImage)
                #self.sigImageReceived.emit()
            # save the stack as ometiff
            self.roiscanStack = np.stack(allFrames, axis=0)
            self.sigImageReceived.emit()
            # save the stack as ometiff including metadata including coordinates and time
            tif.imsave(currentTime + "_" + str(iImage)+experimentName+"_roiscan_stack_metadata.tif", self.roiscanStack, metadata={"X":x, "Y":y, "Z":z, "t":datetime.now().strftime("%d-%m-%Y %H:%M:%S")})
            iImage += 1
            
            # if the experiment is stopped, stop the thread
            if iImage > nTimes:
                return
            # wait for tPeriod seconds
            while 1:
                self._widget.infoText.setText("Waiting for "+str(tPeriod-(time.time()-t0)) + " seconds")
                if time.time()-t0 > tPeriod:
                    self.stop_experiment()
                    break
                if not self.isRoiscanRunning:
                    return
                time.sleep(1)
                

# Copyright (C) 2020-2021 ImSwitch developers
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
