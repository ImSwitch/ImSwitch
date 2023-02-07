from ..basecontrollers import ImConWidgetController


class MotCorrController(ImConWidgetController):
    """ Linked to MotCorrWidget."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self._manager= self._master.leicadmiManager

        self._widget.motcorrControl.slider.valueChanged[int].connect(self.changeSlider)
        self._widget.motcorrControl.setPointEdit.returnPressed.connect(self.changeEdit)
        
    def changeSlider(self, _):
        """ Called when the slider is moved, sets the power of the laser to
        value."""
        self._manager.motCorrPos(self._widget.motcorrControl.slider.value())
        self._widget.motcorrControl.setPointEdit.setText(str(self._widget.motcorrControl.slider.value()))

    def changeEdit(self):
        """ Called when the user manually changes the intensity value of the
        laser. Sets the laser power to the corresponding value."""
        self._manager.motCorrPos(float(self._widget.motcorrControl.setPointEdit.text()))
        self._widget.motcorrControl.slider.setValue(float(self._widget.motcorrControl.setPointEdit.text()))

