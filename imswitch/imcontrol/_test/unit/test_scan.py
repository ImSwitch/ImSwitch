import os

import numpy as np

from imswitch.imcontrol.model import ScanManager
from imswitch.imcontrol._test import setupInfoBasic


def test_scan_signals():
    stageParameters = {'target_device': ['X', 'Y', 'Z'],
                       'axis_length': [5, 5, 5],
                       'axis_step_size': [1, 1, 1],
                       'axis_startpos': [[0], [0], [0]],
                       'sequence_time': 0.005,
                       'sample_rate': 100000,
                       'return_time': 0.001}
    TTLParameters = {'target_device': ['405', '488'],
                     'TTL_start': [[0.0001, 0.004], [0, 0]],
                     'TTL_end': [[0.0015, 0.005], [0, 0]],
                     'sequence_time': 0.005,
                     'sample_rate': 100000}

    sh = ScanManager(setupInfo=setupInfoBasic)
    fullsig, _ = sh.makeFullScan(stageParameters, TTLParameters)

    # All required dicts exist
    assert 'scanSignalsDict' in fullsig
    assert 'TTLCycleSignalsDict' in fullsig

    # All targets match
    assert set(fullsig['scanSignalsDict'].keys()) == set(stageParameters['target_device'])
    assert set(fullsig['TTLCycleSignalsDict'].keys()) == set(TTLParameters['target_device'])

    # Lengths of signal arrays match
    for device in fullsig['scanSignalsDict']:
        assert len(fullsig['scanSignalsDict'][device]) == 111600

    for device in fullsig['TTLCycleSignalsDict']:
        assert len(fullsig['TTLCycleSignalsDict'][device]) == 111600

    # Basic stage signal checks
    assert fullsig['scanSignalsDict']['X'].min() == 0.0
    assert fullsig['scanSignalsDict']['Y'].min() == 0.0
    assert fullsig['scanSignalsDict']['Z'].min() == 0.0
    assert fullsig['scanSignalsDict']['X'].max()\
           == fullsig['scanSignalsDict']['Y'].max()
    assert fullsig['scanSignalsDict']['Z'].max() == 0.5

    # Basic TTL signal checks
    assert np.count_nonzero(fullsig['TTLCycleSignalsDict']['405']) == 51840
    assert np.all(fullsig['TTLCycleSignalsDict']['488'] == False)

    # Check all values against precomputed ones
    with np.load(os.path.join(os.path.dirname(__file__), 'test_scan_expected.npz')) as data:
        assert np.all(fullsig['scanSignalsDict']['X'] == data['Stage_X'])
        assert np.all(fullsig['scanSignalsDict']['Y'] == data['Stage_Y'])
        assert np.all(fullsig['scanSignalsDict']['Z'] == data['Stage_Z'])
        assert np.all(fullsig['TTLCycleSignalsDict']['405'] == data['TTL_405'])
        assert np.all(fullsig['TTLCycleSignalsDict']['488'] == data['TTL_488'])


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
