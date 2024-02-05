from abc import abstractmethod

import napari
import numpy as np
from napari.utils.translations import trans
from qtpy import QtCore, QtGui, QtWidgets
from vispy.color import Color
from vispy.scene.visuals import Compound, Line, Markers
from vispy.visuals.transforms import STTransform

from .imagetools import minmaxLevels


def addNapariGrayclipColormap():
    if hasattr(napari.utils.colormaps.AVAILABLE_COLORMAPS, 'grayclip'):
        return

    grayclip = []
    for i in range(255):
        grayclip.append([i / 255, i / 255, i / 255])
    grayclip.append([1, 0, 0])
    napari.utils.colormaps.AVAILABLE_COLORMAPS['grayclip'] = napari.utils.Colormap(
        name='grayclip', colors=grayclip
    )


class EmbeddedNapari(napari.Viewer):
    """ Napari viewer to be embedded in non-napari windows. Also includes a
    feature to protect certain layers from being removed when added using
    the add_image method. """

    def __init__(self, *args, show=False, **kwargs):
        super().__init__(*args, show=show, **kwargs)

        # Monkeypatch layer removal methods
        oldDelitemIndices = self.layers._delitem_indices

        def newDelitemIndices(key):
            indices = oldDelitemIndices(key)
            for index in indices[:]:
                layer = index[0][index[1]]
                if hasattr(layer, 'protected') and layer.protected:
                    indices.remove(index)
            return indices

        self.layers._delitem_indices = newDelitemIndices

        # Make menu bar not native
        self.window._qt_window.menuBar().setNativeMenuBar(False)

        # Remove unwanted menu bar items
        menuChildren = self.window._qt_window.findChildren(QtWidgets.QAction)
        for menuChild in menuChildren:
            try:
                if menuChild.text() in [trans._('Close Window'), trans._('Exit')]:
                    self.window.file_menu.removeAction(menuChild)
            except Exception:
                pass
        
        self.scale_bar.visible = True

    def add_image(self, *args, protected=False, **kwargs):
        result = super().add_image(*args, **kwargs)

        if isinstance(result, list):
            for layer in result:
                layer.protected = protected
        else:
            result.protected = protected

        return result

    def get_widget(self):
        return self.window._qt_window


class NapariBaseWidget(QtWidgets.QWidget):
    """ Base class for Napari widgets. """

    @property
    @abstractmethod
    def name(self):
        pass

    def __init__(self, napariViewer):
        super().__init__()
        self.viewer = napariViewer

    @classmethod
    def addToViewer(cls, napariViewer, position='left'):
        """ Adds this widget to the specified Napari viewer. """

        # Add dock for this widget
        widget = cls(napariViewer)
        napariViewer.window.add_dock_widget(widget, name=widget.name, area=position)

        # Move layer list to bottom
        napariViewer.window._qt_window.removeDockWidget(
            napariViewer.window.qt_viewer.dockLayerList
        )
        napariViewer.window._qt_window.addDockWidget(
            napariViewer.window.qt_viewer.dockLayerList.qt_area,
            napariViewer.window.qt_viewer.dockLayerList
        )
        napariViewer.window.qt_viewer.dockLayerList.show()
        return widget

    def addItemToViewer(self, item):
        item.attach(self.viewer,
                    canvas=self.viewer.window.qt_viewer.canvas,
                    view=self.viewer.window.qt_viewer.view,
                    parent=self.viewer.window.qt_viewer.view.scene,
                    order=1e6 + 8000)


class NapariUpdateLevelsWidget(NapariBaseWidget):
    """ Napari widget for auto-levelling the currently selected layer with a
    single click. """

    @property
    def name(self):
        return 'update levels widget'

    def __init__(self, napariViewer):
        super().__init__(napariViewer)

        # Update levels button
        self.updateLevelsButton = QtWidgets.QPushButton('Update levels')
        self.updateLevelsButton.clicked.connect(self._on_update_levels)

        # Layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.updateLevelsButton)

        # Make sure widget isn't too big
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                                 QtWidgets.QSizePolicy.Maximum))

    def _on_update_levels(self):
        for layer in self.viewer.layers:
            layer.contrast_limits = minmaxLevels(layer.data)


