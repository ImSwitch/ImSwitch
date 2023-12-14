from PyQt5 import QtWidgets, QtCore

class YourWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        nLedsX = 8
        nLedsY = 8
        self.grid = QtWidgets.QGridLayout()
        self.setLayout(self.grid)
        
        self.createConcentricRings(nLedsX, nLedsY)
        self.createButtons(nLedsX)
        self.createSlider()

        self.setMaximumSize(500, 500)

    def createConcentricRings(self, nLedsX, nLedsY):
        # Create dictionary to hold buttons
        self.leds = {}
        # Create grid layout for leds (buttons)
        gridLayout = self.grid

        # Calculate the number of LEDs in each ring
        ring1_leds = 1
        ring2_leds = 8
        ring3_leds = 15

        # Create LEDs and add them to the grid layout
        for ix in range(nLedsX):
            for iy in range(nLedsY):
                distance = max(abs(ix - nLedsX // 2), abs(iy - nLedsY // 2))
                if distance == 0:
                    ring = 1
                elif distance <= 2:
                    ring = 2
                else:
                    ring = 3

                corrds = str(nLedsX * iy + ix)
                self.leds[corrds] = QtWidgets.QPushButton(corrds)
                self.leds[corrds].setSizePolicy(
                    QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
                )
                self.leds[corrds].setCheckable(True)
                self.leds[corrds].setStyleSheet(
                    """background-color: grey; font-size: 15px"""
                )
                self.leds[corrds].setMaximumSize(25, 25)
                # Add button/label to layout
                gridLayout.addWidget(self.leds[corrds], iy, ix)

        # Store the LEDs for each ring
        self.ring_leds = {1: [], 2: [], 3: []}
        for corrds, button in self.leds.items():
            distance = max(
                abs(button.pos().x() - nLedsX // 2), abs(button.pos().y() - nLedsY // 2)
            )
            self.ring_leds[1 if distance == 0 else (2 if distance <= 2 else 3)].append(
                button
            )

    def createButtons(self, nLedsX):
        self.ButtonAllOn = QtWidgets.QPushButton("All On")
        self.ButtonAllOn.setMaximumSize(25, 50)
        self.ButtonAllOn.clicked.connect(self.turnOnAll)
        self.grid.addWidget(self.ButtonAllOn, 0, nLedsX)

        self.ButtonAllOff = QtWidgets.QPushButton("All Off")
        self.ButtonAllOff.setMaximumSize(25, 50)
        self.ButtonAllOff.clicked.connect(self.turnOffAll)
        self.grid.addWidget(self.ButtonAllOff, 1, nLedsX)

        self.ButtonSubmit = QtWidgets.QPushButton("Submit")
        self.ButtonSubmit.setMaximumSize(25, 50)
        self.grid.addWidget(self.ButtonSubmit, 2, nLedsX)

        self.ButtonToggle = QtWidgets.QPushButton("Toggle")
        self.ButtonToggle.setMaximumSize(25, 50)
        self.grid.addWidget(self.ButtonToggle, 3, nLedsX)

    def createSlider(self):
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.setMinimum(0)
        self.slider.setMaximum(255)
        self.slider.setTickInterval(5)
        self.slider.setSingleStep(5)
        self.slider.setValue(255)
        self.grid.addWidget(self.slider, 9, 0, 1, 4)

    def turnOnAll(self):
        for button in self.leds.values():
            button.setChecked(True)

    def turnOffAll(self):
        for button in self.leds.values():
            button.setChecked(False)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    widget = YourWidget()
    widget.show()
    sys.exit(app.exec_())
