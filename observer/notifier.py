import logging
import pro6.actor

class Notifier:
    logger = logging.getLogger(__name__)

    def __setattr__(self, name, value):
        super().__setattr__(name, value)

        # Ignore private class attributes
        if name[0] == '_': return

        role = getattr(self, 'role', None)

        for subscriber in getattr(self, '_subscribers', []):
            subscriber.recv_notice(self, role=role, param=name, value=value)

    def subscribe(self, obj):
        if not getattr(self, "_subscribers", None):
            self._subscribers = []
        self.logger.debug('Subscribing %s to %s', type(obj), type(self))
        self._subscribers.append(obj)
