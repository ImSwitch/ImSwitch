from qtpy import QtCore, QtGui, QtWidgets


class CheckableComboBox(QtWidgets.QComboBox):
    """ A QComboBox with items that are either checked or unchecked. Displays
    text like "2 items checked" in the main box. """

    sigCheckedChanged = QtCore.Signal(object, bool)  # (itemId, checked)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.itemTypeNameSingular = 'item'
        self.itemTypeNamePlural = 'items'

        model = QtGui.QStandardItemModel(0, 1)
        model.dataChanged.connect(self.dataChanged)
        self.setModel(model)

    def addItem(self, text, itemId):
        """ Adds an item to the list. itemId should be unique. """
        item = QtGui.QStandardItem(text)
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        item.setData(QtCore.Qt.Checked, QtCore.Qt.CheckStateRole)
        item.setData(itemId, QtCore.Qt.UserRole)
        self.model().appendRow(item)

    def getCheckedItems(self):
        """ Returns the IDs of the checked items. """
        itemIds = []
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
                itemIds.append(item.data(QtCore.Qt.UserRole))
        return itemIds

    def getNumChecked(self):
        """ Returns the number of checked items. """
        numChecked = 0
        for row in range(self.model().rowCount()):
            item = self.model().item(row)
            if item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked:
                numChecked += 1
        return numChecked

    def setItemTypeName(self, singular, plural):
        self.itemTypeNameSingular = singular
        self.itemTypeNamePlural = plural

    def dataChanged(self, modelIndex, _, roles):
        self.repaint()  # Must be done to update the text

        if QtCore.Qt.CheckStateRole in roles:
            item = self.model().item(modelIndex.row())
            data = item.data(QtCore.Qt.UserRole)
            checked = item.data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked
            self.sigCheckedChanged.emit(data, checked)

    def paintEvent(self, event):
        numChecked = self.getNumChecked()
        itemTypeName = self.itemTypeNameSingular if numChecked == 1 else self.itemTypeNamePlural

        opt = QtWidgets.QStyleOptionComboBox()
        self.initStyleOption(opt)
        opt.currentText = f'{numChecked} {itemTypeName} selected'

        painter = QtWidgets.QStylePainter(self)
        painter.setPen(self.palette().color(QtGui.QPalette.Text))
        painter.drawComplexControl(QtWidgets.QStyle.CC_ComboBox, opt)
        painter.drawControl(QtWidgets.QStyle.CE_ComboBoxLabel, opt)
