import RPi.GPIO as GPIO
import time
import neopixel
import board
from lib.observer import Subscriber
import pro6
import datetime

PIXEL_COUNT = 10

class LED(Subscriber):
    def __init__(self):

        # Initialize the library (must be called once before other functions).
        self.pixels = neopixel.NeoPixel(board.D18, PIXEL_COUNT)

    def notify(self, obj, param, value):
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
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def green(self):
        self.pixels.fill((0, 255, 0))
        self.pixels.show()

    def yellow(self, time_remaining):
        count = int(time_remaining.total_seconds())
        self.clear()
        for i in range(count):
            self.pixels[i] = (200, 200, 0)

        self.pixels.show()

    def red(self, time_remaining):
        count = int(time_remaining.total_seconds())
        self.clear()
        for i in range(count):
            self.pixels[i] = (255, 0, 0)

        self.pixels.show()
