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
        # This time of day clock needs to be in a thread of its own so it keeps going no matter what
        # self._display.lcd_display_string(time.strftime('%a %d %b  %H:%M:%S'), line=1, pos=0)

        if param == 'ready':
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

        if self._segment_name is None or param == 'current_segment':
            self._show_segment(clock.segment_name)
            self._segment_name = clock.segment_name
        elif param == 'video_duration_remaining':
            self._update_video_clocks(clock)

    def clear(self):
        self._display.lcd_write(0x01)

    def display_message(self, message_str, lcd_line=4):
        self._message_line = lcd_line
        self._display.lcd_display_string(message_str, line=lcd_line, pos=0)

    def clear_message(self):
        self._display.lcd_display_string(' ' * 20, line=self._message_line, pos=0)

    def _update_video_clocks(self, clock):
        self._display.lcd_display_string("-%s" % str(clock.segment_time_remaining), line=3, pos=12)
        self._display.lcd_display_string("+%s" % str(clock.current_video_position), line=4, pos=0)
        self._display.lcd_display_string("-%s" % str(clock.video_duration_remaining), line=4, pos=12)

    def _show_segment(self, name=None):
        self.clear()
        self._display.lcd_display_string("%s" % name, line=2)

    def _reset(self):
        self.clear()
        self._segment_name = None
        self._message_line = None
