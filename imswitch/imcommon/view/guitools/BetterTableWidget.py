from typing import Union, List
from qtpy.QtWidgets import (
    QTableWidget,
    QHeaderView,
    QAbstractItemView,
    QTableWidgetItem,
    QTableView,
    QSpinBox,
    QDoubleSpinBox
)
from qtpy.QtCore import Qt, QModelIndex
from qtpy.QtGui import QDropEvent

# implementation adapted from
# https://stackoverflow.com/questions/26227885/drag-and-drop-rows-within-qtablewidget#26311179
class BetterTableWidget(QTableWidget):
    """ A table widget that allows for drag and drop reordering of rows. 
    It also provides methods to add new rows and remove a selected row, and reimplements
    key press and mouse press events to clear row selection when pressing escape or clicking on an empty area.
    """
    
    def __init__(self, 
                names: list, 
                default: Union[str, int, float],
                initData: List[dict] = None,
                unit: str = None,
                labelName: str = None
            ):
        super(QTableWidget, self).__init__()
        self.default = default
        self.labelName = labelName
        
        if unit is not None: 
            columns = [f"{name} ({unit})" for name in names]
        else:
            columns = names
        
        if self.labelName is not None:
            columns.append("Label")
        
        self.setColumnCount(len(columns))  # Number of columns.
        self.setRowCount(0)  # Number of rows.
        self.setHorizontalHeaderLabels(columns)  # Set labels for columns.
        
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDragDropOverwriteMode(False)
        self.setDropIndicatorShown(True)
        
        sanityCheck = True
        numColumns = self.columnCount()
        if initData is not None:
            for data in initData:
                if len(data) != numColumns:
                    sanityCheck = False
                    break
        else:
            sanityCheck = False
        
        if sanityCheck:
            for data in initData:
                self.addNewRow(data)
        else:
            self.addNewRow()  # Add the first row.
        
        for col in range(numColumns):
            self.setColumnWidth(col, self.width() // numColumns)
        
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
    
    def dropEvent(self, event: QDropEvent):
        """ Monitors a drag and drop event, and reorders rows accordingly.
        Method is reimplemented as a workaround for a bug in the QTableWidget.
        """
        if event.source() == self and (event.dropAction() == Qt.MoveAction or self.dragDropMode() == QAbstractItemView.InternalMove):
            success, row, _, _ = self.__dropOn(event)
            if success:             
                selRows = self.__getSelectedRowsFast()                        

                top = selRows[0]
                dropRow = row
                if dropRow == -1:
                    dropRow = self.rowCount()
                offset = dropRow - top

                for i, row in enumerate(selRows):
                    r = row + offset
                    if r > self.rowCount() or r < 0:
                        r = 0
                    self.insertRow(r)

                selRows = self.__getSelectedRowsFast()

                top = selRows[0]
                offset = dropRow - top
                for i, row in enumerate(selRows):
                    r = row + offset
                    if r > self.rowCount() or r < 0:
                        r = 0

                    for j in range(self.columnCount()):
                        source = QTableWidgetItem(self.item(row, j))
                        self.setItem(r, j, source)
                event.accept()
        else:
            QTableView.dropEvent(event)
    
    def __getSelectedRowsFast(self):
        selRows = []
        for item in self.selectedItems():
            if item.row() not in selRows:
                selRows.append(item.row())
        return selRows

    def __droppingOnItself(self, event, index):
        dropAction = event.dropAction()

        if self.dragDropMode() == QAbstractItemView.InternalMove:
            dropAction = Qt.MoveAction

        if event.source() == self and event.possibleActions() & Qt.MoveAction and dropAction == Qt.MoveAction:
            selectedIndexes = self.selectedIndexes()
            child = index
            while child.isValid() and child != self.rootIndex():
                if child in selectedIndexes:
                    return True
                child = child.parent()

        return False

    def __dropOn(self, event: QDropEvent):
        if event.isAccepted():
            return False, None, None, None

        index = QModelIndex()
        row = -1
        col = -1

        if self.viewport().rect().contains(event.pos()):
            index = self.indexAt(event.pos())
            if not index.isValid() or not self.visualRect(index).contains(event.pos()):
                index = self.rootIndex()

        if self.model().supportedDropActions() & event.dropAction():
            if index != self.rootIndex():
                dropIndicatorPosition = self.__position(event.pos(), self.visualRect(index), index)

                if dropIndicatorPosition == QAbstractItemView.AboveItem:
                    row = index.row()
                    col = index.column()
                elif dropIndicatorPosition == QAbstractItemView.BelowItem:
                    row = index.row() + 1
                    col = index.column()
                else:
                    row = index.row()
                    col = index.column()

            if not self.__droppingOnItself(event, index):
                return True, row, col, index

        return False, None, None, None

    def __position(self, pos, rect, index):
        r = QAbstractItemView.OnViewport
        margin = 2
        if pos.y() - rect.top() < margin:
            r = QAbstractItemView.AboveItem
        elif rect.bottom() - pos.y() < margin:
            r = QAbstractItemView.BelowItem 
        elif rect.contains(pos, True):
            r = QAbstractItemView.OnItem

        if r == QAbstractItemView.OnItem and not (self.model().flags(index) & Qt.ItemIsDropEnabled):
            r = QAbstractItemView.AboveItem if pos.y() < rect.center().y() else QAbstractItemView.BelowItem

        return r
    
    def addNewRow(self, data: list = None):
        """ Add new row to the table. Automatically adds a label to the last column if labelName is not `None`.
        Data type of the row is determined by the default value of the table, which is set as the default
        value of the row. If `data` is provided, it is used instead of the default value.
        """
        rowNumber = self.rowCount()  # Get row number.
        self.insertRow(rowNumber)  # Insert a row.
        
        if data is not None:
            if self.labelName is not None:
                newRowItem = [self.default for _ in range(self.columnCount()-1)]
                newRowItem.append(f"{self.labelName} {rowNumber}")
            else:
                newRowItem = [self.default for _ in range(self.columnCount())]
        else:
            if self.labelName is not None:
                newRowItem = [self.default for _ in range(self.columnCount()-1)]
                newRowItem.append(f"{self.labelName} {rowNumber}")
            else:
                newRowItem = [self.default for _ in range(self.columnCount())]
        
        for col, item in zip(range(self.columnCount()), newRowItem):
            if type(item) == int:
                self.setCellWidget(rowNumber, col, QSpinBox(self))
                self.cellWidget(rowNumber, col).setAlignment(Qt.AlignCenter)
            elif type(item) == float:
                self.setCellWidget(rowNumber, col, QDoubleSpinBox(self))
                self.cellWidget(rowNumber, col).setAlignment(Qt.AlignCenter)
            else:
                self.setItem(rowNumber, col, QTableWidgetItem(str(item)))  
                self.item(rowNumber, col).setTextAlignment(Qt.AlignCenter)          

    def removeSelectedRow(self):
        """ Remove currently selected row from the table. Automatically clears selection.
        """
        self.removeRow(self.currentRow())  # Remove a row.
        self.clearSelection()
    
    def keyPressEvent(self, event):
        """ Override key press event to clear row selection when pressing escape.
        """
        if (event.key() == Qt.Key_Escape and
            event.modifiers() == Qt.NoModifier):
            self.selectionModel().clear()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """ Override mouse press event to clear row selection when clicking outside of a row.
        """
        if not self.indexAt(event.pos()).isValid():
            self.selectionModel().clear()
        super().mousePressEvent(event)