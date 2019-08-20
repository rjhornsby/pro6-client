import sys
import pro6
from .lcd import LCD
from pro6.actor import Actor
# from pro6.director import Roles
import time

try:
    from . import I2C_LCD_driver
except ModuleNotFoundError:
    pass


class LCDScreen(Actor):

    def __init__(self, config):
        super().__init__(config)

        if 'pi.I2C_LCD_driver' not in sys.modules:
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

    def h_director_event(self, value):
        pass

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

