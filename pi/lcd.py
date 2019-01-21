import time
import datetime
from . import I2C_LCD_driver
from lib.observer import Subscriber
import pro6
import threading

class LCD(Subscriber):
    def __init__(self):

        self._display = I2C_LCD_driver.lcd()
        self._message_line = None
        self._segment_name = None
        self._wait_chars = '._'
        self._wait_char_idx = 0
        self.stopping = False
        self._t = None
        self._t_lock = threading.Lock()
        self._curr_date_str = None
        self._curr_date = datetime.date.today()
        self.clear()

    def notify(self, obj, param, value):
        if param == 'ready':
            self._reset()

            if value is False:
                self.display_message('Waiting for', 3)
                self.display_message('ProPresenter', 4)

        if type(obj) is pro6.clock.Clock:
            clock = obj
        else:
            return

        if not clock.ready:
            return

        if self._segment_name is None or param == 'current_segment':
            self._show_segment(clock.segment_name)
            self._segment_name = clock.segment_name
        elif param == 'video_duration_remaining':
            self._update_video_clocks(clock)

    def rtc_run(self):
        self._t = threading.Thread(target=self._rtc_loop)
        self._t.start()
        self._t.join(2.0)

    def rtc_stop(self):
        self.stopping = True

    def _rtc_loop(self):
        while not self.stopping:
            try:
                if self._message_line is not 1:
                    with self._t_lock:
                        if self.date_as_string():
                            self._display.lcd_display_string(self._curr_date_str, 1, 0)
                        self._display.lcd_display_string(time.strftime("%H:%M:%S"), 1, 12)
                    time.sleep(1)
            except KeyboardInterrupt:
                self.rtc_stop()

    def date_as_string(self):

        updated = False
        if datetime.date.today() > self._curr_date:
            updated = True
            self._curr_date = datetime.date.today()
            # python uses a zero-based week number, calendars generally use one-based.
            week = int(time.strftime('%U')) + 1

            # Use the Sunday week number, not Saturday. If today is Saturday,
            # "cheat" and use the next week.
            if time.strftime('%w') == '6':
                week += 1

            day = time.strftime("%a")[0:2]

            # zero-pad the week number
            week_str = str(week).zfill(2)
            month = time.strftime("%b")[0:2]

            self._curr_date_str = time.strftime("Wk{} {}%d{}").format(week_str, day, month)

        return updated

    def clear(self):
        with self._t_lock:

            self._display.lcd_write(0x01)
            # Force the RTC loop to redraw the date
            self._curr_date = datetime.date(1980, 1, 1)

    def display_message(self, message_str, lcd_line=4):
        self._message_line = lcd_line
        with self._t_lock:
            self._display.lcd_display_string(message_str, line=lcd_line, pos=0)

    def clear_message(self):
        with self._t_lock:
            self._display.lcd_display_string(' ' * 20, line=self._message_line, pos=0)

    def _update_video_clocks(self, clock):
        with self._t_lock:
            self._display.lcd_display_string("-%s" % str(clock.segment_time_remaining), line=3, pos=12)
            self._display.lcd_display_string("+%s" % str(clock.current_video_position), line=4, pos=0)
            self._display.lcd_display_string("-%s" % str(clock.video_duration_remaining), line=4, pos=12)

    def _show_segment(self, name=None):
        self.clear()
        with self._t_lock:
            self._display.lcd_display_string("%s" % name, line=2)

    def _reset(self):
        self.clear()
        self._segment_name = None
        self._message_line = None
