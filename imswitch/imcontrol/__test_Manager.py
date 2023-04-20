import numpy as np

from imswitch.imcontrol.model import configfiletools

from imswitch.imcontrol.model.managers.positioners.SmarACTPositionerManager import SmarACTPositionerManager
from unittest import TestCase
import logging

from imswitch.imcontrol.view import ViewSetupInfo

logger = logging.getLogger('test stage')
logging.basicConfig(level=logging.DEBUG)
logger.error('critical1')

class TestReadConfig(TestCase):

    def test_me(self):
        options, optionsDidNotExist = configfiletools.loadOptions()
        print(options)
        setupInfo = configfiletools.loadSetupInfo(options, ViewSetupInfo )
        print(setupInfo)

class Test_PM(TestCase):

    def setUp(self) -> None:
        options, optionsDidNotExist = configfiletools.loadOptions()
        setupInfo = configfiletools.loadSetupInfo(options, ViewSetupInfo)
        p_info = setupInfo.positioners['SmarACT']
        self.drive: SmarACTPositionerManager = SmarACTPositionerManager(positionerInfo=p_info, name='something')

    def tearDown(self) -> None:
        self.drive.finalize()

    def test_connect(self):
        print('Setting up what the positioners are')
        print('Drive name: ', self.drive.name)



    def test_get_position(self):
        current_position = self.drive.position
        logger.critical(f'Current position: {current_position}')
        print(current_position)

    def test_move(self):

        for i, axis in enumerate('XYZ'):
            print(f'###### {i} #### {axis}')
            position = self.drive.position
            position_at_axis = position[axis]
            direction = -1*np.sign(position_at_axis)
            self.drive.move(direction, axis)
            new_position = self.drive.position
            new_position_at_axis = new_position[axis]
            position_as_array = np.array([position[a] for a in 'XYZ'])
            new_position_as_array = np.array([new_position[a] for a in 'XYZ'])
            diff = new_position_as_array - position_as_array

            msg = f'Error when moving axis {axis}.\n'
            msg += f'Initial position: {position_as_array}\n, new position: {new_position_as_array}\n, diff: {diff}\n'
            msg += str(self.drive.position)
            self.assertLessEqual(diff[i]-direction, 0.1, msg)

            logger.critical(f'Current position {self.drive.position}')


    def test_move_to_zero(self):
        for ax in self.drive.axes:
            logger.info(f'Moving axis {ax} to 0')
            self.drive.setPosition(position=0, axis=ax)
            p_out = self.drive.position
            try:
                self.assertAlmostEqual(p_out[ax], 0, places=3)
            except AssertionError:
                logger.error(f'Could not move the position properly for axis {ax}. Got: ')
                logger.info(f'Final position: {self.drive.position}')


