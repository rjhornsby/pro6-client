from enum import Enum
import logging
from observer import Subscriber, Notifier


class Actor(Subscriber, Notifier):
    class StatusEnum(Enum):
        OFFLINE = 0
        STANDBY = 1
        ACTIVE = 2
        DISABLED = 255

    logger = logging.getLogger(__name__)

    def __init__(self, config):
        self._status = self.StatusEnum.OFFLINE
        self._endpoint = None
        self._discovered = False
        self.config = config
        self._role = None

        if self.config:
            if self.config.get('disabled', None):
                self.disable()

    @property
    def enabled(self):
        return self._status is not self.StatusEnum.DISABLED

    def enable(self):
        if self._status is self.StatusEnum.DISABLED:
            self._status = self.StatusEnum.OFFLINE

    def disable(self):
        self._status = self.StatusEnum.DISABLED

    @property
    def role(self):
        return self._role

    def assign_role(self, role):
        if self._role is None:
            self._role = role

    @property
    def watching(self):
        return []

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, new_status):
        if self._status is not new_status:
            self.logger.debug('Setting new status %s' % new_status)
            self._status = new_status

    @property
    def discovered(self):
        return self._discovered

    @discovered.setter
    def discovered(self, state):
        if self._discovered is not state:
            self._discovered = state

    @property
    def endpoint(self):
        return self._endpoint

    @endpoint.setter
    def endpoint(self, new_endpoint):
        if self._endpoint is not new_endpoint:
            self._endpoint = new_endpoint

    ####

    def discover(self):
        if not self.enabled:
            self.logger.info('%s disabled, ignoring discovery' % __name__)
            return
        raise NotImplementedError

    def recv_notice(self, *args):
        if not self.enabled:
            self.logger.debug('%s disabled, ignoring notice' % __name__)
            return
        raise NotImplementedError
