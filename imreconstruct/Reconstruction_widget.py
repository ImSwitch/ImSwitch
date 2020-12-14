# -*- coding: utf-8 -*-
"""
Created on Fri Feb 16 11:56:03 2018

@author: andreas.boden
"""

import os

import numpy as np

import pyqtgraph as pg
from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.dockarea import Dock, DockArea
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from imreconstruct.mainwindow.controllers import DataFrameController
from imreconstruct.mainwindow.widgets import DataFrame
from imreconstruct.core import PatternFinder

import tifffile as tiff
import copy

from imreconstruct.core.DataObj import DataObj
from imreconstruct.core.ReconObj import ReconObj
from imreconstruct.core.SignalExtractor import SignalExtractor

from imreconstruct.multidata.widgets import MultiDataFrame
from imreconstruct.reconstructionview.controllers import ReconstructionController
from imreconstruct.reconstructionview.widgets import ReconstructionWidget
from imreconstruct.scanparams.widgets import ScanParamsDialog


# Add path to dependency DLLs.
os.environ['PATH'] = os.environ['PATH'] + ';' + os.path.join(os.getcwd(), 'dlls')


class ReconParTree(ParameterTree):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Parameter tree for the reconstruction
        params = [
            {'name': 'Pixel size', 'type': 'float', 'value': 65, 'suffix': 'nm'},
            {'name': 'CPU/GPU', 'type': 'list', 'values': ['GPU', 'CPU']},
            {'name': 'Pattern', 'type': 'group', 'children': [
                {'name': 'Row-offset', 'type': 'float', 'value': 9.89, 'limits': (0, 9999)},
                {'name': 'Col-offset', 'type': 'float', 'value': 10.4, 'limits': (0, 9999)},
                {'name': 'Row-period', 'type': 'float', 'value': 11.05, 'limits': (0, 9999)},
                {'name': 'Col-period', 'type': 'float', 'value': 11.05, 'limits': (0, 9999)},
                {'name': 'Find pattern', 'type': 'action'}]},
            {'name': 'Reconstruction options', 'type': 'group', 'children': [
                {'name': 'PSF FWHM', 'type': 'float', 'value': 220, 'limits': (0, 9999),
                 'suffix': 'nm'},
                {'name': 'BG modelling', 'type': 'list',
                 'values': ['Constant', 'Gaussian', 'No background'], 'children': [
                    {'name': 'BG Gaussian size', 'type': 'float', 'value': 500, 'suffix': 'nm'}]}]},
            {'name': 'Scanning parameters', 'type': 'action'},
            {'name': 'Show pattern', 'type': 'bool'}]

        self.p = Parameter.create(name='params', type='group', children=params)
        self.setParameters(self.p, showTop=False)
        self._writable = True


