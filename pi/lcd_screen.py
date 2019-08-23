import sys
import pro6
from .lcd import LCD
from pro6.actor import Actor


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
        self.status = Actor.StatusEnum.ACTIVE

    def discover(self):
        pass  # noop

    @property
    def watching(self):
        return [
            pro6.Roles.CLOCK,
            pro6.Roles.DIRECTOR
        ]

    def recv_notice(self, obj, role, param, value):
        self.logger.debug('Notified: (%s) %s / %s / %s' % (role, type(obj).__name__, param, value))
        if self.status is Actor.StatusEnum.DISABLED:
            return

        target = getattr(self, 'h_%s_%s' % (role.name.lower(), param), None)
        if target is None:
            self.logger.warning('No handler for %s:%s:%s', type(obj), role, param)
            return

        target(value)

    def h_director_stopping(self, value):
        if value: self.stop()

    def h_director_status(self, value):
        self._display.clear()
        if value is Actor.StatusEnum.OFFLINE:
            self._display.display_message('ProPres: offline', 4)
        elif value is Actor.StatusEnum.STANDBY:
            self._display.display_message('ProPres: ready', 4)

    def h_director_event(self, value):
        target = getattr(self, 'h_director_event_%s' % value['event'], None)
        if target is None:
            self.logger.warning('No handler for %s:' % value['event'])
            return

        target(value)

    def h_director_event_slide_change(self, metadata):
        self.logger.debug('slide change')
        self._display.clear()

    def h_clock_video_duration_remaining(self, value):
        pass

    def h_clock_current_segment(self, value):
        if value is None: return
        self._display.clear()
        self.logger.debug(value)
        self._display.display_message('%s/%s' % (value['name'], value['control_data']['light_cue']), line=2)

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

    # def h_client_message(self, param, value, *args):
    #     if param == 'stopping' and value is True:
    #         self.stop()
    #     elif param == 'p6_state':
    #         self._client_p6_state(value)
    #     elif param == 'network_up':
    #         self._client_network_state(value)
    #     else:
    #         pass
    #
    # def _client_network_state(self, value):
    #     if value:
    #         self._display.display_message('Network: up', 3)
    #     else:
    #         self._display.display_message('Network: down', 3)
    #
    # def _client_p6_state(self, value):
    #     if value == Actor.StatusEnum.OFFLINE:
    #         self._display.clear()
    #         self._display.display_message('ProPres: offline', 4)
    #     elif value == Actor.StatusEnum.STANDBY:
    #         self._display.clear()
    #         self._display.display_message('ProPres: ready', 4)
    #     elif value == Actor.StatusEnum.ACTIVE:
    #         pass

    def stop(self):
        self._display.rtc_stop()
        self._display.clear()
        self._display.backlight(False)
