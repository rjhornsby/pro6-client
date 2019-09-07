# Keep track of the current Pro6 state
import logging
import time
from lib.observer import Notifier
from lib.observer import Subscriber
from pro6 import Message


class Clock(Notifier, Subscriber):
    logger = logging.getLogger(__name__)

    THROTTLE_THRESHOLD = 0.25

    def __init__(self):
        self.ready = False
        self.video_duration_remaining = None  # Will come from WS vid pro6
        self.current_segment = None

        self._video_total_duration = None
        self._segment_markers = None
        self._last_update = time.monotonic()
        self.ws_connected = False

    def notify(self, obj, param, value):
        if type(value) is Message:
            self._process_message(value)
        elif param == 'connected':
            if self.ws_connected != value:
                self.ws_connected = value
            self._check_ready()

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
            self._find_current_segment()
        else:
            # Update segment information
            pos = self.current_video_position
            if not (self.current_segment['in'] <= pos <= self.current_segment['out']):
                self._find_current_segment()
                self.logger.info("New segment: %s" % self.current_segment)

    def _find_current_segment(self):
        pos = self.current_video_position
        for segment in self._segment_markers.values():
            if segment['in'] <= pos <= segment['out']:
                self.current_segment = segment
                break
        else:
            # last
            self.current_segment = self._segment_markers[next(reversed(self._segment_markers))]

        self._check_ready()

    def new_slide(self, message):
        self.reset()
        if message['segment_markers'] is None:
            self.logger.info('No segment data for slide')
            return

        self._segment_markers = message['segment_markers']
        # last
        self._video_total_duration = next(reversed(self._segment_markers.values()))['out']

        self._check_ready()

    def _check_ready(self):
        if self.video_duration_remaining is None:
            self.ready = False
            return

        if self._segment_markers is None:
            self.ready = False
            return

        if self.current_segment is None:
            self.ready = False
            return

        if self._video_total_duration is None:
            self.ready = False
            return

        if self.ws_connected is False:
            self.ready = False
            return

        # Seems dumb, but without the 'if' python treats self.ready as if it is always being
        # set, even if the value didn't actually change. This generates a notification to all
        # observers.
        if not self.ready:
            self.ready = True

    @property
    def current_video_position(self):
        return self._video_total_duration - self.video_duration_remaining

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
        
        return self.control_data.get('light_cue', None)
    @property
    def hide_led(self):
        return '!' in self.control_data

    @property
    def segment_time_remaining(self):
        return self.current_segment['out'] - self.current_video_position

    def reset(self):
        self.logger.info('Resetting timecode')
        self.ready = False
        self.current_segment = None
        self._segment_markers = None
        self._video_total_duration = None

    # alias for video_duration_remaining
    def update_timecode(self, message):
        # Throttle
        if message.timestamp - self._last_update < Clock.THROTTLE_THRESHOLD:
            self.logger.info('Throttling timecode updates')
            return

        self.video_duration_remaining = message['timecode']
        self._last_update = message.timestamp
        self._timecode_updated()

