import napari
import numpy as np
from pyqtgraph.Qt import QtCore
from vispy.color import Color
from vispy.scene.visuals import Compound, Line, Markers
from vispy.visuals.transforms import STTransform


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
        self._position = np.array(value, dtype=np.int)
        self._update_position()
        self.sigROIChanged.emit(self.position, self.size)

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, value):
        self._size = np.array(value, dtype=np.int)
        self._update_size()
        self.sigROIChanged.emit(self.position, self.size)

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

        if (pos_end[0] <= mouse_pos[0] < pos_end[0] + self._world_scale * self._handle_side_length and
            pos_end[1] <= mouse_pos[1] < pos_end[1] + self._world_scale * self._handle_side_length):
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
        self._position = np.array(value, dtype=np.int)
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

        self.node.transform.translate = [
            self._position[0] - self._line_length / 2 * self._world_scale * (np.cos(np.deg2rad(self._angle))),
            self._position[1] - self._line_length / 2 * self._world_scale * (np.sin(np.deg2rad(self._angle))),
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

    def on_mouse_move(self, event):
        if not self._visible or self._paused:
            return

        mouse_pos = self._view.scene.node_transform(self._view).imap(event.pos)[0:2]
        self._line_positions = [mouse_pos[0], mouse_pos[1]]
        self._update_line_data()

    def on_mouse_release(self, event):
        if event.button != 1 or not self._visible:
            return

        #self._paused = not self._paused


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
