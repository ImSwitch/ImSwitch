import os
import qdarkstyle


def getBaseStyleSheet():
    baseStyleSheet = qdarkstyle.load_stylesheet(qt_api=os.environ.get('PYQTGRAPH_QT_LIB'))
    baseStyleSheet += '''
        QWidget:disabled {
            color: #54687A;
        }

        QComboBox {
            padding-right: 4px;
            min-width: 40px;
        }
        
        QPushButton {
            min-width: 20px;
        }
        
        QPushButton:disabled {
            color: #788D9C;
        }
        
        QPushButton:checked {
            background-color: #2B333D;
            border: 2px solid #1464A0;
        }
        
        QPushButton:pressed {
            background-color: #262E38;
        }
        
        QScrollArea QWidget QPushButton:disabled {
            background-color: #455364;
        }
        
        QSplitter {
            background-color: #37414F;
        }

        QLabel {
            background-color: transparent;
        }
            
        DockLabel {
            padding: 0;
        }
        
        ParameterTree QTreeView::item, ParameterTree QAbstractSpinBox, ParameterTree QComboBox {
            padding-top: 0;
            padding-bottom: 0;
            margin-top: 0;
            margin-bottom: 0;
            border: none;
        }
        
        ParameterTree QComboBox QAbstractItemView {
            min-width: 128px;
        }
    '''
    return baseStyleSheet


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
