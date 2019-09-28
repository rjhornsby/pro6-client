import sys
import pro6
from .lcd import LCD
from pro6.actor import Actor
from marker.timecode import Timecode
from marker.marker import Marker


class LCDScreen(Actor):

    def __init__(self, config):
        super().__init__(config)

        try:
            from . import I2C_LCD_driver
        except ModuleNotFoundError as e:
            self.logger.warning(e)
            self.logger.warning('I2C driver not loaded, disabling LCD')
            self.disable()
            return

        self._display = LCD()
        self._display.rtc_run()
        self._clock = None
        self.status = Actor.StatusEnum.ACTIVE

    def discover(self):
        pass  # noop

    @property
    def watching(self):
        return [
            pro6.Roles.CLOCK,
            pro6.Roles.DIRECTOR
        ]

    # Notices we need to handle:
    # Director:
    #   * status
    #   * stopping
    #   * slide change event
    # Clock:
    #   * status?
    #   * current_segment change
    #   * video_duration_remaining

    def recv_notice(self, obj, role, param, value):
        if self.status is Actor.StatusEnum.DISABLED:
            return

        if role is pro6.Roles.CLOCK and self._clock is not obj:
            self._clock = obj

        target = getattr(self, 'h_%s_%s' % (role.name.lower(), param), None)
        if target is None:
            self.logger.debug('No handler for %s:%s:%s', type(obj), role, param)
            return

        target(value)

    def h_director_stopping(self, value):
        if value: self.stop()

    def h_director_status(self, value):
        self._display.clear(line=4)
        if value is Actor.StatusEnum.OFFLINE:
            self._display.display_message('ProPres: offline', 4)
        elif value is Actor.StatusEnum.STANDBY:
            self._display.display_message('ProPres: ready', 4)

    def h_director_status_message(self, value: str):
        self._display.clear(line=4)
        self._display.display_message(f"ProPres: {value}"[:20], 4)

    def h_director_event(self, value):
        target = getattr(self, 'h_director_event_%s' % value['event'], None)
        if target is None:
            self.logger.info('No handler for %s:' % value['event'])
            return

        target(value)

    def h_director_event_video_advance(self, *_):
        pass  # ignore this event

    def h_director_event_slide_change(self, *_):
        self.logger.debug('slide change')

    def h_clock_tcr_negative(self, _):
        self._update_video_clocks()

    def h_clock_current_marker(self, marker: Marker):
        if marker is None:
            return
        self._display.clear()
        self.logger.debug(marker.name)
        self._display.display_message(f"{marker.name}/{marker.light_cue}", line=2)

    @staticmethod
    def _format_clock(timecode: Timecode):
        tc_str = str(timecode)
        if ';' in tc_str:
            tc_str = tc_str.split(';')[0]
        tc_ints = map(lambda s: int(s), tc_str.split(':'))

        return "{:d}:{:02d}:{:02d}".format(*tc_ints)

    def _update_video_clocks(self):
        if self._clock.tcr_negative.to_seconds() == 0:
            self._display.clear()
            return

        if not self._clock.ready: return

        self._display.display_message(f"-{LCDScreen._format_clock(self._clock.block_remaining)}", line=3, pos=12)
        self._display.display_message(f"+{LCDScreen._format_clock(self._clock.tcr)}", line=4, pos=0)
        self._display.display_message(f"-{LCDScreen._format_clock(self._clock.tcr_negative)}", line=4, pos=12)

    def stop(self):
        self._display.rtc_stop()
        self._display.clear()
        self._display.backlight(False)
