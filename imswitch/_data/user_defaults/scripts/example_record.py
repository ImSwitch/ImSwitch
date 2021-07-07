"""
This script demonstrates some basic functions for recording, changing what
module is displayed, and waiting for signals to be emitted. Note that the
recording does not stop automatically if the script is terminated before it
finishes.
"""


import time

print('Starting recording in "until stop" mode...')
api.imcontrol.setRecModeUntilStop()
api.imcontrol.startRecording()

print('Recording started. Showing hardware control tab for a few seconds before stopping.')
time.sleep(3)
mainWindow.setCurrentModule('imcontrol')
time.sleep(5)

print('Going back to scripting tab.')
mainWindow.setCurrentModule('imscripting')
time.sleep(2)

print('Stopping recording...')
waitForRecordingToEnd = getWaitForSignal(api.imcontrol.signals().recordingEnded)
api.imcontrol.stopRecording()  # It's important to call this after getWaitForSignal!
waitForRecordingToEnd()

print('Recording stopped.')


# Copyright (C) 2020, 2021 TestaLab
# This file is part of ImSwitch.
#
# ImSwitch is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ImSwitch is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
