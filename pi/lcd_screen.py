import logging
from lib.observer import Subscriber
from enum import Enum
from .lcd import LCD

# Screen modes
# 0 - offline, standby, waiting
# 1 - active show



class LCDScreenView(Enum):
    STANDBY = 0
    ACTIVE = 1

class LCDScreen(Subscriber):

    logger = logging.getLogger(__name__)

    def __init__(self):
        self._mode = LCDScreenView.STANDBY
        self.network_online = False

        self._display = LCD()
        self._display.rtc_run()

    def notify(self, obj, param, value):
        self.logger.debug('Notified: %s / %s / %s' % (obj, param, value))
        if param == 'stopping' and value is True:
            self.stop()

    def stop(self):
        self._display.rtc_stop()

