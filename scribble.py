# Code for sending messages to scribble strips
from typing import NamedTuple
from faderport import FaderPort
class Template(NamedTuple):
    number: int
    code: int
    lines: int
    description: str

TEMPLATES = [
                Template(number=0, code=0x00, lines=3,  description=
                         """Default Mode
                         3 lines of text* and value bar
                         Line 0 : Small min. 7 chars
                         Line 1 : Small min. 7 chars
                         Line 2 : Large min. 4 chars"""),

                Template(number=1 , code=0x01, lines=3, description=
                        """Alternative Default Mode
                        3 lines of text* and value bar:
                        Line 0 : Large min. 4 chars
                        Line 1 : Small min. 7 chars
                        Line 2 : Small min. 7 chars OHL"""),

                Template(number=2, code= 0x02, lines=4, description=
                        """Small Text Mode
                        4 lines of text* and value bar:
                        Line 0 :Small min. 7 chars
                        Line 1 :Small min. 7 chars
                        Line 2 :Small min. 7 chars
                        Line 3 :Small min. 7 chars"""),

                Template(number=3, code= 0x03, lines=2, description=
                        """Large Text Mode
                        2 lines of text* and value bar:
                        Line 0 :Large min. 4 chars
                        Line 1 :Large min. 4 chars"""),

                Template(number=4, code= 0x04, lines=2, description=
                        """Large Text Metering Mode
                        2 lines of text*, meters
                        and value bar:
                        Line 0 : Large min. 2 chars
                        Line 1 : Large min. 2 chars"""),

                Template(number=5, code= 0x05, lines=3, description=
                        """Default Text Metering Mode
                        3 lines of text*, meters and value bar:
                        Line 0 : Small min. 4 chars
                        Line 1 : Small min. 4 chars
                        Line 2 : Large min. 2 chars"""),

                Template(number=6, code= 0x06, lines=3, description=
                        """Mixed Text Mode
                        3 lines of text*, and value bar:
                        Line 0 : Small min. 7 chars
                        Line 1 : Large min. 4 chars
                        Line 2 : Small min. 7 chars"""),

                Template(number=7, code= 0x07, lines=3, description=
                        """Alternative Text Metering Mode
                        3 lines of text*, meters and value bar:
                        Line 0 : Large min. 2 chars
                        Line 1 : Small min. 4 chars
                        Line 2 : Small min. 4 chars"""),

                Template(number=8, code= 0x08, lines=3, description=
                        """Mixed Text Metering Mode
                        3 lines of text*, meters and value bar:
                        Line 0 : Small min. 4 chars
                        Line 1 : Large min. 2 chars
                        Line 2 : Small min. 4 chars"""),

                Template(number=9, code= 0x09, lines=7, description=
                        """Menu Mode
                        Line 0 : Small min. 7 chars
                        Line 1 : Small min. 7 chars
                        Line 2 : Small min. 7 chars
                        Line 3 : Small min. 7 chars
                        Line 4 : Small min. 7 chars
                        Line 5 : Small min. 7 chars
                        Line 6 : Small min. 7 chars""")]

_template_from_number_ = {x.number: x for x in TEMPLATES}

def template_from_number(number: int) -> Template:
     """
     Given a button name return the corresponding Button
     :param name: The name of a button
     :return: a Button
     """
     return _template_from_number_.get(number, None)

activescreen = 0 #This keeps track to make sure you have prepared the screen for messages

class Screen:
    def __init__(self, faderport: FaderPort, scribble_id: int):
         self.id = scribble_id
         self.current_template = 0
         self.current_message = "CBGB"
         self.faderport = faderport

    def set_template(self, template: int):
        self.current_template = template

    def prep_screen(self):
        global activescreen
        msg = mido.Message('sysex')
        msg.data = bytes([0xF0, 0x00, 0x01, 0x06, 0x02, 0x13,])
        # scribble id
        msg.data += bytes([self.id])
        # redraw screen
        msg.data += bytes([self.template + 0x10]) #bit 4 (0, don't redraw, 1 redraw)
        self.faderport.outport.send(msg)
        activescreen = self.id

    def load_line(self, text: str, line_number: int, alignment: int = 0):
        global activescreen
        # make sure screen has been prepped
        if self.id != activescreen:
            self.prep_screen()
            activescreen = self.id

        msg = mido.Message('sysex')
        # pack prefix
        msg.data = bytes([0x00, 0x01, 0x06, 0x02, 0x12,])
        # scribble id
        msg.data += bytes([self.template])
        # line number
        msg.data += bytes([line_number])
        # alignment (center: 0, left: 1, right: 2)
        msg.data += bytes([aligment])
        # text
        msg.data += [ord(c) for c in text]
        f.outport.send(msg)


#msg.data += [ord(c) for c in 'CBGB']
#f.outport.send(msg)



#def send_scribble(faderport: Faderport, template:
#f.outport.send(mido.Message.from_bytes([0xF0, 0x00, 0x01, 0x06, 0x02, 0x13, 0x00, 0x12, 0xF7]))
#f.outport.send(mido.Message.from_bytes([0xF0, 0x00, 0x01, 0x06, 0x02, 0x12, 0x00, 0x00, 0x00, 0x50, 0x50, 0x50, 0x50, 0xF7]))
