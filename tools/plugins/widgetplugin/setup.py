# setup.py for a Camera Plugin
from setuptools import setup, find_packages

setup(
    name="widgetplugin",
    version="0.1",
    packages=find_packages(),
    entry_points={
        'imswitch.implugins.widgets': [
            'widgetplugincontroller = widgetplugincontroller:widgetplugincontroller',
            'widgetpluginwidget = widgetpluginwidget:widgetpluginwidget',
        ],
    }
)
