


def stageCalibrationThread(self, stageName=None, scanMax=100, scanMin=-100, scanStep = 50, rescalingFac=10.0, gridScan=True):
    # we assume we have a structured sample in focus
    # the sample is moved around and the deltas are measured
    # everything has to be inside a thread

    # get current position
    if stageName is None:
        stageName = self._master.positionersManager.getAllDeviceNames()[0]
    currentPositions = self._master.positionersManager.execOn(stageName, lambda c: c.getPosition())
    self.initialPosition = (currentPositions["X"], currentPositions["Y"])
    self.initialPosiionZ = currentPositions["Z"]
    
    # snake scan
    
    if gridScan:
        xyScanStepsAbsolute = []
        fwdpath = np.arange(scanMin, scanMax, scanStep)
        bwdpath = np.flip(fwdpath)
        for indexX, ix in enumerate(np.arange(scanMin, scanMax, scanStep)): 
            if indexX%2==0:
                for indexY, iy in enumerate(fwdpath):
                    xyScanStepsAbsolute.append([ix, iy])
            else:
                for indexY, iy in enumerate(bwdpath):
                    xyScanStepsAbsolute.append([ix, iy])
        xyScanStepsAbsolute = np.array(xyScanStepsAbsolute)    
    else:
        # avoid grid pattern to be detected as same locations => random positions
        xyScanStepsAbsolute = np.random.randint(scanMin, scanMax, (10,2))

    # initialize xy coordinates
    value = xyScanStepsAbsolute[0,0] + self.initialPosition[0], xyScanStepsAbsolute[0,1] + self.initialPosition[1]
    self._master.positionersManager.execOn(stageName, lambda c: c.move(value=value[0], axis="X", is_absolute=True, is_blocking=True))
    self._master.positionersManager.execOn(stageName, lambda c: c.move(value=value[1], axis="Y", is_absolute=True, is_blocking=True))
    # store images
    allPosImages = []
    for ipos, iXYPos in enumerate(xyScanStepsAbsolute):
        
        # move to xy position is necessary
        value = iXYPos[0]+self.initialPosition[0],iXYPos[1]+self.initialPosition[1]
        self._master.positionersManager.execOn(stageName, lambda c: c.move(value=value, axis="XY", is_absolute=True, is_blocking=True))
        #TODO: do we move to the correct positions?
        # antishake
        time.sleep(0.5)
        lastFrame = self.detector.getLatestFrame()
        allPosImages.append(lastFrame)
    
    # reinitialize xy coordinates
    value = self.initialPosition[0], self.initialPosition[1]
    self._master.positionersManager.execOn(stageName, lambda c: c.move(value=value[0], axis="X", is_absolute=True, is_blocking=True))
    self._master.positionersManager.execOn(stageName, lambda c: c.move(value=value[1], axis="Y", is_absolute=True, is_blocking=True))
    # process the slices and compute their relative distances in pixels
    # compute shift between images relative to zeroth image
    self._logger.info("Starting to compute relative displacements from the first image")
    allShiftsComputed = []
    for iImage in range(len(allPosImages)):
        image1 = cv2.cvtColor(allPosImages[0], cv2.COLOR_BGR2GRAY)
        image2 = cv2.cvtColor(allPosImages[iImage], cv2.COLOR_BGR2GRAY)
        
        # downscaling will reduce accuracy, but will speed up computation
        image1 = cv2.resize(image1, dsize=None, dst=None, fx=1/rescalingFac, fy=1/rescalingFac)
        image2 = cv2.resize(image2, dsize=None, dst=None, fx=1/rescalingFac, fy=1/rescalingFac)

        shift, error, diffphase = phase_cross_correlation(image1, image2)
        shift *=rescalingFac
        self._logger.info("Shift w.r.t. 0 is:"+str(shift))
        allShiftsComputed.append((shift[0],shift[1]))
        
    # compute averrage shifts according to scan grid 
    # compare measured shift with shift given by the array of random coordinats
    allShiftsPlanned = np.array(xyScanStepsAbsolute)
    allShiftsPlanned -= np.min(allShiftsPlanned,0)
    allShiftsComputed = np.array(allShiftsComputed)

    # compute differencs
    nShiftX = (self.xScanMax-self.xScanMin)//self.xScanStep
    nShiftY = (self.yScanMax-self.yScanMin)//self.yScanStep

    # determine the axis and swap if necessary (e.g. swap axis (y,x))
    dReal = np.abs(allShiftsPlanned-np.roll(allShiftsPlanned,-1,0))
    dMeasured = np.abs(allShiftsComputed-np.roll(allShiftsComputed,-1,0))
    xAxisReal = np.argmin(np.mean(dReal,0))
    xAxisMeasured = np.argmin(np.mean(dMeasured,0))
    if xAxisReal != xAxisMeasured:
        xAxisMeasured = np.transposes(xAxisMeasured, (1,0))
    
    # stepsize => real motion / stepsize 
    stepSizeStage = (dMeasured*self.pixelSize)/dReal
    stepSizeStage[stepSizeStage == np.inf] = 0
    stepSizeStage = np.nan_to_num(stepSizeStage, nan=0.)
    stepSizeStage = stepSizeStage[np.where(stepSizeStage>0)]
    stepSizeStageDim = np.mean(stepSizeStage)
    stepSizeStageVar = np.var(stepSizeStage)

    self._logger.debug("Stage pixel size: "+str(stepSizeStageDim)+"nm/step")
    self._widget.setInformationLabel("Stage pixel size: "+str(stepSizeStageDim)+" nm/step")

    # Set in setup info
    name="test"
    self._setupInfo.setPositionerPreset(name, self.makePreset())
    configfiletools.saveSetupInfo(configfiletools.loadOptions()[0], self._setupInfo)



