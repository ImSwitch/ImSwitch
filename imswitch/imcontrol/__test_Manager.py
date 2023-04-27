import numpy as np

from imswitch.imcontrol.model import configfiletools

from imswitch.imcontrol.model.managers.positioners.SmarACTPositionerManager import SmarACTPositionerManager
from unittest import TestCase
import logging

from imswitch.imcontrol.view import ViewSetupInfo

logger = logging.getLogger('test stage')
logging.basicConfig(level=logging.INFO)


OK_to_run=True


class TestSmarACTPositionManager(TestCase):

    def setUp(self) -> None:
        global OK_to_run
        if OK_to_run is None:
            print(
                'WARNING!!! This is a hardware test. The stage will move in random directions. Only run this if that is safe')
            answer = input('Continue? [n]')
            if answer.lower() != 'y':
                OK_to_run = False
            else:
                OK_to_run = True
        elif OK_to_run is False:
            raise RuntimeError('Cannot run test as running hasnt been confirmed')
        options, optionsDidNotExist = configfiletools.loadOptions()
        setupInfo = configfiletools.loadSetupInfo(options, ViewSetupInfo)
        p_info = setupInfo.positioners['SmarACT']
        self.drive: SmarACTPositionerManager = SmarACTPositionerManager(positionerInfo=p_info, name='drive to test')

    def tearDown(self) -> None:
        self.drive.finalize()


    def test_get_position(self):
        """
        Get the position and display it.
        """
        current_position = self.drive.position
        logger.info(f'Current position: {current_position}')


    def test_move(self):
        """
        Move all axes once and check that the movements are what we expect.
        """
        for i, axis in enumerate('XYZ'):
            print(f'###### {i} #### {axis}')
            position = self.drive.position
            position_at_axis = position[axis]
            direction = -1*np.sign(position_at_axis)
            self.drive.move(direction, axis)
            new_position = self.drive.position

            position_as_array = np.array([position[a] for a in 'XYZ'])
            new_position_as_array = np.array([new_position[a] for a in 'XYZ'])
            diff = new_position_as_array - position_as_array

            msg = f'Error when moving axis {axis}.\n'
            msg += f'Initial position: {position_as_array}\n, new position: {new_position_as_array}\n, diff: {diff}\n'
            msg += str(self.drive.position)
            self.assertLessEqual(diff[i]-direction, 0.1, msg)



    def test_move_to_zero(self):
        """Move every axis to 0 and check that it ends up at zero."""
        for ax in self.drive.axes:
            logger.info(f'Moving axis {ax} to 0')
            self.drive.setPosition(position=0, axis=ax)
            p_out = self.drive.position
            try:
                self.assertAlmostEqual(p_out[ax], 0, places=3)
            except AssertionError:
                logger.error(f'Could not move the position properly for axis {ax}. Got: ')
                logger.info(f'Final position: {self.drive.position}')


