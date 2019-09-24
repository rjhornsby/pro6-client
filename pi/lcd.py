import time
import threading
import logging
import sys

try:
    from . import I2C_LCD_driver
except ModuleNotFoundError:
    pass


class LCD:

    LINE_WIDTH = 20

    logger = logging.getLogger(__name__)

    def __init__(self):
        # self._disabled = False

        if 'pi.I2C_LCD_driver' not in sys.modules:
            self.logger.warning('I2C driver not loaded, disabling LCD')
            # self._disabled = True
            return

        self._display = I2C_LCD_driver.lcd()
        self._message_line = None
        self._segment_name = None
        self._wait_chars = '._'
        self._wait_char_idx = 0
        self._stopping = False
        self._t = None
        self._t_lock = threading.Lock()
        self._write_full_rtc = True
        self.clear()

    # def recv_notice(self, obj, param, value):
    #     if self._disabled: return
    #
    #     if param == 'ready':
    #         self._reset()
    #
    #     if type(obj) is pro6.clock.Clock:
    #         clock = obj
    #     else:
    #         return
    #
    #     if not clock.ready:
    #         return
    #
    #     if self._segment_name is None or param == 'current_segment':
    #         self._show_segment(clock.segment_name, clock.cuelist_id)
    #         self._segment_name = clock.segment_name
    #     elif param == 'video_duration_remaining':
    #         self._update_video_clocks(clock)

    def backlight(self, state):
        self._display.backlight(int(state))

    def rtc_run(self):
        # if self._disabled: return
        self._stopping = False
        self._t = threading.Thread(target=self._rtc_loop)
        self._t.start()
        self._t.join(2.0)

    def rtc_stop(self):
        # if self._disabled: return
        self._stopping = True

    def _rtc_loop(self):
        while not self._stopping:
            with self._t_lock:
                self._display.lcd_display_string(self._rtc_str(), 1, 0)
            time.sleep(0.5)

    def _rtc_str(self):
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

        date_str = time.strftime("Wk{} {}%d{}").format(week_str, day, month)
        time_str = time.strftime("%H:%M:%S")

        # Ensure we return exactly a <LINE_WIDTH> length string
        rtc_str = str.format("{} {}", date_str, time_str)
        return rtc_str.rjust(self.LINE_WIDTH, ' ')[:self.LINE_WIDTH]

    def clear(self, line: int = None):
        # FIXME: this gets called too often, and wipes out the block name from the display
        # when writing the timecode clocks
        with self._t_lock:
            if line is None:
                self._display.lcd_write(0x01)
            else:
                self._display.lcd_display_string(' '.join([''] * 20), line=line)

    def display_message(self, message_str: str, line: int = 4, pos: int = 0):
        # if self._disabled: return
        # self._message_line = lcd_line
        with self._t_lock:
            self._display.lcd_display_string(message_str, line=line, pos=pos)

    # def clear_message(self):
    #     if self._disabled: return
    #     with self._t_lock:
    #         self._display.lcd_display_string(' ' * self.LINE_WIDTH, line=self._message_line, pos=0)
    #
    # def _update_video_clocks(self, clock):
    #     with self._t_lock:
    #         self._display.lcd_display_string("-%s" % str(clock.segment_time_remaining), line=3, pos=12)
    #         self._display.lcd_display_string("+%s" % str(clock.current_video_position), line=4, pos=0)
    #         self._display.lcd_display_string("-%s" % str(clock.video_duration_remaining), line=4, pos=12)
    #
    # def _show_segment(self, name=None, cuelist_id=None):
    #     self.clear()
    #     with self._t_lock:
    #         self._display.lcd_display_string("%s/%s" % (name, cuelist_id), line=2)

