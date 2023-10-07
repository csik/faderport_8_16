import collections
from itertools import cycle, islice
from typing import NamedTuple
from abc import ABC, abstractmethod
import time

import mido

# Button = namedtuple('Button', ['name', 'press', 'light'])

class Button(NamedTuple):
    name: str
    press: int
    light: str
Button.__doc__ = "FaderPort button details."
Button.name.__doc__ = "Button name, usually what's written on the physical button."
Button.press.__doc__ = "MIDI note sent when button is pressed and released."
Button.light.__doc__ = "MIDI note to send to illuminate the button."

# These are the FaderPort buttons, specifically ordered to "snake" down from
# the top to the bottom. Changing the order will mess up the pattern :-(

BUTTONS = [

    # General Controls (left side)
    Button(name='Pan_Param',    press=0x20, light='na'),
    Button(name='Arm',          press=0x00, light='LED'),
    Button(name='Solo_Clear',   press=0x01, light='LED'),
    Button(name='Mute_Clear',   press=0x02, light='LED'),
    Button(name='Bypass',       press=0x03, light='RGB'),
    Button(name='Macro',        press=0x04, light='RGB'),
    Button(name='Link',         press=0x05, light='RGB'),
    Button(name='Shift_Right',   press=0x06, light='LED'),

    # Channel Strip Controls
    Button(name='Solo_1', press=0x08, light='LED'),
    Button(name='Solo_2', press=0x09, light='LED'),
    Button(name='Solo_3', press=0x0A, light='LED'),
    Button(name='Solo_4', press=0x0B, light='LED'),
    Button(name='Solo_5', press=0x0C, light='LED'),
    Button(name='Solo_6', press=0x0D, light='LED'),
    Button(name='Solo_7', press=0x0E, light='LED'),
    Button(name='Solo_8', press=0x0F, light='LED'),
    Button(name='Mute_1', press=0x10, light='LED'),
    Button(name='Mute_2', press=0x11, light='LED'),
    Button(name='Mute_3', press=0x12, light='LED'),
    Button(name='Mute_4', press=0x13, light='LED'),
    Button(name='Mute_5', press=0x14, light='LED'),
    Button(name='Mute_6', press=0x15, light='LED'),
    Button(name='Mute_7', press=0x16, light='LED'),
    Button(name='Mute_8', press=0x17, light='LED'),
    Button(name='Select_1', press=0x18, light='RGB'),
    Button(name='Select_2', press=0x19, light='RGB'),
    Button(name='Select_3', press=0x1A, light='RGB'),
    Button(name='Select_4', press=0x1B, light='RGB'),
    Button(name='Select_5', press=0x1C, light='RGB'),
    Button(name='Select_6', press=0x1D, light='RGB'),
    Button(name='Select_7', press=0x1E, light='RGB'),
    Button(name='Select_8', press=0x1F, light='RGB'),
    Button(name='Fader_Touch_1', press=0x68, light='na'),
    Button(name='Fader_Touch_2', press=0x69, light='na'),
    Button(name='Fader_Touch_3', press=0x6A, light='na'),
    Button(name='Fader_Touch_4', press=0x6B, light='na'),
    Button(name='Fader_Touch_5', press=0x6C, light='na'),
    Button(name='Fader_Touch_6', press=0x6D, light='na'),
    Button(name='Fader_Touch_7', press=0x6E, light='na'),
    Button(name='Fader_Touch_8', press=0x6F, light='na'),

    # Fader Mode Buttons
    Button(name='Track',        press=0x28, light='LED'),
    Button(name='Edit_Plugins', press=0x2B, light='LED'),
    Button(name='Send',         press=0x29, light='LED'),
    Button(name='Pan',          press=0x2A, light='LED'),

    # Session Navigator
    Button(name='Prev',         press=0x2E, light='LED'),
    Button(name='Navigator',    press=0x53, light='na'),
    Button(name='Next',         press=0x2F, light='LED'),
    Button(name='Channel',      press=0x36, light='LED'),
    Button(name='Zoom',         press=0x37, light='LED'),
    Button(name='Scroll',       press=0x38, light='LED'),
    Button(name='Bank',         press=0x39, light='LED'),
    Button(name='Master',       press=0x3A, light='LED'),
    Button(name='Click',        press=0x3B, light='LED'),
    Button(name='Section',      press=0x3C, light='LED'),
    Button(name='Marker',       press=0x3D, light='LED'),

    # Mix Management
    Button(name='Audio',        press=0x3E, light='RGB'),
    Button(name='VI',           press=0x3F, light='RGB'),
    Button(name='Bus',          press=0x40, light='RGB'),
    Button(name='VCA',          press=0x41, light='RGB'),
    Button(name='All',          press=0x42, light='RGB'),
    Button(name='Shift_Left',  press=0x46, light='LED'),

    # Automation
    Button(name='Read',         press=0x4A, light='RGB'),
    Button(name='Write',        press=0x4B, light='RGB'),
    Button(name='Trim',         press=0x4C, light='RGB'),
    Button(name='Touch',        press=0x4D, light='RGB'),
    Button(name='Latch',        press=0x4E, light='RGB'),
    Button(name='Off',          press=0x4F, light='RGB'),

    # Transport
    Button(name='Loop',         press=0x56, light='LED'),
    Button(name='Rewind',       press=0x5B, light='LED'),
    Button(name='Fast_Forward', press=0x5C, light='LED'),
    Button(name='Stop',         press=0x5D, light='LED'),
    Button(name='Play',         press=0x5E, light='LED'),
    Button(name='Record',       press=0x5F, light='LED'),
    Button(name='Footswitch',   press=0x66, light='na'),

   ]

