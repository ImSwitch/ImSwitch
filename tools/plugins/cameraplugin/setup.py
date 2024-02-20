# setup.py for a Camera Plugin
from setuptools import setup, find_packages

setup(
    name="cameraplugin",
    version="0.1",
    packages=find_packages(),
    entry_points={
        'imswitch.implugins.detectors': [
            'cameraplugin = cameraplugin:cameraplugin',
        ],
    }
)