class NapariResetViewWidget(NapariBaseWidget):
    """ Napari widget for resetting the dimensional view of the currently
    selected layer with a single click. """

    @property
    def name(self):
        return 'reset view widget'

    def __init__(self, napariViewer):
        super().__init__(napariViewer)

        # Reset buttons and line edit
        self.resetViewButton = QtWidgets.QPushButton('Reset view')
        self.resetViewButton.clicked.connect(self._on_reset_view)
        self.resetOrderButton = QtWidgets.QPushButton('Reset axis order')
        self.resetOrderButton.clicked.connect(self._on_reset_axis_order)
        self.setOrderButton = QtWidgets.QPushButton('Set axis order')
        self.setOrderButton.clicked.connect(self._on_set_axis_order)
        self.setOrderLineEdit = QtWidgets.QLineEdit('0,1')

        # Layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.resetViewButton)
        self.layout().addWidget(self.resetOrderButton)
        self.layout().addWidget(self.setOrderLineEdit)
        self.layout().addWidget(self.setOrderButton)

        # Make sure widget isn't too big
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                                 QtWidgets.QSizePolicy.Maximum))

    def _on_reset_view(self):
        self.viewer.reset_view()

    def _on_reset_axis_order(self):
        order_curr = self.viewer.dims.order
        self.viewer.dims.order = tuple(sorted(order_curr))
        step_curr = self.viewer.dims.current_step
        step_curr = [0 for _ in step_curr]
        self.viewer.dims.current_step = tuple(step_curr)

    def _on_set_axis_order(self):
        order_new = [int(c) for c in self.setOrderLineEdit.text().split(',')]
        self.viewer.dims.order = tuple(order_new)


class NapariShiftWidget(NapariBaseWidget):
    """ Napari widget for shifting the currently selected layer by a
    user-defined number of pixels. """

    @property
    def name(self):
        return 'image shift controls'

    def __init__(self, napariViewer):
        super().__init__(napariViewer)

        # Title label
        self.titleLabel = QtWidgets.QLabel('<h3>Image shift controls</h3>')

        # Shift up button
        self.upButton = QtWidgets.QPushButton()
        self.upButton.setToolTip('Shift selected layer up')
        self.upButton.setIcon(QtGui.QIcon(f':/themes/{self.viewer.theme}/up_arrow.svg'))
        self.upButton.clicked.connect(self._on_up)

        # Shift right button
        self.rightButton = QtWidgets.QPushButton()
        self.rightButton.setToolTip('Shift selected layer right')
        self.rightButton.setIcon(QtGui.QIcon(f':/themes/{self.viewer.theme}/right_arrow.svg'))
        self.rightButton.clicked.connect(self._on_right)

        # Shift down button
        self.downButton = QtWidgets.QPushButton()
        self.downButton.setToolTip('Shift selected layer down')
        self.downButton.setIcon(QtGui.QIcon(f':/themes/{self.viewer.theme}/down_arrow.svg'))
        self.downButton.clicked.connect(self._on_down)

        # Shift left button
        self.leftButton = QtWidgets.QPushButton()
        self.leftButton.setToolTip('Shift selected layer left')
        self.leftButton.setIcon(QtGui.QIcon(f':/themes/{self.viewer.theme}/left_arrow.svg'))
        self.leftButton.clicked.connect(self._on_left)

        # Reset button
        self.resetButton = QtWidgets.QPushButton('Reset')
        self.resetButton.clicked.connect(self._on_reset)

        # Shift distance field
        self.shiftDistanceLabel = QtWidgets.QLabel('Shift distance:')
        self.shiftDistanceInput = QtWidgets.QSpinBox()
        self.shiftDistanceInput.setMinimum(1)
        self.shiftDistanceInput.setMaximum(9999)
        self.shiftDistanceInput.setValue(1)
        self.shiftDistanceInput.setSuffix(' px')

        # Layout
        self.buttonGrid = QtWidgets.QGridLayout()
        self.buttonGrid.setSpacing(6)
        self.buttonGrid.addWidget(self.upButton, 0, 1)
        self.buttonGrid.addWidget(self.rightButton, 1, 2)
        self.buttonGrid.addWidget(self.downButton, 2, 1)
        self.buttonGrid.addWidget(self.leftButton, 1, 0)
        self.buttonGrid.addWidget(self.resetButton, 1, 1)

        self.shiftDistanceLayout = QtWidgets.QHBoxLayout()
        self.shiftDistanceLayout.setSpacing(12)
        self.shiftDistanceLayout.addWidget(self.shiftDistanceLabel)
        self.shiftDistanceLayout.addWidget(self.shiftDistanceInput, 1)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setSpacing(24)
        self.layout().addWidget(self.titleLabel)
        self.layout().addLayout(self.buttonGrid)
        self.layout().addLayout(self.shiftDistanceLayout)

        # Make sure widget isn't too big
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                                 QtWidgets.QSizePolicy.Maximum))

    def _on_up(self):
        self._do_shift(0, -self._get_shift_distance())

    def _on_right(self):
        self._do_shift(self._get_shift_distance(), 0)

    def _on_down(self):
        self._do_shift(0, self._get_shift_distance())

    def _on_left(self):
        self._do_shift(-self._get_shift_distance(), 0)

    def _on_reset(self):
        for layer in self.viewer.layers.selected:
            layer.translate = [0, 0]

    def _do_shift(self, xDist, yDist):
        for layer in self.viewer.layers.selected:
            y, x = layer.translate
            layer.translate = [y + yDist, x + xDist]

    def _get_shift_distance(self):
        return self.shiftDistanceInput.value()


