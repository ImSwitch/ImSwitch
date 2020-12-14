import os
import qdarkstyle


def getBaseStyleSheet():
    baseStyleSheet = qdarkstyle.load_stylesheet(qt_api=os.environ.get('PYQTGRAPH_QT_LIB'))
    baseStyleSheet += '''
        QComboBox {
            padding-right: 4px;
            min-width: 40px;
        }
        
        QPushButton {
            min-width: 20px;
        }
        
        QPushButton:checked {
            background-color: #29353D;
            border: 2px solid #1464A0;
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
