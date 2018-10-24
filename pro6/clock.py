# Keep track of the current Pro6 state
import logging
import time
from lib.observer import Notifier
from lib.observer import Subscriber
from pro6 import Message


class Clock(Notifier, Subscriber):

    THROTTLE_THRESHOLD = 0.50

    def __init__(self):
        self.ready = False
        self.video_duration_remaining = None  # Will come from WS vid pro6
        self.current_segment = None

        self._video_total_duration = None

        self._segment_markers = None
        self._last_update = time.monotonic()

    def notify(self, obj, param, value):
        if type(value) is Message:
            message = value
        else:
            return

        if message.name == 'slide_change':
            self.new_slide(message)
        elif message.name == 'video_advance':
            self.update_timecode(message)

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
                logging.info("New segment: %s" % self.current_segment)

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
            logging.info('No segment data for slide')
            return

        self._segment_markers = message['segment_markers']
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
    def segment_time_remaining(self):
        return self.current_segment['out'] - self.current_video_position

    def reset(self):
        logging.info('Resetting timecode')
        self.ready = False
        self.current_segment = None
        self._segment_markers = None
        self._video_total_duration = None

    # alias for video_duration_remaining
    def update_timecode(self, message):
        # Throttle
        if message.timestamp - self._last_update < Clock.THROTTLE_THRESHOLD:
            logging.info('Throttling timecode updates')
            return

        self.video_duration_remaining = message['timecode']
        self._last_update = message.timestamp
        self._timecode_updated()