class VispyBaseVisual(QtCore.QObject):
    def __init__(self):
        super().__init__()
        self._viewer = None
        self._view = None
        self._canvas = None
        self._nodes = []
        self._visible = True
        self._attached = False

    def attach(self, viewer, view, canvas, parent=None, order=0):
        self._viewer = viewer
        self._view = view
        self._canvas = canvas
        self._attached = True

    def detach(self):
        for node in self._nodes:
            node.parent = None

        self._viewer = None
        self._view = None
        self._canvas = None
        self._attached = False

    def setVisible(self, value):
        for node in self._nodes:
            node.visible = value

        self._visible = value

    def show(self):
        self.setVisible(True)

    def hide(self):
        self.setVisible(False)

    def _get_center_line_p1(self, pos, line_length, vertical):
        if vertical:
            return [pos[0], pos[1] - line_length / 2, 0]
        else:
            return [pos[0] - line_length / 2, pos[1], 0]

    def _get_center_line_p2(self, pos, line_length, vertical):
        if vertical:
            return [pos[0], pos[1] + line_length / 2, 0]
        else:
            return [pos[0] + line_length / 2, pos[1], 0]


class VispyROIVisual(VispyBaseVisual):
    sigROIChanged = QtCore.Signal(object, object)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = np.array(value, dtype=int)
        self._update_position()
        self.sigROIChanged.emit(self.position, self.size)

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = np.array(value, dtype=int)
        self._update_size()
        self.sigROIChanged.emit(self.position, self.size)

    @property
    def bounds(self):
        pos = self.position
        size = self.size
        x0 = int(pos[0])
        y0 = int(pos[1])
        x1 = int(x0 + size[0])
        y1 = int(y0 + size[1])
        return x0, y0, x1, y1

    def __init__(self, rect_color='yellow', handle_color='orange'):
        super().__init__()
        self._drag_mode = None
        self._world_scale = 1

        self._position = [0, 0]
        self._size = [64, 64]

        self._rect_color = Color(rect_color)
        self._handle_color = Color(handle_color)

        # note order is x, y, z for VisPy
        self._rect_line_data2D = np.array(
            [[0, 0, 0], [1, 0, 0], [1, 0, 0], [1, 1, 0],
             [1, 1, 0], [0, 1, 0], [0, 1, 0], [0, 0, 0]]
        )
        self._handle_line_data2D = np.array(
            [[0, 0, 0], [1, 0, 0], [1, 0, 0], [1, 1, 0],
             [1, 1, 0], [0, 1, 0], [0, 1, 0], [0, 0, 0]]
        )
        self._handle_side_length = 16

    def attach(self, viewer, view, canvas, parent=None, order=0):
        super().attach(viewer, view, canvas, parent, order)

        self.rect_node = Compound(
            [Line(connect='segments', method='gl', width=4)],
            parent=parent,
        )
        self.rect_node.transform = STTransform()
        self.rect_node.order = order

        self.handle_node = Compound(
            [Line(connect='segments', method='gl', width=2)],
            parent=parent,
        )
        self.handle_node.transform = STTransform()
        self.handle_node.order = order

        self._nodes = [self.rect_node, self.handle_node]

        canvas.connect(self.on_mouse_press)
        canvas.connect(self.on_mouse_move)
        canvas.connect(self.on_mouse_release)
        self._viewer.camera.events.zoom.connect(self._on_zoom_change)
        self._viewer.dims.events.ndisplay.connect(self._on_data_change)

        self._on_zoom_change(None)
        self._on_data_change(None)
        self._update_position()
        self._update_size()

    def setVisible(self, value):
        super().setVisible(value)
        self._on_data_change(None)

    def _update_position(self):
        if not self._attached:
            return

        self.rect_node.transform.translate = [self._position[0] - 0.5,
                                              self._position[1] - 0.5,
                                              0, 0]
        self._update_handle()

    def _update_size(self):
        if not self._attached:
            return

        self.rect_node.transform.scale = [self._size[0], self._size[1], 1, 1]
        self._update_handle()

    def _update_handle(self):
        if not self._attached:
            return

        self.handle_node.transform.translate = [self._position[0] - 0.5 + self._size[0],
                                                self._position[1] - 0.5 + self._size[1],
                                                0, 0]

    def _on_data_change(self, event):
        if not self._attached or not self._visible:
            return

        # Actual number of displayed dims
        ndisplay = len(self._viewer.dims.displayed)
        if ndisplay != 2:
            raise ValueError('ndisplay not supported')

        self.rect_node._subvisuals[0].set_data(self._rect_line_data2D, self._rect_color)
        self.handle_node._subvisuals[0].set_data(self._handle_line_data2D, self._handle_color)

    def _on_zoom_change(self, event):
        if not self._attached:
            return

        self._world_scale = 1 / self._viewer.camera.zoom
        self.handle_node.transform.scale = [self._handle_side_length * self._world_scale,
                                            self._handle_side_length * self._world_scale,
                                            1, 1]

    def on_mouse_press(self, event):
        if not self._visible or event.button != 1:
            return

        # Determine whether the line was clicked
        mouse_pos = self._view.scene.node_transform(self._view).imap(event.pos)[0:2]

        pos_start = self.position
        pos_end = self.position + self._size

        if (pos_end[0] <= mouse_pos[0] <
                pos_end[0] + self._world_scale * self._handle_side_length and
            pos_end[1] <= mouse_pos[1] <
                pos_end[1] + self._world_scale * self._handle_side_length):
            self._drag_mode = 'scale'
        elif (pos_start[0] <= mouse_pos[0] < pos_end[0] and
              pos_start[1] <= mouse_pos[1] < pos_end[1]):
            self._drag_mode = 'move'
        else:
            return

        # Prepare for dragging
        self._view.interactive = False
        self._start_move_visual_pos = self.position
        self._start_move_visual_size = self.size
        self._start_move_mouse_pos = mouse_pos

    def on_mouse_move(self, event):
        if not self._visible or self._drag_mode is None:
            return

        mouse_pos = self._view.scene.node_transform(self._view).imap(event.pos)[0:2]
        if self._drag_mode == 'move':
            self.position = np.rint(
                self._start_move_visual_pos + mouse_pos - self._start_move_mouse_pos
            )
        elif self._drag_mode == 'scale':
            self.size = np.rint(
                np.clip(self._start_move_visual_size + mouse_pos - self._start_move_mouse_pos,
                        1, None)
            )

    def on_mouse_release(self, event):
        if not self._visible or event.button != 1:
            return

        self._view.interactive = True
        self._drag_mode = None


