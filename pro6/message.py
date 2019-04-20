from enum import Enum
from pro6.filter import Filter
import time
import logging


class Message:

    logger = logging.getLogger(__name__)

    class Kind(Enum):
        ACTION = 0
        EVENT = 1
        ERROR = 2

    def __init__(self, message_content=None, kind=None, source=None):
        self._message = message_content

        if source is None:
            self._source = 'Undef'
        else:
            self._source = source

        self._timestamp = time.monotonic()
        self._kind = None  # Initialize it
        self.set_message_kind(kind)  # pass the argument we were passed

        if self._kind is self.Kind.ACTION:
            Filter.normalize(self._message)

    @property
    def error(self):
        if 'error' in self._message:
            return self._message['error']
        else:
            return None

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def source(self):
        return self._source

    @property
    def kind(self):
        return self._kind

    @property
    def name(self):
        if self._kind is self.Kind.ACTION:
            return self._message['action']
        elif self._kind is self.Kind.EVENT:
            return self._message['event']
        elif self._kind is self.Kind.ERROR:
            return self._message['error']

    def __getitem__(self, key):
        return self._message.get(key, None)

    def __str__(self):
        return str(self._message)

    def set_message_kind(self, kind):
        if kind is not None:
            self._kind = kind
        else:
            # try to extract the message kind from the message itself
            if 'action' in self._message:
                self._kind = self.Kind.ACTION
                Filter.normalize(self._message)
            elif 'event' in self._message:
                self._kind = self.Kind.EVENT

        if self._kind is None:
            raise ValueError('Unknown or unspecified message kind. Must be ACTION or EVENT.')
