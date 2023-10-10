import sys
import math

from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtCore import Qt
from qtpy import QtCore

class Joystick(QWidget):
    floatValueChanged = QtCore.Signal(float)
    ''' based on https://github.com/bsiyoung/PyQt5-Joystick/ '''

    def __init__(self, window_min_size = [200, 200], callbackFct=None):
        super().__init__()

        self.window_title = 'Joystick'
        self.window_min_size = window_min_size 
        self.wnd_fit_size = 400
        self.window_size = [self.wnd_fit_size, self.wnd_fit_size]

        self.circle_margin_ratio = 0.1
        self.circle_diameter = int(self.window_size[0] * (1 - self.circle_margin_ratio * 2))

        self.stick_diameter_ratio = 0.1
        self.stick_diameter = int(self.circle_diameter * self.stick_diameter_ratio)
        self.is_mouse_down = False
        self.stick_pos = [0, 0]
        self.strength = 0

        self.stat_label_margin = 10
        self.stat_label = QLabel(self)
        
        self.callbackFct = callbackFct
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(self.window_title)

        self.setMinimumSize(self.window_min_size[0], self.window_min_size[1])
        self.resize(self.window_size[0], self.window_size[1])

        self.stat_label.setAlignment(Qt.AlignLeft)
        self.stat_label.setGeometry(self.stat_label_margin, self.stat_label_margin,
                                    self.window_min_size[0] - self.stat_label_margin * 2,
                                    self.window_min_size[0] - self.stat_label_margin * 2)
        font = self.stat_label.font()
        font.setPointSize(10)

        self.setMouseTracking(True)

        self.show()

    def resizeEvent(self, event):
        self.wnd_fit_size = min(self.width(), self.height())

        self.circle_diameter = int(self.wnd_fit_size * (1 - self.circle_margin_ratio * 2))
        self.stick_diameter = int(self.circle_diameter * self.stick_diameter_ratio)

    def _draw_outer_circle(self, painter):
        painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))

        circle_margin = int(self.wnd_fit_size * self.circle_margin_ratio)
        painter.drawEllipse(circle_margin, circle_margin,
                            self.circle_diameter, self.circle_diameter)

    def _draw_sub_lines(self, painter):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(Qt.lightGray, 1, Qt.DashLine))

        num_sub_line = 6
        for i in range(num_sub_line):
            theta = math.pi / 2 - math.pi * i / num_sub_line
            x0 = int(self.wnd_fit_size / 2 - self.circle_diameter / 2 * math.cos(theta))
            y0 = int(self.wnd_fit_size / 2 - self.circle_diameter / 2 * math.sin(theta))
            x1 = int(self.wnd_fit_size / 2 - self.circle_diameter / 2 * math.cos(theta + math.pi))
            y1 = int(self.wnd_fit_size / 2 - self.circle_diameter / 2 * math.sin(theta + math.pi))
            painter.drawLine(x0, y0, x1, y1)

    def _draw_sub_circles(self, painter):
        painter.setPen(QPen(Qt.lightGray, 1, Qt.DashLine))

        num_sub_circle = 4
        for i in range(num_sub_circle):
            sub_radius = int(self.circle_diameter / 2 * (i + 1) / (num_sub_circle + 1))
            sub_margin = int(self.wnd_fit_size / 2 - sub_radius)
            painter.drawEllipse(sub_margin, sub_margin, sub_radius * 2, sub_radius * 2)

        # Draw Inner(Joystick) Circle
        painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
        stick_margin = [int(self.wnd_fit_size / 2 + self.stick_pos[0] - self.stick_diameter / 2),
                        int(self.wnd_fit_size / 2 - self.stick_pos[1] - self.stick_diameter / 2)]
        painter.drawEllipse(stick_margin[0], stick_margin[1], self.stick_diameter, self.stick_diameter)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Draw Outer(Main) Circle
        self._draw_outer_circle(painter)

        # Draw Sub Lines
        self._draw_sub_lines(painter)

        # Draw Sub Circles
        self._draw_sub_circles(painter)

        # Change Status Label Text (Angle In Degree)
        strength = self.get_strength()
        angle = self.get_angle(in_deg=True)
        if angle < 0:
            angle += 360
        #self.stat_label.setText('Strength : {:.2f} \nDirection : {:.2f}°'.format(strength, angle))

    def mouseMoveEvent(self, event):
        # Move Stick Only When Mouse Left Button Pressed
        if self.is_mouse_down is False:
            return

        # Window Coordinate To Cartesian Coordinate
        pos = event.pos()
        stick_pos_buf = [pos.x() - self.wnd_fit_size / 2, self.wnd_fit_size / 2 - pos.y()]

        # If Cursor Is Not In Available Range, Correct It
        if self._get_strength(stick_pos_buf) > 1.0:
            theta = math.atan2(stick_pos_buf[1], stick_pos_buf[0])
            radius = (self.circle_diameter - self.stick_diameter) / 2
            stick_pos_buf[0] = radius * math.cos(theta)
            stick_pos_buf[1] = radius * math.sin(theta)
        
        # Emit signal #TODO: Not sure if this is the right way to do it
        if self.callbackFct is not None:
            self.callbackFct(stick_pos_buf[0], stick_pos_buf[1])

        self.stick_pos = stick_pos_buf
        self.repaint()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_mouse_down = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_mouse_down = False
            self.stick_pos = [0, 0]
            self.repaint()
            if self.callbackFct is not None:
                self.callbackFct(0,0)


    # Get Strength With Argument
    def _get_strength(self, stick_pos):
        max_distance = (self.circle_diameter - self.stick_diameter) / 2
        distance = math.sqrt(stick_pos[0] * stick_pos[0] + stick_pos[1] * stick_pos[1])

        return distance / max_distance

    # Get Strength With Current Stick Position
    def get_strength(self):
        max_distance = (self.circle_diameter - self.stick_diameter) / 2
        distance = math.sqrt(self.stick_pos[0] * self.stick_pos[0] + self.stick_pos[1] * self.stick_pos[1])
        
        return distance / max_distance

    def get_angle(self, in_deg=False):
        angle = math.atan2(self.stick_pos[1], self.stick_pos[0])
        if in_deg is True:
            angle = angle * 180 / math.pi

        return angle