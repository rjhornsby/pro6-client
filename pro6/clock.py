import time
from pro6 import Message
from .actor import Actor
from .director import Roles


class Clock(Actor):

    THROTTLE_THRESHOLD = 1.0

    def __init__(self):
        super().__init__(None)
        self.video_duration_remaining = None  # Will come from WS vid pro6
        self.current_segment = None

        self._video_duration_total = None
        self._segment_markers = None
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
            self.update_timecode(message)
        else:
            self.logger.warning("Unknown message name '%s'" % message.name)

    def _timecode_updated(self):
        if self._segment_markers is None:
            return

        if self.current_segment is None:
            self._update_current_segment()
        else:
            # Update segment information
            pos = self.current_video_position
            if not (self.current_segment['in'] <= pos <= self.current_segment['out']):
                self._update_current_segment()
                self.logger.info("New segment: %s" % self.current_segment)

    def _update_current_segment(self):
        pos = self.current_video_position
        for segment in self._segment_markers.values():
            if segment['in'] <= pos <= segment['out']:
                self.current_segment = segment
                break
        else:
            # last
            self.current_segment = self._segment_markers[next(reversed(self._segment_markers))]

        self._update_status()

    def new_slide(self, message):
        self.reset()
        if message['segment_markers'] is None:
            self.logger.info('No segment data for slide')
            return

        self._segment_markers = message['segment_markers']
        # last
        self._video_duration_total = next(reversed(self._segment_markers.values()))['out']

        self._update_status()

    def _update_status(self):
        if self.video_duration_remaining is None:
            self.status = Actor.StatusEnum.OFFLINE
            return

        if self._segment_markers is None:
            self.status = Actor.StatusEnum.OFFLINE
            return

        if self.current_segment is None:
            self.status = Actor.StatusEnum.OFFLINE
            return

        if self._video_duration_total is None:
            self.status = Actor.StatusEnum.OFFLINE
            return

        self.status = Actor.StatusEnum.ACTIVE

    @property
    def ready(self):
        return self.status is Actor.StatusEnum.ACTIVE


    @property
    def current_video_position(self):
        return self._video_duration_total - self.video_duration_remaining

    @property
    def segment_name(self):
        if self.current_segment is None:
            return None

        return self.current_segment['name']

    @property
    def control_data(self):
        if self.current_segment is None:
            return None
        return self.current_segment['control_data']

    @property
    def cuelist_id(self):
        if self.control_data is None: return None

        return self.control_data.split(':')[0]

    @property
    def hide_led(self):
        return '!' in self.control_data

    @property
    def segment_time_remaining(self):
        return self.current_segment['out'] - self.current_video_position

    def reset(self):
        self.logger.info('Resetting timecode')
        self.status = Actor.StatusEnum.STANDBY
        self.current_segment = None
        self._segment_markers = None
        self._video_duration_total = None

    # alias for video_duration_remaining
    def update_timecode(self, message):
        # Throttle
        if message.timestamp - self._last_update < self.THROTTLE_THRESHOLD:
            self.logger.info('Throttling timecode updates')
            return

        self.video_duration_remaining = message['timecode']
        self._last_update = message.timestamp
        self._timecode_updated()

