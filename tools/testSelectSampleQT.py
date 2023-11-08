from PyQt5 import QtCore, QtGui, QtWidgets


class GraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        scene = QtWidgets.QGraphicsScene(self)
        self.setScene(scene)

        self._pixmap_item = QtWidgets.QGraphicsPixmapItem()
        scene.addItem(self.pixmap_item)

        self.selection_rect = None
        self.start_point = None

    @property
    def pixmap_item(self):
        return self._pixmap_item

    def setPixmap(self, pixmap):
        self.pixmap_item.setPixmap(pixmap)

    def resizeEvent(self, event):
        self.fitInView(self.pixmap_item, QtCore.Qt.KeepAspectRatio)
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        sp = self.mapToScene(event.pos())
        lp = self.pixmap_item.mapFromScene(sp).toPoint()

        if event.button() == QtCore.Qt.LeftButton:
            self.start_point = lp
            if self.selection_rect:
                self.scene().removeItem(self.selection_rect)
            self.selection_rect = QtWidgets.QGraphicsRectItem(QtCore.QRectF(self.start_point, lp))
            self.selection_rect.setPen(QtGui.QPen(QtGui.QColor(255, 0, 0)))
            self.scene().addItem(self.selection_rect)

    def mouseMoveEvent(self, event):
        if self.start_point:
            sp = self.mapToScene(event.pos())
            lp = self.pixmap_item.mapFromScene(sp).toPoint()
            rect = QtCore.QRectF(self.start_point, lp)
            self.selection_rect.setRect(rect.normalized())

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.start_point:
            self.start_point = None
            # Calculate the selected coordinates here based on self.selection_rect.rect()
            selected_rect = self.selection_rect.rect()
            left = selected_rect.left()
            top = selected_rect.top()
            right = selected_rect.right()
            bottom = selected_rect.bottom()
            print("Selected coordinates:", left, top, right, bottom)


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    w = GraphicsView()
    w.setPixmap(QtGui.QPixmap("imswitch/_data/images/WellplateAdapter3Slides.png"))
    w.showMaximized()
    sys.exit(app.exec_())
