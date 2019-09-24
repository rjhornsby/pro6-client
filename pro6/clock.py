import time
from pro6 import Message
from .actor import Actor
from .director import Roles
from marker.table import MarkerTable
from marker.marker import Marker
from marker.timecode import Timecode
import typing


class Clock(Actor):

    THROTTLE_THRESHOLD:     float = 0.5
    _markers:               typing.Optional[MarkerTable]
    current_marker:         typing.Optional[Marker]

    def __init__(self):
        super().__init__(None)
        self.tcr_negative = None  # comes from pro6
        self.current_marker = None
        self._markers = None
        self._last_update = time.monotonic()

    @property
    def watching(self):
        return [
            Roles.DIRECTOR
        ]

    def recv_notice(self, obj, role, param, value):
        if type(value) is Message:
            self._process_message(value)

    def _process_message(self, message):
        if message.name == 'slide_change':
            self.new_slide(message)
        elif message.name == 'video_advance':
            self.tcr_update(message)
        else:
            self.logger.warning("Unknown message name '%s'" % message.name)

    @property
    def ready(self) -> bool:
        return self.status is Actor.StatusEnum.ACTIVE

    @property
    def total_duration(self) -> typing.Optional[Timecode]:
        if self._markers is None: return

        return self._markers.last.out_point

    @property
    def tcr(self) -> Timecode:
        return self.total_duration - self.tcr_negative

    @property
    def marker_name(self) -> typing.Optional[str]:
        return getattr(self.current_marker, 'name', None)

    @property
    def control_data(self) -> typing.Optional[dict]:
        return getattr(self.current_marker, 'control_data', None)

    @property
    def hide_led(self) -> bool:
        return self.control_data.get('hide_emcee_timer', False)

    @property
    def block_remaining(self) -> Timecode:
        # FIXME: "current_marker" is not correct here
        return self.current_marker.out_point - self.tcr

    def new_slide(self, message):
        self.reset()
        if message['markers'] is None:
            self.logger.info('No segment data for slide')
            return

        self._markers = message['markers']
        self._update_status()

    def reset(self):
        self.logger.info('Resetting clock')
        self.current_marker = None
        self._markers = None
        self._update_status()

    # alias for video_duration_remaining
    def tcr_update(self, message):
        if self._markers is None: return

        # Throttle
        if message.timestamp - self._last_update < self.THROTTLE_THRESHOLD:
            self.logger.info('Throttling clock updates')
            return

        self._last_update = message.timestamp
        self.tcr_negative = message['timecode']

        # self._timecode_updated()
        if self.current_marker is None:
            self._update_current_marker()
            return

        if self._markers.find(self.tcr) is self.current_marker:
            return

        # Update segment information
        self.logger.debug("Updating marker")
        self._update_current_marker()
        self.logger.info("New marker: %s" % self.current_marker.name)

    def _update_status(self):
        self.logger.debug('updating status')
        if self.tcr_negative is None:
            self.status = Actor.StatusEnum.OFFLINE
            return

        if self._markers is None:
            self.status = Actor.StatusEnum.OFFLINE
            return

        if self.current_marker is None:
            self.status = Actor.StatusEnum.OFFLINE
            return

        if self.total_duration is None:
            self.status = Actor.StatusEnum.OFFLINE
            return

        self.status = Actor.StatusEnum.ACTIVE

    # def _timecode_updated(self):
    #     if self.current_marker is None:
    #         self._update_current_marker()
    #     else:
    #         # Update segment information
    #         if self._markers.find(self.current_timecode) is not self.current_marker:
    #             self.logger.debug("Updating marker")
    #             self._update_current_marker()
    #             self.logger.info("New marker: %s" % self.current_marker)

    def _update_current_marker(self):
        self.current_marker = self._markers.find(self.tcr)
        self._update_status()

