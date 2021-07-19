from .BetterSlider import BetterSlider

from qtpy import QtCore


class FloatSlider(BetterSlider):
    """ Slider that uses floating-point values.

    Based on: https://stackoverflow.com/a/50300848 """

    floatValueChanged = QtCore.Signal(float)

    def __init__(self, *args, decimals=2, **kwargs):
        super().__init__(*args, **kwargs)
        self._multiplier = 10 ** decimals

        self.valueChanged.connect(self.emitFloatValueChanged)
        self.__superValueChanged = self.valueChanged
        self.valueChanged = self.floatValueChanged

    def emitFloatValueChanged(self):
        self.floatValueChanged.emit(self.value())

    def value(self):
        return float(super().value()) / self._multiplier

    def setMinimum(self, value):
        return super().setMinimum(value * self._multiplier)

    def setMaximum(self, value):
        return super().setMaximum(value * self._multiplier)

    def setSingleStep(self, value):
        return super().setSingleStep(value * self._multiplier)

    def singleStep(self):
        return float(super().singleStep()) / self._multiplier

    def setValue(self, value):
        super().setValue(int(value * self._multiplier))
