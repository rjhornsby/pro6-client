#!/usr/bin/env python3.7
import datetime
from . import I2C_LCD_driver

class LCD:
    def __init__(self):

        self._display = I2C_LCD_driver.lcd()
        self.clear()

    def clear(self):
        self._display.lcd_write(0x01)

    def show_segment(self, name=None):
        self.clear()
        self._display.lcd_display_string("CS %s" % name, line=1)

    def show_time_remaining(self, total_time_remaining=None, segment_time_remaining=None):
        self._display.lcd_display_string("-%s" % str(total_time_remaining), line=2, pos=0)
        self._display.lcd_display_string("-%s" % str(segment_time_remaining), line=2, pos=10)

    def show_time_elapsed(self, time_elapsed=None):
        self._display.lcd_display_string("+%s" % str(time_elapsed), line=3, pos=0)

    def display_message(self, message_str, lcd_line=4):
        self._display.lcd_display_string(message_str, line=lcd_line, pos=0)

if __name__ == "__main__":
    lcd = LCD()

    lcd.show_segment(name='foo!')
    lcd.show_segment_remaining(time_remaining=datetime.timedelta(hours=0, minutes=3, seconds=5))