class VispyLineVisual(VispyBaseVisual):
    sigPositionChanged = QtCore.Signal(np.ndarray, int)

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):
        self._position = np.array(value, dtype=int)
        self._update_position()

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = value
        self._update_angle()

    def __init__(self, color='yellow', movable=False):
        super().__init__()
        self._drag_mode = None
        self._world_scale = 1

        self._position = [0, 0]
        self._angle = 0.0

        self._color = Color(color)
        self._movable = movable
        self._click_sensitivity = 16

        # note order is x, y, z for VisPy
        self._line_data2D = np.array(
            [[0, 0, 0], [1, 0, 0]]
        )
        self._line_length = 4096

    def attach(self, viewer, view, canvas, parent=None, order=0):
        super().attach(viewer, view, canvas, parent, order)

        self.node = Compound(
            [Line(connect='segments', method='gl', width=4)],
            parent=parent,
        )
        self.node.transform = STTransform()
        self.node.order = order

        self._nodes = [self.node]

        canvas.connect(self.on_mouse_press)
        canvas.connect(self.on_mouse_move)
        canvas.connect(self.on_mouse_release)
        self._viewer.camera.events.zoom.connect(self._on_zoom_change)
        self._viewer.dims.events.ndisplay.connect(self._on_data_change)

        self._on_zoom_change(None)
        self._on_data_change(None)
        self._update_position()

    def setVisible(self, value):
        super().setVisible(value)
        self._on_data_change(None)

    def _update_position(self):
        if not self._attached:
            return

        angleRad = np.deg2rad(self._angle)
        self.node.transform.translate = [
            self._position[0] - self._line_length / 2 * self._world_scale * (np.cos(angleRad)),
            self._position[1] - self._line_length / 2 * self._world_scale * (np.sin(angleRad)),
            0, 0
        ]

    def _update_angle(self):
        if not self._attached:
            return

        self._line_data2D = np.array(
            [
                [0, 0, 0],
                [self._world_scale * self._line_length * np.cos(np.deg2rad(self._angle)),
                 self._world_scale * self._line_length * np.sin(np.deg2rad(self._angle)),
                 0]
            ]
        )
        self._on_data_change(None)
        self._update_position()

    def _on_data_change(self, event):
        if not self._attached or not self._visible:
            return

        # Actual number of displayed dims
        ndisplay = len(self._viewer.dims.displayed)
        if ndisplay != 2:
            raise ValueError('ndisplay not supported')

        self.node._subvisuals[0].set_data(self._line_data2D, self._color)

    def _on_zoom_change(self, event):
        if not self._attached:
            return

        self._world_scale = 1 / self._viewer.camera.zoom
        self._update_angle()

    def on_mouse_press(self, event):
        if not self._visible or not self._movable or event.button != 1:
            return

        # Determine whether the line was clicked
        mouse_pos = np.array(self._view.scene.node_transform(self._view).imap(event.pos)[0:2])

        s = np.sin(np.deg2rad(-self.angle))
        c = np.cos(np.deg2rad(-self.angle))

        center = np.array(self.position)

        mouse_pos_rot = mouse_pos - center
        mouse_pos_rot = np.array([mouse_pos_rot[0] * c - mouse_pos_rot[1] * s,
                                  mouse_pos_rot[0] * s + mouse_pos_rot[1] * c])
        mouse_pos_rot = mouse_pos_rot + center

        x_start = self.position[0] - self._line_length / 2
        x_end = self.position[0] + self._line_length / 2
        y_start = self.position[1] - self._click_sensitivity * self._world_scale
        y_end = self.position[1] + self._click_sensitivity * self._world_scale

        if x_start <= mouse_pos_rot[0] <= x_end and y_start <= mouse_pos_rot[1] <= y_end:
            self._drag_mode = 'move'
        else:
            return

        # Prepare for dragging
        self._view.interactive = False
        self._start_move_visual_pos = self.position
        self._start_move_mouse_pos = mouse_pos

    def on_mouse_move(self, event):
        if not self._visible or not self._movable or self._drag_mode is None:
            return

        mouse_pos = self._view.scene.node_transform(self._view).imap(event.pos)[0:2]
        if self._drag_mode == 'move':
            self.position = np.rint(
                self._start_move_visual_pos + mouse_pos - self._start_move_mouse_pos
            )

    def on_mouse_release(self, event):
        if not self._visible or not self._movable or event.button != 1:
            return

        self._view.interactive = True
        self._drag_mode = None


