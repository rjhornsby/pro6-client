import pro6
import datetime
import sys
from pro6.actor import Actor
from marker.timecode import Timecode

try:
    import RPi.GPIO as GPIO
    import neopixel
    import board
except ModuleNotFoundError:
    pass


class LED(Actor):
    PIXEL_COUNT = 10

    GREEN_TIME = Timecode.from_str('0:0:30:0')
    YELLOW_TIME = Timecode.from_str('0:0:10:0')
    RED_TIME = Timecode.from_str('0:0:5:0')

    def __init__(self):
        super().__init__(None)

        self.status = Actor.StatusEnum.STANDBY
        required_modules = ['RPi', 'neopixel', 'board']
        for mod in required_modules:
            if mod not in sys.modules:
                self.logger.warning('%s module not loaded, disabling LED', mod)
                self.disable()
                return

        # Initialize the library (must be called once before other functions).
        self.pixels = neopixel.NeoPixel(board.D18, self.PIXEL_COUNT)


    @property
    def watching(self):
        return [
            pro6.Roles.CLOCK
        ]

    def recv_notice(self, obj, role, param, value):
        if not self.enabled: return

        if type(obj) is pro6.clock.Clock:
            clock = obj
        else:
            return

        if not clock.ready: return

        if param == 'video_duration_remaining':
            if clock.control_data.get('hide_emcee_timer'): return

            if clock.block_remaining <= self.RED_TIME:
                self.red(clock.block_remaining)
            elif clock.block_remaining <= self.YELLOW_TIME:
                self.yellow(clock.block_remaining)
            elif clock.block_remaining <= self.GREEN_TIME:
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

    def yellow(self, time_remaining: Timecode):
        if not self.enabled: return
        count = int(time_remaining.to_seconds())
        self.clear()
        for i in range(count):
            self.pixels[i] = (200, 200, 0)

        self.pixels.show()

    def red(self, time_remaining: Timecode):
        if not self.enabled: return
        count = int(time_remaining.to_seconds())
        self.clear()
        for i in range(count):
            self.pixels[i] = (255, 0, 0)

        self.pixels.show()
