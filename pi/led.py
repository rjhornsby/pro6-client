import RPi.GPIO as GPIO
import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI
from lib.observer import Subscriber
import pro6
import datetime

PIXEL_COUNT = 10
SPI_PORT = 0
SPI_DEVICE = 0

class LED(Subscriber):
    def __init__(self):

        self.pixels = Adafruit_WS2801.WS2801Pixels(PIXEL_COUNT, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE), gpio=GPIO)

    def notify(self, obj, param, value):
        if type(obj) is pro6.clock.Clock:
            clock = obj
        else:
            return

        if not clock.ready: return

        if param == 'video_duration_remaining':
            if clock.segment_time_remaining <= datetime.timedelta(seconds=5):
                self.red(clock.segment_time_remaining)
            elif clock.segment_time_remaining <= datetime.timedelta(seconds=10):
                self.yellow(clock.segment_time_remaining)
            elif clock.segment_time_remaining <= datetime.timedelta(seconds=30):
                self.green()
            else:
                self.clear()

    def green(self):
        self.pixels.clear()
        for i in range(self.pixels.count()):
            self.pixels.set_pixel(i, Adafruit_WS2801.RGB_to_color(0, 255, 0))

        self.pixels.show()

    def yellow(self, time_remaining):
        count = int(time_remaining.total_seconds())
        self.pixels.clear()
        for i in range(count):
            self.pixels.set_pixel(i, Adafruit_WS2801.RGB_to_color(200, 200, 0))

        self.pixels.show()

    def red(self, time_remaining):
        count = int(time_remaining.total_seconds())
        self.pixels.clear()
        for i in range(count):
            self.pixels.set_pixel(i, Adafruit_WS2801.RGB_to_color(255, 0, 0))

        self.pixels.show()

    def clear(self):
        self.pixels.clear()
        self.pixels.show()
