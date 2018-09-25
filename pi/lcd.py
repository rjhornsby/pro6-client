#!/usr/bin/env python3.7
import time
from . import I2C_LCD_driver
from lib.observer import Subscriber
import pro6


class LCD(Subscriber):
    def __init__(self):

        self._display = I2C_LCD_driver.lcd()
        self.clear()
        self._message_line = None
        self._segment_name = None
        self._wait_chars = '._'
        self._wait_char_idx = 0

    def notify(self, obj, param, value):
        # This clock needs to be in a thread of its own so it keeps going no matter what
        # self._display.lcd_display_string(time.strftime('%a %d %b  %H:%M:%S'), line=1, pos=0)

        # FIXME: deal with a rapid sequence of segment changes because of scrubbing
        # should probably ignore all but the last one, somehow
        # maybe don't accept notifications more than once per second?
        # maybe the clock shouldn't be allowed to push updates more than
        # once per second?

        print("notified:%s" % param)

        if param == '_ready':
            self._reset()

            if value is False:
                self.display_message('  Waiting for data')

        if type(obj) is pro6.clock.Clock:
            clock = obj
        else:
            return

        if not clock.ready:

            wait_char = self._wait_chars[self._wait_char_idx]
            self._display.lcd_display_string(wait_char, 4, 0)
            self._display.lcd_display_string(wait_char, 4, 19)
            self._wait_char_idx += 1
            if self._wait_char_idx >= len(self._wait_chars):
                self._wait_char_idx = 0
            return

        if self._segment_name is None or param == '_current_segment':
            self._segment_name = clock.segment_name

            self.clear()
            self._display.lcd_display_string(clock.segment_name[:20], line=2)
        elif param == '_video_duration_remaining':
            self._display.lcd_display_string("-%s" % str(clock.segment_time_remaining), line=3, pos=12)
            self._display.lcd_display_string("+%s" % str(clock.current_video_position), line=4, pos=0)
            self._display.lcd_display_string("-%s" % str(clock.video_duration_remaining), line=4, pos=12)

    def clear(self):
        self._display.lcd_write(0x01)

    def show_segment(self, name=None):
        self.clear()
        self._display.lcd_display_string("%s" % name, line=1)

    def show_time_remaining(self, total_time_remaining=None, segment_time_remaining=None):
        self._display.lcd_display_string("-%s" % str(total_time_remaining), line=2, pos=0)
        self._display.lcd_display_string("-%s" % str(segment_time_remaining), line=2, pos=10)

    def show_time_elapsed(self, time_elapsed=None):
        self._display.lcd_display_string("+%s" % str(time_elapsed), line=3, pos=0)

    def display_message(self, message_str, lcd_line=4):
        self._message_line = lcd_line
        self._display.lcd_display_string(message_str, line=lcd_line, pos=0)

    def clear_message(self):
        self._display.lcd_display_string(' ' * 20, line=self._message_line, pos=0)

    def _reset(self):
        self.clear()
        self._segment_name = None
        self._message_line = None