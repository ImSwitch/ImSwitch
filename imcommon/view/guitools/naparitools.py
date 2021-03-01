import napari


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

