import board
import pro6
import datetime
import sys
from pro6.actor import Actor

try:
    import RPi.GPIO as GPIO
    import neopixel
except ModuleNotFoundError:
    pass

PIXEL_COUNT = 10


class LED(Actor):

    def __init__(self):
        super().__init__(None)

        self.status = Actor.StatusEnum.STANDBY

        if 'RPi' not in sys.modules:
            self.logger.warning('RPi module not loaded, disabling LED')
            self.disable()
            return

        if 'neopixel' not in sys.modules:
            self.logger.warning('neopixel module not loaded, disabling LED')
            self.disable()
            return

        # Initialize the library (must be called once before other functions).
        self.pixels = neopixel.NeoPixel(board.D18, PIXEL_COUNT)

    @property
    def watching(self):
        return [
            pro6.Roles.CLOCK
        ]

    def recv_notice(self, obj, role, param, value):
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
        if not self.enabled: return
        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def green(self):
        if not self.enabled: return
        self.pixels.fill((0, 255, 0))
        self.pixels.show()

    def yellow(self, time_remaining):
        if not self.enabled: return
        count = int(time_remaining.total_seconds())
        self.clear()
        for i in range(count):
            self.pixels[i] = (200, 200, 0)

        self.pixels.show()

    def red(self, time_remaining):
        if not self.enabled: return
        count = int(time_remaining.total_seconds())
        self.clear()
        for i in range(count):
            self.pixels[i] = (255, 0, 0)

        self.pixels.show()