_button_from_name = {x.name: x for x in BUTTONS}
_button_from_press = {x.press: x for x in BUTTONS}


def button_from_name(name: str) -> Button:
    """
    Given a button name return the corresponding Button
    :param name: The name of a button
    :return: a Button
    """
    return _button_from_name[name.title()]


def button_from_press(press: int) -> Button:
    """
    Given a button press value return the corresponding button
    :param press: The value emitted by a pressed button
    :return: a Button
    """
    return _button_from_press.get(press, None)



class FaderPort(ABC):
    """
    An abstract class to interface with a Presonus FaderPort device.

    The Presonus FaderPort is a USB MIDI controller that features a
    motorized fader, an endless rotary controller and a bunch of buttons.
    This class will handle the basic interfacing to the device. You
    write a concrete subclass to implement your application specific
    requirements.

    This subclass must implement the following methods:

    * `on_button` — Called when button is pressed or released,
    * `on_close` — Called when MIDI port is about  to close,
    * `on_fader` — Called when fader is moved,
    * `on_fader_touch` — Called when fader is touched or released,
    * `on_open` — Called when MIDI port has opened,
    * `on_rotary` — Called when the Pan control is rotated.

    The `fader` property allows you to read or set the fader position
    on a scale of 0 to 1023.

    You can turn the button lights on and off individually using
    `light_on` and `light_off`.

    You can display hexadecimal characters (0-9, A-F) using `char_on`.
    This will use the button LEDs in a dot matrix style.
    (Extending this to the a full alphanumeric character set is an
    exercise left to the reader).

    There some methods for 'fancy' display effects, because why not?
    Check out: `countdown`, `snake`, `blink` and `chase`

    **IMPORTANT NOTE** - There is a 'feature' in the FaderPort that can
    cause you some problems. If the 'Off' button is lit the fader will
    not send value updates when it's moved.
    """

    def __init__(self):
        self.inport = None
        self.outport = None
        self._fader = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
        self._msb = 0

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self, number=0):
        """
        Open the FaderPort and register a callback so we can send and
        receive MIDI messages.
        :param number: 0 unless you've got more than one FaderPort attached.
                       In which case 0 is the first, 1 is the second etc
                       I only have access to a single device so I can't
                       actually test this.
        """
        self.inport = mido.open_input(find_faderport_input_name(number))
        self.outport = mido.open_output(find_faderport_output_name(number))
        self.outport.send(mido.Message.from_bytes([0x91, 0, 0x64]))  # A reset message???
        time.sleep(0.01)
        self.inport.callback = self._message_callback
        self.on_open()

    def close(self):
        self.on_close()
        self.inport.callback = None
        self.fader = 0
        self.all_off()
        self.outport.reset()
        self.inport.close()
        self.outport.close()

    @abstractmethod
    def on_open(self):
        """Called after the FaderPort has been opened."""
        pass

    @abstractmethod
    def on_close(self):
        """Called when the FaderPort is closing."""
        pass

    def _message_callback(self, msg):
        """Callback function to handle incoming MIDI messages."""
        try:
            if msg.type == 'note_on':
                try:
                    print(msg)
                    button = button_from_press(msg.note)
                    print(button.name)
                    if button:
                        self.on_button(button, msg.velocity != 0)
                except:
                    print("exception in note_on")
            elif msg.type == 'control_change':
                print("control change")
            elif msg.type == 'pitchwheel':
                try:
                    # print("in pitchwheel")
                    # print(f"pitch = {msg.pitch} channel = {msg.channel}")
                    self._fader[msg.channel] = msg.pitch
                    self.on_fader(pitch=msg.pitch, channel=msg.channel)
                    # print(f"fader {msg.channel} = {msg.pitch}")
                    # test by echoing to fader to the right
                    self.outport.send(mido.Message('pitchwheel',channel=msg.channel+1, pitch=msg.pitch))
                except:
                    print("exception in pitchwheel")
            else:
                print('Unhandled:', msg)
        except:
            print('Exception!')


    @abstractmethod
    def on_rotary(self, direction: int):
        """
        Called when the FaderPort "Pan" control is changed.
        :param direction:  1 if clockwise, -1 if anti-clockwise
        """
        pass

    @abstractmethod
    def on_button(self, button: Button, state: bool):
        """
        Called when a FaderPort button is pressed and released.
        :param button: The Button in question
        :param state:  True if pressed, False when released.
        """
        pass

    @abstractmethod
    def on_fader_touch(self, state: bool):
        """
        Called when the fader is touched and when it is released.
        :param state: True if touched, False when released.
        """
        pass

    @abstractmethod
    def on_fader(self, pitch: int, channel: int):
        """
        Called when the Fader has been moved.
        :param value: The new fader value.
        """
        pass

    @property
    def fader(self, channel) -> int:
        """"Returns the position of the Fader in the range -8192 to 8192"""
        return self._fader[channel]

    @fader.setter
    def fader(self, value: list):
        """Move the fader to a new position in the range -8192 to 8192."""
        pitch, channel = value
        self.outport.send(mido.Message('pitchwheel',channel=channel, pitch=pitch))
        #self._fader = int(value) if 0 < value < 1024 else 0
        #self.outport.send(mido.Message('control_change', control=0,
        #                               value=self._fader >> 7))
        #self.outport.send(mido.Message('control_change', control=32,
        #                               value=self._fader & 0x7F))

    def light_on(self, button: Button):
        """Turn the light on for the given Button.

        NOTE! If yuo turn the "Off" button light on, the fader won't
        report value updates when it's moved."""
        self.outport.send(mido.Message('note_on', note=button.light, value=1))

    def light_off(self, button: Button):
        """Turn the light off for the given Button"""
        self.outport.send(mido.Message('polytouch', note=button.light, value=0))

    def all_off(self):
        """Turn all the button lights off."""
        for button in BUTTONS:
            self.light_off(button)

    def all_on(self):
        """Turn all the button lights on.

        NOTE! The fader will not report value changes while the "Off"
        button is lit."""
        for button in BUTTONS:
            self.light_on(button)

    def snake(self, duration: float = 0.03):
        """
        Turn the button lights on then off in a snakelike sequence.
        NOTE! Does not remember prior state of lights and will finish
        with all lights off.
        :param duration: The duration to hold each individual button.
        """
        for button in BUTTONS:
            self.light_on(button)
            time.sleep(duration)

        for button in reversed(BUTTONS):
            self.light_off(button)
            time.sleep(duration)

    def blink(self, interval: float = 0.2, n: int = 3):
        """
        Blink all the lights on and off at once.
        NOTE! Does not remember prior state of lights and will finish
        with all lights off.
        :param interval: The length in seconds of an ON/OFF cycle
        :param n: How many times to cycle ON and OFF
        :return:
        """
        for i in range(n):
            self.all_on()
            time.sleep(interval / 2)
            self.all_off()
            time.sleep(interval / 2)

    def char_on(self, c):
        """
        Use button lights (as matrix) to display a hex character.
        :param c: String containing one of 0-9,A-F
        """
        if c.upper() in CHARACTERS:
            for i in CHARACTERS[c.upper()]:
                self.light_on(BUTTONS[i])

    def countdown(self, interval: float = 0.5):
        """
        Display a numeric countdown from 5
        :param interval: The interval in seconds for each number.
        """
        for c in '54321':
            self.char_on(c)
            time.sleep(interval * 0.66667)
            self.all_off()
            time.sleep(interval * 0.33333)

    def all_up(self):
        for x in range(0,8):
            self.fader = (8191,x)

    def all_down(self):
        for x in range(0,8):
            self.fader = (-8192,x)

    def all_zero(self):
        for x in range(0,8):
            self.fader = (0,x)

    def scribbletest(self):
        from scribbledata import d
        for i in d:
            self.outport.send(mido.Message('sysex', data=i))

    def chase(self, duration: float = 0.08, num_lights: int = 2, ticks: int = 20):
        """
        Display an animated light chaser pattern
        Chase will last ticks * duration seconds
        :param duration: How long each chase step will last in seconds
        :param num_lights: How many lights in the chase (1 to 4)
        :param ticks: How many chase steps.
        """
        seq = [
            button_from_name('Chan Down'),
            button_from_name('Bank'),
            button_from_name('Chan Up'),
            button_from_name('Output'),
            button_from_name('Off'),
            button_from_name('Undo'),
            button_from_name('Loop'),
            button_from_name('User'),
            button_from_name('Punch'),
            button_from_name('Shift'),
            button_from_name('Mix'),
            button_from_name('Read'),
        ]

        num_lights = num_lights if num_lights in [1, 2, 3, 4] else 2

        its = [cycle(seq) for _ in range(num_lights)]
        for i, it in enumerate(its):
            if i:
                consume(it, i * (len(seq) // num_lights))

        for x in range(ticks):
            for it in its:
                button = next(it)
                self.light_on(button)
            time.sleep(duration)
            self.all_off()


def find_faderport_input_name(number=0):
    """
    Find the MIDI input name for a connected FaderPort.

    NOTE! Untested for more than one FaderPort attached.
    :param number: 0 unless you've got more than one FaderPort attached.
                   In which case 0 is the first, 1 is the second etc
    :return: Port name or None
    """
    ins = [i for i in mido.get_input_names() if i.lower().startswith('faderport')]
    if 0 <= number < len(ins):
        return ins[number]
    else:
        return None


def find_faderport_output_name(number=0):
    """
    Find the MIDI output name for a connected FaderPort.

    NOTE! Untested for more than one FaderPort attached.
    :param number: 0 unless you've got more than one FaderPort attached.
                   In which case 0 is the first, 1 is the second etc
    :return: Port name or None
    """
    outs = [i for i in mido.get_output_names() if i.lower().startswith('faderport')]
    if 0 <= number < len(outs):
        return outs[number]
    else:
        return None


class TestFaderPort(FaderPort):
    """
    A class for testing the FaderPort functionality and demonstrating
    some of the possibilities.
    """

    def __init__(self):
        super().__init__()
        self._left_shift = False
        self._right_shift = False
        self.cycling = False
        self.should_exit = False

    @property
    def shift(self):
        return self._shift

    def on_open(self):
        print('FaderPort opened!!')

    def on_close(self):
        print('FaderPort closing...')

    def on_rotary(self, direction):
        print(f"Pan turned {'clockwise' if direction > 0 else 'anti-clockwise'}.")
        if self.shift:
            if direction > 0:
                if self.fader < 1023:
                    self.fader += 1
            else:
                self.fader -= 1

    def on_button(self, button, state):
        print(f"Button: {button.name} {'pressed' if state else 'released'}")
        if button.name == 'Left_Shift':
            self._left_shift = state
        if button.name == 'Right_Shift':
            self._right_shift = state
        if button.name == 'Off' and not state:
            self.should_exit = True
        # if not self.cycling:
        #     if state:
        #         self.light_on(button)
        #     else:
        #         self.light_off(button)

    def on_fader_touch(self, state):
        # print(f"Fader: {'touched' if state else 'released'}")
        pass

    def on_fader(self, pitch, channel):
        # print(f"Fader {channel}: {self._fader[channel]}")
        pass

def consume(iterator, n):  # Copied consume From the itertool docs
    """Advance the iterator n-steps ahead. If n is none, consume entirely."""
    # Use functions that consume iterators at C speed.
    if n is None:
        # feed the entire iterator into a zero-length deque
        collections.deque(iterator, maxlen=0)
    else:
        # advance to the empty slice starting at position n
        next(islice(iterator, n, n), None)


def test():
    with TestFaderPort() as f:
        f.countdown()
        f.fader = 1023
        f.snake()
        f.fader = 512
        f.blink()
        f.fader = 128
        f.chase(num_lights=3)
        f.fader = 0
        print('Try the buttons, the rotary and the fader. The "Off" '
              'button will exit.')
        while not f.should_exit:
            time.sleep(1)


if __name__ == '__main__':
    test()