class VispyGridVisual(VispyBaseVisual):
    def __init__(self, color='yellow'):
        super().__init__()
        self._color = Color(color).rgba
        self._shape = np.array([0, 0])
        self._line_data2D = None
        self._line_length = 4096

    def attach(self, viewer, view, canvas, parent=None, order=0):
        super().attach(viewer, view, canvas, parent, order)

        self._update_line_data()

        self.node = Compound(
            [Line(connect='segments', method='gl', width=4)],
            parent=parent,
        )
        self.node.transform = STTransform()
        self.node.order = order

        self._nodes = [self.node]

        self._viewer.camera.events.zoom.connect(self._on_zoom_change)
        self._viewer.dims.events.ndisplay.connect(self._on_data_change)

        self._on_data_change(None)

    def setVisible(self, value):
        super().setVisible(value)
        self._on_data_change(None)

    def update(self, shape):
        self._shape = np.array(shape)
        self._update_line_data()

    def _update_line_data(self):
        scaled_line_length = self._line_length / self._viewer.camera.zoom
        self._line_data2D = np.array(
            [
                self._get_center_line_p1(0.25 * self._shape, scaled_line_length, True),
                self._get_center_line_p2(0.25 * self._shape, scaled_line_length, True),
                self._get_center_line_p1(0.375 * self._shape, scaled_line_length, True),
                self._get_center_line_p2(0.375 * self._shape, scaled_line_length, True),
                self._get_center_line_p1(0.50 * self._shape, scaled_line_length, True),
                self._get_center_line_p2(0.50 * self._shape, scaled_line_length, True),
                self._get_center_line_p1(0.625 * self._shape, scaled_line_length, True),
                self._get_center_line_p2(0.625 * self._shape, scaled_line_length, True),
                self._get_center_line_p1(0.75 * self._shape, scaled_line_length, True),
                self._get_center_line_p2(0.75 * self._shape, scaled_line_length, True),

                self._get_center_line_p1(0.25 * self._shape, scaled_line_length, False),
                self._get_center_line_p2(0.25 * self._shape, scaled_line_length, False),
                self._get_center_line_p1(0.375 * self._shape, scaled_line_length, False),
                self._get_center_line_p2(0.375 * self._shape, scaled_line_length, False),
                self._get_center_line_p1(0.50 * self._shape, scaled_line_length, False),
                self._get_center_line_p2(0.50 * self._shape, scaled_line_length, False),
                self._get_center_line_p1(0.625 * self._shape, scaled_line_length, False),
                self._get_center_line_p2(0.625 * self._shape, scaled_line_length, False),
                self._get_center_line_p1(0.75 * self._shape, scaled_line_length, False),
                self._get_center_line_p2(0.75 * self._shape, scaled_line_length, False)
            ]
        )
        self._on_data_change(None)

    def _on_data_change(self, event):
        if not self._attached or not self._visible or self._line_data2D is None:
            return

        # Actual number of displayed dims
        ndisplay = len(self._viewer.dims.displayed)
        if ndisplay != 2:
            raise ValueError('ndisplay not supported')

        self.node._subvisuals[0].set_data(self._line_data2D, self._color)

    def _on_zoom_change(self, event):
        if not self._attached:
            return

        self._update_line_data()


