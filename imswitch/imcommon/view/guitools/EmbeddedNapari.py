import napari


class EmbeddedNapari(napari.Viewer):
    def __init__(self, *args, show=False, **kwargs):
        super().__init__(*args, show=show, **kwargs)
        self.window._qt_window.menuBar().setNativeMenuBar(False)

    def getWidget(self):
        return self.window._qt_window
