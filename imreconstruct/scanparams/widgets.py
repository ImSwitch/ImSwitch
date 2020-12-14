from pyqtgraph.Qt import QtGui


class ScanParamsDialog(QtGui.QDialog):
    """Seperate window for editing scanning parameters"""
    def __init__(self, main, parDict, r_l_text, u_d_text, b_f_text, timepoints_text, p_text, n_text, *args, **kwargs):
        super().__init__(main, *args, **kwargs)

        self.parDict = parDict

        im_dim_label = QtGui.QLabel('Image dimension')
        dim_dir_label = QtGui.QLabel('Direction')
        im_steps_label = QtGui.QLabel('Steps')
        im_step_size_label = QtGui.QLabel('Step size (nm)')

        self.r_l_text = r_l_text
        self.u_d_text = u_d_text
        self.b_f_text = b_f_text
        self.p_text = p_text
        self.timepoints_text = timepoints_text
        self.n_text = n_text

        dim0_label = QtGui.QLabel('Dimension 0')
        self.dim0_dim_edit = QtGui.QComboBox()
        self.dim0_dim_edit.addItems([self.r_l_text, self.u_d_text, self.b_f_text])
        self.dim0_dim_edit.currentIndexChanged.connect(self.dim0_changed)
        self.dim0_dir_edit = QtGui.QComboBox()
        self.dim0_dir_edit.addItems([self.p_text, self.n_text])
        self.dim0_size_edit = QtGui.QLineEdit()
        self.dim0_size_edit.returnPressed.connect(lambda: self.checkForInt(self.dim0_size_edit))
        self.dim0_step_size_edit = QtGui.QLineEdit()

        dim1_label = QtGui.QLabel('Dimension 1')
        self.dim1_dim_edit = QtGui.QComboBox()
        self.dim1_dim_edit.currentIndexChanged.connect(self.dim1_changed)
        self.dim1_dir_edit = QtGui.QComboBox()
        self.dim1_dir_edit.addItems([self.p_text, self.n_text])
        self.dim1_size_edit = QtGui.QLineEdit()
        self.dim1_size_edit.returnPressed.connect(lambda: self.checkForInt(self.dim1_size_edit))
        self.dim1_step_size_edit = QtGui.QLineEdit()

        dim2_label = QtGui.QLabel('Dimension 2')
        self.dim2_dim_edit = QtGui.QComboBox()
        self.dim2_dir_edit = QtGui.QComboBox()
        self.dim2_dir_edit.addItems([self.p_text, self.n_text])
        self.dim2_size_edit = QtGui.QLineEdit()
        self.dim2_size_edit.returnPressed.connect(lambda: self.checkForInt(self.dim2_size_edit))
        self.dim2_step_size_edit = QtGui.QLineEdit()

        dim3_label = QtGui.QLabel('Dimension 3')
        self.dim3_dim_label = QtGui.QLabel(self.timepoints_text)
        self.dim3_size_edit = QtGui.QLineEdit()
        self.dim3_size_edit.returnPressed.connect(lambda: self.checkForInt(self.dim3_size_edit))
        self.dim3_step_size_edit = QtGui.QLineEdit()

        self.unidir_check = QtGui.QCheckBox('Unidirectional scan')

        OK_btn = QtGui.QPushButton('OK')
        OK_btn.pressed.connect(self.OK_pressed)

        layout = QtGui.QGridLayout()
        self.setLayout(layout)

        layout.addWidget(im_dim_label, 0, 1)
        layout.addWidget(dim_dir_label, 0, 2)
        layout.addWidget(im_steps_label, 0, 3)
        layout.addWidget(im_step_size_label, 0, 4)
        layout.addWidget(dim0_label, 1, 0)
        layout.addWidget(self.dim0_dim_edit, 1, 1)
        layout.addWidget(self.dim0_dir_edit, 1, 2)
        layout.addWidget(self.dim0_size_edit, 1, 3)
        layout.addWidget(self.dim0_step_size_edit, 1, 4)
        layout.addWidget(dim1_label, 2, 0)
        layout.addWidget(self.dim1_dim_edit, 2, 1)
        layout.addWidget(self.dim1_dir_edit, 2, 2)
        layout.addWidget(self.dim1_size_edit, 2, 3)
        layout.addWidget(self.dim1_step_size_edit, 2, 4)
        layout.addWidget(dim2_label, 3, 0)
        layout.addWidget(self.dim2_dim_edit, 3, 1)
        layout.addWidget(self.dim2_dir_edit, 3, 2)
        layout.addWidget(self.dim2_size_edit, 3, 3)
        layout.addWidget(self.dim2_step_size_edit, 3, 4)
        layout.addWidget(dim3_label, 4, 0)
        layout.addWidget(self.dim3_dim_label, 4, 1)
        layout.addWidget(self.dim3_size_edit, 4, 3)
        layout.addWidget(self.dim3_step_size_edit, 4, 4)
        layout.addWidget(self.unidir_check, 5, 1)
        layout.addWidget(OK_btn, 5, 2)

        #Initiate values
        try:
            self.dim0_dim_edit.setCurrentIndex(self.dim0_dim_edit.findText(self.parDict['dimensions'][0]))
            self.dim1_dim_edit.setCurrentIndex(self.dim1_dim_edit.findText(self.parDict['dimensions'][1]))
            self.dim2_dim_edit.setCurrentIndex(self.dim2_dim_edit.findText(self.parDict['dimensions'][2]))
            self.dim0_changed()

            self.dim0_dir_edit.setCurrentIndex(self.dim0_dir_edit.findText(self.parDict['directions'][0]))
            self.dim1_dir_edit.setCurrentIndex(self.dim1_dir_edit.findText(self.parDict['directions'][1]))
            self.dim2_dir_edit.setCurrentIndex(self.dim2_dir_edit.findText(self.parDict['directions'][2]))

            self.dim0_size_edit.setText(self.parDict['steps'][0])
            self.dim1_size_edit.setText(self.parDict['steps'][1])
            self.dim2_size_edit.setText(self.parDict['steps'][2])
            self.dim3_size_edit.setText(self.parDict['steps'][3])

            self.dim0_step_size_edit.setText(self.parDict['step_sizes'][0])
            self.dim1_step_size_edit.setText(self.parDict['step_sizes'][1])
            self.dim2_step_size_edit.setText(self.parDict['step_sizes'][2])
            self.dim3_step_size_edit.setText(self.parDict['step_sizes'][3])

            self.unidir_check.setChecked(self.parDict['unidirectional'])
        except:
            print('Error setting initial values')
            self.dim0_changed()

    def checkForInt(self, parameter):
        try:
            int(parameter.text())
        except ValueError:
            parameter.setText('1')
            print('Cannot interpret given value as integer')

    def dim0_changed(self):
        currText = self.dim0_dim_edit.currentText()
        self.dim1_dim_edit.clear()
        if currText == self.r_l_text:
            self.dim1_dim_edit.addItems([self.u_d_text, self.b_f_text])
        elif currText == self.u_d_text:
            self.dim1_dim_edit.addItems([self.r_l_text, self.b_f_text])
        else:
            self.dim1_dim_edit.addItems([self.r_l_text, self.u_d_text])

        self.dim1_changed()

    def dim1_changed(self):
        currdim0Text = self.dim0_dim_edit.currentText()
        currdim1Text = self.dim1_dim_edit.currentText()
        self.dim2_dim_edit.clear()
        if currdim0Text == self.r_l_text:
            if currdim1Text == self.u_d_text:
                self.dim2_dim_edit.addItem(self.b_f_text)
            else:
                self.dim2_dim_edit.addItem(self.u_d_text)
        elif currdim0Text == self.u_d_text:
            if currdim1Text == self.r_l_text:
                self.dim2_dim_edit.addItem(self.b_f_text)
            else:
                self.dim2_dim_edit.addItem(self.r_l_text)
        else:
            if currdim1Text == self.r_l_text:
                self.dim2_dim_edit.addItem(self.u_d_text)
            else:
                self.dim2_dim_edit.addItem(self.r_l_text)

    def OK_pressed(self):

        self.parDict['dimensions'] = [self.dim0_dim_edit.currentText(),
                                        self.dim1_dim_edit.currentText(),
                                        self.dim2_dim_edit.currentText(),
                                        self.dim3_dim_label.text()]

        self.parDict['directions'] = [self.dim0_dir_edit.currentText(),
                                        self.dim1_dir_edit.currentText(),
                                        self.dim2_dir_edit.currentText(),
                                        self.p_text]

        self.parDict['steps'] = [self.dim0_size_edit.text(),
                                self.dim1_size_edit.text(),
                                self.dim2_size_edit.text(),
                                self.dim3_size_edit.text()]

        self.parDict['step_sizes'] = [self.dim0_step_size_edit.text(),
                                self.dim1_step_size_edit.text(),
                                self.dim2_step_size_edit.text(),
                                self.dim3_step_size_edit.text()]

        self.parDict['unidirectional'] = self.unidir_check.isChecked()

        self.close()