class ReconWid(QtGui.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('MoNaLISA Reconstruction')
        self.setWindowIcon(QtGui.QIcon(r'/Graphics/ML_logo.ico'))

        """self parameters"""
        self.r_l_text = 'Right/Left'
        self.u_d_text = 'Up/Down'
        self.b_f_text = 'Back/Forth'
        self.timepoints_text = 'Timepoints'
        self.p_text = 'pos'
        self.n_text = 'neg'

        self.current_data = None

        # Actions in menubar
        menubar = self.menuBar()
        File = menubar.addMenu('&File')

        saveReconAction = QtGui.QAction('Save reconstruction', self)
        saveReconAction.setShortcut('Ctrl+S')
        saveReconAction.triggered.connect(lambda: self.save_current('reconstruction'))
        File.addAction(saveReconAction)
        saveCoeffsAction = QtGui.QAction('Save coefficients', self)
        saveCoeffsAction.setShortcut('Ctrl+A')
        saveCoeffsAction.triggered.connect(lambda: self.save_current('coefficients'))
        File.addAction(saveCoeffsAction)

        setDataFolder = QtGui.QAction('Set data folder', self)
        setDataFolder.triggered.connect(self.SetDataFolder)
        File.addAction(setDataFolder)

        setSaveFolder = QtGui.QAction('Set save folder', self)
        setSaveFolder.triggered.connect(self.SetSaveFolder)
        File.addAction(setSaveFolder)

        self.extractor = SignalExtractor('dlls\GPU_acc_recon.dll')
        self.pat_finder = PatternFinder.PatternFinder()
        self.data_frame = DataFrame(DataFrameController)
        self.multi_data_frame = MultiDataFrame()
        self.multi_data_frame.sigCurrentDataChanged.connect(self.changeAndShowCurrentData)
        btn_frame = BtnFrame(self)
        btn_frame.recon_curr_sig.connect(self.reconstruct_current)
        btn_frame.recon_multi_sig.connect(self.reconstruct_multi)
        btn_frame.q_load_data_sig.connect(self.quick_load_data)
        btn_frame.update_sig.connect(self.update)

        self.ReconstructionWidget = ReconstructionWidget(ReconstructionController)

        self.partree = ReconParTree()
        self.scanningParDict = {
            'dimensions': [self.r_l_text, self.u_d_text, self.b_f_text, self.timepoints_text],
            'directions': [self.p_text, self.p_text, self.p_text],
            'steps': ['35', '35', '1', '1'],
            'step_sizes': ['35', '35', '35', '1'],
            'unidirectional': True}
        self.scanningParWindow = ScanParamsDialog(self,
                                                  self.scanningParDict,
                                                  self.r_l_text,
                                                  self.u_d_text,
                                                  self.b_f_text,
                                                  self.timepoints_text,
                                                  self.p_text,
                                                  self.n_text)

        parameterFrame = QtGui.QFrame()
        parameterGrid = QtGui.QGridLayout()
        parameterFrame.setLayout(parameterGrid)
        parameterGrid.addWidget(self.partree, 0, 0)

        DataDock = DockArea()

        MultiDataDock = Dock('Multidata management')
        MultiDataDock.addWidget(self.multi_data_frame)
        DataDock.addDock(MultiDataDock)

        CurrentDataDock = Dock('Current data')
        CurrentDataDock.addWidget(self.data_frame)
        DataDock.addDock(CurrentDataDock, 'above', MultiDataDock)

        layout = QtGui.QHBoxLayout()
        self.cwidget = QtGui.QWidget()
        self.setCentralWidget(self.cwidget)
        self.cwidget.setLayout(layout)

        leftContainer = QtGui.QVBoxLayout()
        leftContainer.setContentsMargins(0, 0, 0, 0)

        rightContainer = QtGui.QVBoxLayout()
        rightContainer.setContentsMargins(0, 0, 0, 0)

        leftContainer.addWidget(parameterFrame, 1)
        leftContainer.addWidget(btn_frame, 0)
        leftContainer.addWidget(DataDock, 1)
        rightContainer.addWidget(self.ReconstructionWidget)

        layout.addLayout(leftContainer, 1)
        layout.addLayout(rightContainer, 3)

        pg.setConfigOption('imageAxisOrder', 'row-major')

        self.show_pat_bool = self.partree.p.param('Show pattern')
        self.show_pat_bool.sigStateChanged.connect(self.toggle_pattern)
        self.find_pat_btn = self.partree.p.param('Pattern').param('Find pattern')
        self.find_pat_btn.sigStateChanged.connect(self.find_pattern)
        self.scanParWin_btn = self.partree.p.param('Scanning parameters')
        self.scanParWin_btn.sigStateChanged.connect(self.update_scanning_pars)

        self.update_pattern()

        self.partree.p.param('Pattern').sigTreeStateChanged.connect(self.update_pattern)

        self.showMaximized()

    def test(self):
        print('Test fcn run')

    def update_scanning_pars(self):
        self.scanningParWindow.show()

    def find_pattern(self):
        print('Find pattern clicked')
        meanData = self.current_data.getMeanData()
        if len(meanData) > 0:
            print('Finding pattern')
            pattern = self.pat_finder.find_pattern(meanData)
            print('Pattern found as: ', self.pattern)
            pattern_pars = self.partree.p.param('Pattern')
            pattern_pars.param('Row-offset').setValue(pattern[0])
            pattern_pars.param('Col-offset').setValue(pattern[1])
            pattern_pars.param('Row-period').setValue(pattern[2])
            pattern_pars.param('Col-period').setValue(pattern[3])
            self.update_pattern()

    def SetDataFolder(self):
        self.data_folder = QtGui.QFileDialog.getExistingDirectory()
        self.multi_data_frame.data_folder = self.data_folder

    def SetSaveFolder(self):
        self.save_folder = QtGui.QFileDialog.getExistingDirectory()

    def toggle_pattern(self):
        print('Toggling pattern')
        if self.show_pat_bool.value():
            self.data_frame.pattern = self.pattern

        self.data_frame.setShowPattern(self.show_pat_bool.value())

    def update_pattern(self):
        print('Updating pattern')
        pattern_pars = self.partree.p.param('Pattern')
        self.pattern = [np.mod(pattern_pars.param('Row-offset').value(),
                               pattern_pars.param('Row-period').value()),
                        np.mod(pattern_pars.param('Col-offset').value(),
                               pattern_pars.param('Col-period').value()),
                        pattern_pars.param('Row-period').value(),
                        pattern_pars.param('Col-period').value()]

        if self.data_frame.getShowPattern():
            self.data_frame.pattern = self.pattern
            self.data_frame.make_pattern_grid()

    def update(self):

        self.ReconstructionWidget.UpdateScanPars(self.scanningParDict)

    def quick_load_data(self):

        dlg = QtGui.QFileDialog()
        if hasattr(self, 'data_folder'):
            datapath = dlg.getOpenFileName(directory=self.data_folder)[0]
        else:
            datapath = dlg.getOpenFileName()[0]

        if datapath:
            print('Loading data at:', datapath)

            name = os.path.split(datapath)[1]
            if not self.current_data is None:
                self.current_data.checkAndUnloadData()
            self.current_data = DataObj(name, datapath)
            self.current_data.checkAndLoadData()
            if self.current_data.data_loaded == True:
                self.data_frame.setData(self.current_data)
                self.multi_data_frame.allWhite()
                print('Data loaded')
            else:
                pass

    def changeAndShowCurrentData(self):
        self.currDataChanged()
        self.showCurrentData()

    def currDataChanged(self):

        newCurrDataObj = self.multi_data_frame.data_list.currentItem().data(1)
        newCurrDataObj.checkAndLoadData()

        self.current_data = newCurrDataObj

    def showCurrentData(self):
        self.data_frame.setData(self.current_data)

    def extract_data(self):

        recon_pars = self.partree.p.param('Reconstruction options')
        fwhm_nm = recon_pars.param('PSF FWHM').value()
        if recon_pars.param('BG modelling').value() == 'Constant':
            fwhm_nm = np.append(fwhm_nm, 9999)  # Code for constant bg
        elif recon_pars.param('BG modelling').value() == 'No background':
            fwhm_nm = np.append(fwhm_nm, 0)  # Code for zero bg
        else:
            print('In Gaussian version')
            fwhm_nm = np.append(fwhm_nm,
                                recon_pars.param('BG modelling').param('BG Gaussian size').value())
            print('Appended to sigmas')

        sigmas = np.divide(
            fwhm_nm, 2.355 * self.partree.p.param('Pixel size').value())

        if self.partree.p.param('CPU/GPU').value() == 'CPU':
            coeffs = self.extractor.extract_signal(self.current_data.data, sigmas, self.pattern,
                                                   'cpu')
        elif self.partree.p.param('CPU/GPU').value() == 'GPU':
            coeffs = self.extractor.extract_signal(self.current_data.data, sigmas, self.pattern,
                                                   'gpu')

        return coeffs

    def reconstruct_current(self):
        if self.current_data is None:
            pass
        elif np.prod(
                np.array(self.scanningParDict['steps'], dtype=np.int)) < self.current_data.frames:
            print('Too many frames in data')
        else:
            coeffs = self.extract_data()

            reconObj = ReconObj(self.current_data.name,
                                self.scanningParDict,
                                self.r_l_text,
                                self.u_d_text,
                                self.b_f_text,
                                self.timepoints_text,
                                self.p_text,
                                self.n_text)
            reconObj.addCoeffsTP(coeffs)
            reconObj.update_images()

            self.ReconstructionWidget.AddNewData(reconObj)

    def reconstruct_multi(self):
        data_list = self.multi_data_frame.data_list

        for i in range(data_list.count()):
            self.current_data = data_list.item(i).data(1)
            pre_loaded = self.current_data.data_loaded
            self.current_data.checkAndLoadData()
            coeffs = self.extract_data()
            reconObj = ReconObj(self.current_data.name,
                                self.scanningParDict,
                                self.r_l_text,
                                self.u_d_text,
                                self.b_f_text,
                                self.timepoints_text,
                                self.p_text,
                                self.n_text)
            if not pre_loaded:
                data_list.item(i).data(1).checkAndUnloadData()
            reconObj.addCoeffsTP(coeffs)
            reconObj.update_images()
            self.ReconstructionWidget.AddNewData(reconObj)

    def save_current(self, data_type=None):
        """Saves the reconstructed image from self.reconstructor to specified
        destination"""
        if data_type:
            dlg = QtGui.QFileDialog()
            if hasattr(self, 'save_folder'):
                savename = \
                dlg.getSaveFileName(self, 'Save File', filter='*.tiff', directory=self.save_folder)[
                    0]
            else:
                savename = dlg.getSaveFileName(self, 'Save File', filter='*.tiff')[0]
            print(savename)
            if savename:
                if data_type == 'reconstruction':
                    reconstruction_obj = self.ReconstructionWidget.recon_list.currentItem().data(1)
                    vxsizec = int(reconstruction_obj.scanningParDict['step_sizes'][
                                      self.scanningParDict['dimensions'].index(self.r_l_text)])
                    vxsizer = int(reconstruction_obj.scanningParDict['step_sizes'][
                                      self.scanningParDict['dimensions'].index(self.u_d_text)])
                    vxsizez = int(reconstruction_obj.scanningParDict['step_sizes'][
                                      self.scanningParDict['dimensions'].index(self.b_f_text)])
                    dt = int(reconstruction_obj.scanningParDict['step_sizes'][
                                 self.scanningParDict['dimensions'].index(self.timepoints_text)])

                    print('Trying to save to: ', savename, 'Vx size:', vxsizec, vxsizer, vxsizez)
                    # Reconstructed image
                    reconstr_data = copy.deepcopy(reconstruction_obj.getReconstruction())
                    reconstr_data = reconstr_data[:, 0, :, :, :, :]
                    reconstr_data.shape = reconstr_data.shape[0], reconstr_data.shape[1], \
                                          reconstr_data.shape[2], reconstr_data.shape[3], \
                                          reconstr_data.shape[4], 1
                    reconstr_data = np.swapaxes(reconstr_data, 1, 2)
                    tiff.imwrite(savename, reconstr_data,
                                 imagej=True, resolution=(1 / vxsizec, 1 / vxsizer),
                                 metadata={'spacing': vxsizez, 'unit': 'nm', 'axes': 'TZCYX'})
                elif data_type == 'coefficients':
                    coeffs = copy.deepcopy(self.ReconstructionWidget.getCurrentItemData().getCoeffs())
                    print('Shape of coeffs = ', coeffs.shape)
                    try:
                        coeffs = np.swapaxes(coeffs, 1, 2)
                        tiff.imwrite(savename, coeffs,
                                     imagej=True, resolution=(1, 1),
                                     metadata={'spacing': 1, 'unit': 'px', 'axes': 'TZCYX'})
                    except:
                        pass
                else:
                    print('Data type in save_current not recognized')
            else:
                print('No saving path given')
        else:
            print('No data type given in save current')


class BtnFrame(QtWidgets.QFrame):
    recon_curr_sig = QtCore.pyqtSignal()
    recon_multi_sig = QtCore.pyqtSignal()
    q_load_data_sig = QtCore.pyqtSignal()
    update_sig = QtCore.pyqtSignal()

    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)

        recon_curr_btn = QtWidgets.QPushButton('Reconstruct current')
        recon_curr_btn.clicked.connect(self.recon_curr_sig.emit)
        recon_multi_btn = QtWidgets.QPushButton('Reconstruct multidata')
        recon_multi_btn.clicked.connect(self.recon_multi_sig.emit)
        q_load_data_btn = QtWidgets.QPushButton('Quick load data')
        q_load_data_btn.clicked.connect(self.q_load_data_sig.emit)
        update_btn = QtWidgets.QPushButton('Update reconstruction')
        update_btn.clicked.connect(self.update_sig.emit)

        layout = QtGui.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(q_load_data_btn, 0, 0, 1, 2)
        layout.addWidget(recon_curr_btn, 1, 0)
        layout.addWidget(recon_multi_btn, 1, 1)
        layout.addWidget(update_btn, 2, 0, 1, 2)
