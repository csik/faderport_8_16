from faderport import TestFaderPort
import mido
f = TestFaderPort()
f.open()
from scribble import *

SCREENS = [None]*8
for i in range(0,8):
    SCREENS[i]=Screen(f, i)

def randomfades():
    while(1):
    for i in range(0,8):
        value = random.randint(-8192,8191)
        f.fader = (value,i)
    time.sleep(random.random()*1)

def test_scribbles():
    for i in range(0,8):
        SCREEN[i].set_template(i)
        SCREEN[i].load_line('CBGB',0)
        SCREEN[i].load_line('nice',1)
        SCREEN[i].load_line('easy',2)


if __name__ == "main":
    test_scribbles()
    randomfades()