class VispyCrosshairVisual(VispyBaseVisual):
    def __init__(self, color='yellow'):
        super().__init__()
        self._paused = False
        self._mouse_moved_since_press = False
        self._color = Color(color).rgba
        self._line_positions = [0, 0]
        self._line_data2D = None
        self._line_length = 4096

    def attach(self, viewer, view, canvas, parent=None, order=0):
        super().attach(viewer, view, canvas, parent, order)

        self._update_line_data()

        self.node = Compound(
            [Line(connect='segments', method='gl', width=4)],
            parent=parent,
        )
        self.node.transform = STTransform()
        self.node.order = order

        self._nodes = [self.node]

        canvas.connect(self.on_mouse_press)
        canvas.connect(self.on_mouse_move)
        canvas.connect(self.on_mouse_release)
        self._viewer.camera.events.zoom.connect(self._on_zoom_change)
        self._viewer.dims.events.ndisplay.connect(self._on_data_change)

        self._on_data_change(None)

    def setVisible(self, value):
        super().setVisible(value)
        self._on_data_change(None)

    def _update_line_data(self):
        scaled_line_length = self._line_length / self._viewer.camera.zoom
        self._line_data2D = np.array(
            [
                self._get_center_line_p1(self._line_positions, scaled_line_length, True),
                self._get_center_line_p2(self._line_positions, scaled_line_length, True),
                self._get_center_line_p1(self._line_positions, scaled_line_length, False),
                self._get_center_line_p2(self._line_positions, scaled_line_length, False)
            ]
        )
        self._on_data_change(None)

    def _on_data_change(self, event):
        if not self._attached or not self._visible or self._line_data2D is None:
            return

        # Actual number of displayed dims
        ndisplay = len(self._viewer.dims.displayed)
        if ndisplay != 2:
            raise ValueError('ndisplay not supported')

        self.node._subvisuals[0].set_data(self._line_data2D, self._color)

    def _on_zoom_change(self, event):
        if not self._attached:
            return

        self._update_line_data()

    def on_mouse_press(self, event):
        if event.button != 1 or not self._visible:
            return

        self._mouse_moved_since_press = False

    def on_mouse_move(self, event):
        self._mouse_moved_since_press = True

        if not self._visible or self._paused:
            return

        mouse_pos = self._view.scene.node_transform(self._view).imap(event.pos)[0:2]
        self._line_positions = [mouse_pos[0], mouse_pos[1]]
        self._update_line_data()

    def on_mouse_release(self, event):
        if event.button != 1 or not self._visible or self._mouse_moved_since_press:
            return

        self._paused = not self._paused
        if not self._paused:
            self.on_mouse_move(event)


class VispyScatterVisual(VispyBaseVisual):
    def __init__(self, color='red', symbol='x'):
        super().__init__()
        self._color = Color(color)
        self._symbol = symbol
        self._markers_data = -1e8 * np.ones((1, 2))

    def attach(self, viewer, view, canvas, parent=None, order=0):
        super().attach(viewer, view, canvas, parent, order)

        self.node = Markers(pos=self._markers_data, parent=parent)
        self.node.transform = STTransform()
        self.node.order = order

        self._nodes = [self.node]

        self._viewer.dims.events.ndisplay.connect(self._on_data_change)

        self._on_data_change(None)

    def setVisible(self, value):
        super().setVisible(value)
        self._on_data_change(None)

    def setData(self, x, y):
        self._markers_data = np.column_stack((x, y))
        self._on_data_change(None)

    def _on_data_change(self, event):
        if not self._attached or not self._visible:
            return

        # Actual number of displayed dims
        ndisplay = len(self._viewer.dims.displayed)
        if ndisplay != 2:
            raise ValueError('ndisplay not supported')

        self.node.set_data(self._markers_data, edge_color=self._color, face_color=self._color,
                           symbol=self._symbol)
