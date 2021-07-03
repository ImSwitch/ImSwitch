from qtpy import QtCore, QtWidgets


class ModuleLoadErrorView(QtWidgets.QMainWindow):
    """ Widget that explains that a module failed to load. """

    def __init__(self, error, *args, **kwargs):
        super().__init__(*args, **kwargs)

        headerLabel = QtWidgets.QLabel('<h1>Failed to load module</h1>')
        headerLabel.setAlignment(QtCore.Qt.AlignCenter)

        errorMessage = QtWidgets.QTextEdit(f'{type(error).__name__}: {error}')
        errorMessage.setAlignment(QtCore.Qt.AlignCenter)
        errorMessage.setStyleSheet('font-size: 14pt')
        errorMessage.setReadOnly(True)

        layout = QtWidgets.QVBoxLayout()
        layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
            )
        )
        layout.setAlignment(QtCore.Qt.AlignCenter)
        layout.setSpacing(32)
        layout.setContentsMargins(64, 64, 64, 64)
        layout.addWidget(headerLabel)
        layout.addWidget(errorMessage)
        layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
            )
        )

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)


# Copyright (C) 2020, 2021 TestaLab
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
