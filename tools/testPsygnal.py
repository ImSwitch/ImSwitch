from psygnal import Signal

# define an object with class attribute Signals
class mCommChannel:

    # this signal will emit a single string
    move_stage = Signal(str)

    def __init__(self, value=0):
        self._value = value

    def set_value(self, value):
        if value != self._value:
            self._value = str(value)
            # emit the signal
            self.move_stage.emit(self._value)
# Note how the class itself calls move_stage.emit whenever the value changes. This notifies "anyone listening" that a change has occurred.
# Other components can subscribe to these change notifications by connecting a callback function to the signal instance using its connect method


def on_move_stage(new_value):
    print(f"The new value is {new_value!r}")

# instantiate the object with Signals
commchannel = mCommChannel()

# connect one or more callbacks with `connect`
commchannel.move_stage.connect(on_move_stage)

commchannel.move_stage.emit('hello!')  # prints: 'The new value is 'hello!'

# callbacks are called when value changes
commchannel.set_value('hello!')  # prints: 'The new value is 'hello!'