from lantz import Feat
from lantz.drivers.cobolt.cobolt0601 import Cobolt0601


class Cobolt0601_f2(Cobolt0601):
    """Driver for any Cobolt 06-01 Series laser, new firmware.
    """
    @Feat(units='mW')
    def power_mod(self):
        """Laser modulated power (mW).
        """
        return float(self.query('glmp?'))

    @power_mod.setter
    def power_mod(self, value):
        self.query('slmp {}'.format(value))
