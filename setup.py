from setuptools import setup, find_packages

# Version will be read from your package's __init__.py
# Make sure __version__ is defined in imswitch/__init__.py
def get_version():
    version_file = 'imswitch/__init__.py'
    with open(version_file, 'r') as file:
        for line in file:
            if line.startswith('__version__'):
                # Strip the line to remove whitespaces and newline characters,
                # then split it on '=' and strip again to remove any remaining whitespaces.
                # Finally, strip the quotes from the version string.
                return line.strip().split('=')[1].strip().strip('\'"')
    raise RuntimeError('Unable to find version string.')


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ImSwitch",
    version=get_version(),
    author="Benedict Diederich, Xavier Casas Moreno, et al.",
    author_email="benedictdied@gmail.com",
    description="Microscopy control",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/openuc2/ImSwitch",
    project_urls={
        "Bug Tracker": "https://github.com/openuc2/ImSwitch/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "coloredlogs >= 15",
        "colour-science >= 0.3",
        "dataclasses-json >= 0.5",
        "h5py >= 3",
        "pyvisa-py==0.4.1",
        "lantzdev[qt] >= 0.5.2",
        "luddite >= 1",
        "napari[pyqt5]",
        "nidaqmx >= 0.5.7",
        "numpy >= 1.19",
        "packaging >= 19",
        "psutil >= 5.4.8",
        "PyQt5 >= 5.15.2",
        "pyqtgraph >= 0.12.1",
        "microscope",
        "pyserial >= 3.4",
        "QDarkStyle >= 3",
        "QScintilla >= 2.12",
        "qtpy >= 1.9",
        "requests >= 2.25",
        "scikit-image >= 0.18",
        "Send2Trash >= 1.8",
        "tifffile >= 2020.11.26",
        "ome_zarr >= 0.6.1",
        "Pyro5 >= 5.14",
        "fastAPI >= 0.86.0",
        "uvicorn[standard] >= 0.19.0",
        "matplotlib >= 3.6",
        "websockets >= 10.0",
        "websocket-client >= 1.2"
    ],
    entry_points={
        "console_scripts": [
            "imswitch = imswitch.__main__:main",
        ],
        'imswitch.implugins.detectors': [],
        'imswitch.implugins.lasers': [],
        'imswitch.implugins.positioner': []
    },
)

