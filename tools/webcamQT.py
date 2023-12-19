import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor

class ImageLabel(QLabel):
    doubleClicked = pyqtSignal()
    dragPosition = pyqtSignal(QPoint, QPoint)

    def __init__(self):
        super().__init__()
        self.originalPixmap = None
        self.dragStartPos = None
        self.currentRect = None
        self.doubleClickPos = None

    def setOriginalPixmap(self, pixmap):
        self.originalPixmap = pixmap
        self.setPixmap(pixmap)

    def mouseDoubleClickEvent(self, event):
        self.currentRect = None
        self.doubleClickPos = event.pos()
        self.doubleClicked.emit()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragStartPos = event.pos()

    def mouseMoveEvent(self, event):
        if not self.dragStartPos:
            return
        self.currentRect = QRect(self.dragStartPos, event.pos())
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.dragStartPos:
            self.dragPosition.emit(self.dragStartPos, event.pos())
            self.dragStartPos = None

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self.currentRect:
            return
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.originalPixmap)
        pen = QPen(QColor(255, 0, 0), 2)
        painter.setPen(pen)
        painter.drawRect(self.currentRect)

class WebcamViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.imageLabel = ImageLabel()
        self.layout.addWidget(self.imageLabel)
        self.setLayout(self.layout)

        # Setup the webcam feed
        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateFrame)
        self.timer.start(30)

        # Connect signals
        self.imageLabel.doubleClicked.connect(self.onDoubleClick)
        self.imageLabel.dragPosition.connect(self.onDragPosition)

    def updateFrame(self):
        ret, frame = self.capture.read()
        if ret:
            image = QImage(frame, frame.shape[1], frame.shape[0], 
                           frame.strides[0], QImage.Format_BGR888)
            pixmap = QPixmap.fromImage(image)
            self.imageLabel.setOriginalPixmap(pixmap)

    def onDoubleClick(self):
        print("Double Clicked")
        # return the clicked mouse image coordinates 
        return self.imageLabel.doubleClickPos.getCoords()
        
        
    def onDragPosition(self, start, end):
        print(f"Dragged from {start} to {end}")
        # Convert to image coordinates and handle the event
        return self.imageLabel.currentRect.getCoords()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WebcamViewer()
    ex.show()
    sys.exit(app.exec_())
