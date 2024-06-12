#!/usr/bin/env python3
import os
import sys
import shutil
import setuptools

# Workaround issue in pip with "pip install -e --user ."
import site
site.ENABLE_USER_SITE = True

with open("README.rst", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="thorlabs_apt_device",
    version="0.3.8",
    author="Patrick Tapping",
    author_email="mail@patricktapping.com",
    description="Interface to ThorLabs devices which communicate using the APT protocol.",
    long_description=long_description,
    url="https://gitlab.com/ptapping/thorlabs-apt-device",
    project_urls={
        "Documentation": "https://thorlabs-apt-device.readthedocs.io/",
        "Source": "https://gitlab.com/ptapping/thorlabs-apt-device",
        "Tracker": "https://gitlab.com/ptapping/thorlabs-apt-device/-/issues",
    },
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "pyserial",
    ],
)
