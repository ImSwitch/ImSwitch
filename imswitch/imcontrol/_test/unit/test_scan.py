import os

import numpy as np

from imswitch.imcontrol.model import ScanManager
from imswitch.imcontrol._test import setupInfoBasic


def test_scan_signals():
    Stageparameters = {'Targets[x]': ['Stage_X', 'Stage_Y', 'Stage_Z'],
                       'Sizes[x]': [5, 5, 5],
                       'Step_sizes[x]': [1, 1, 1],
                       'Start[x]': [0, 0, 0],
                       'Sequence_time_seconds': 0.005,
                       'Sample_rate': 100000,
                       'Return_time_seconds': 0.001}
    TTLparameters = {'Targets[x]': ['405', '488'],
                     'TTLStarts[x,y]': [[0.0001, 0.004], [0, 0]],
                     'TTLEnds[x,y]': [[0.0015, 0.005], [0, 0]],
                     'Sequence_time_seconds': 0.005,
                     'Sample_rate': 100000}

    sh = ScanManager(setupInfo=setupInfoBasic)
    fullsig = sh.makeFullScan(Stageparameters, TTLparameters)

    # All required dicts exist
    assert 'stageScanSignalsDict' in fullsig
    assert 'TTLCycleSignalsDict' in fullsig

    # All targets match
    assert set(fullsig['stageScanSignalsDict'].keys()) == set(Stageparameters['Targets[x]'])
    assert set(fullsig['TTLCycleSignalsDict'].keys()) == set(TTLparameters['Targets[x]'])

    # Lengths of signal arrays match
    for device in fullsig['stageScanSignalsDict']:
        assert len(fullsig['stageScanSignalsDict'][device]) == 111600

    for device in fullsig['TTLCycleSignalsDict']:
        assert len(fullsig['TTLCycleSignalsDict'][device]) == 111600

    # Basic stage signal checks
    assert fullsig['stageScanSignalsDict']['Stage_X'].min() == 0.0
    assert fullsig['stageScanSignalsDict']['Stage_Y'].min() == 0.0
    assert fullsig['stageScanSignalsDict']['Stage_Z'].min() == 0.0
    assert fullsig['stageScanSignalsDict']['Stage_X'].max()\
           == fullsig['stageScanSignalsDict']['Stage_Y'].max()
    assert fullsig['stageScanSignalsDict']['Stage_Z'].max() == 0.5

    # Basic TTL signal checks
    assert np.count_nonzero(fullsig['TTLCycleSignalsDict']['405']) == 51840
    assert np.all(fullsig['TTLCycleSignalsDict']['488'] == False)

    # Check all values against precomputed ones
    with np.load(os.path.join(os.path.dirname(__file__), 'test_scan_expected.npz')) as data:
        assert np.all(fullsig['stageScanSignalsDict']['Stage_X'] == data['Stage_X'])
        assert np.all(fullsig['stageScanSignalsDict']['Stage_Y'] == data['Stage_Y'])
        assert np.all(fullsig['stageScanSignalsDict']['Stage_Z'] == data['Stage_Z'])
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
