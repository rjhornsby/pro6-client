import logging
import board
from lib.observer import Subscriber
import pro6
import datetime
import sys

try:
    import RPi.GPIO as GPIO
    import neopixel
except ModuleNotFoundError:
    logging.warning('Unable to load modules for LED support')

PIXEL_COUNT = 10


class LED(Subscriber):
    def __init__(self):

        self._disabled = False

        if 'RPi' not in sys.modules:
            logging.warning('RPi module not loaded, disabling LED')
            self._disabled = True
            return

        if 'neopixel' not in sys.modules:
            logging.warning('neopixel module not loaded, disabling LED')
            self._disabled = True
            return

        # Initialize the library (must be called once before other functions).
        self.pixels = neopixel.NeoPixel(board.D18, PIXEL_COUNT)

    def notify(self, obj, param, value):
        if self._disabled: return

        if type(obj) is pro6.clock.Clock:
            clock = obj
        else:
            return

        if not clock.ready: return

        if param == 'video_duration_remaining':
            if clock.hide_led: return

            if clock.segment_time_remaining <= datetime.timedelta(seconds=5):
                self.red(clock.segment_time_remaining)
            elif clock.segment_time_remaining <= datetime.timedelta(seconds=10):
                self.yellow(clock.segment_time_remaining)
            elif clock.segment_time_remaining <= datetime.timedelta(seconds=30):
                self.green()
            else:
                self.clear()

    def clear(self):
        if self._disabled: return
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def green(self):
        if self._disabled: return
        self.pixels.fill((0, 255, 0))
        self.pixels.show()

    def yellow(self, time_remaining):
        if self._disabled: return
        count = int(time_remaining.total_seconds())
        self.clear()
        for i in range(count):
            self.pixels[i] = (200, 200, 0)

        self.pixels.show()

    def red(self, time_remaining):
        if self._disabled: return
        count = int(time_remaining.total_seconds())
        self.clear()
        for i in range(count):
            self.pixels[i] = (255, 0, 0)

        self.pixels.show()
