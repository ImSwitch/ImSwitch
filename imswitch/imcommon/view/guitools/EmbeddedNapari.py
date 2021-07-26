import napari
from napari.utils.translations import trans
from qtpy import QtWidgets


class EmbeddedNapari(napari.Viewer):
    """ Napari viewer to be embedded in non-napari windows. Also includes a
    feature to protect certain layers from being removed when added using
    the add_image method. """

    def __init__(self, *args, show=False, **kwargs):
        super().__init__(*args, show=show, **kwargs)

        # Monkeypatch layer removal methods
        oldRemove = self.layers.remove
        def newRemove(layer, force=False):
            if not hasattr(layer, 'protected') or not layer.protected or force:
                oldRemove(layer)
        self.layers.remove = newRemove

        oldPop = self.layers.pop
        def newPop(index, force=False):
            layer = self.layers[index]
            if not hasattr(layer, 'protected') or not layer.protected or force:
                oldPop(index)
        self.layers.pop = newPop

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
