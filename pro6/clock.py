# Keep track of the current Pro6 state
import logging
import time
from lib.observer import Notifier


class Clock(Notifier):
    def __init__(self, message_queue=None):
        self.ready = False
        self.video_duration_remaining = None  # Will come from WS vid pro6
        self.current_segment = None

        self._message_queue = message_queue
        self._video_total_duration = None

        self._segment_markers = None
        self._last_update = time.monotonic()

    def _clock_updated(self):

        if self._segment_markers is None:
            return

        event = None

        if self.current_segment is None:
            self._find_current_segment()
        else:
            # Update segment information
            pos = self.current_video_position
            if not (self.current_segment['in'] <= pos <= self.current_segment['out']):
                self._find_current_segment()
                logging.info("New segment: %s" % self.current_segment)

        if event is not None:
            self._message_queue.put(event)

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

        # Seems dumb, but without the 'if' python
        # treats self.ready as if it is always being
        # set, even if the value didn't actually change
        if not self.ready:
            self.ready = True

    # @property
    # def ready(self):
    #     return self._ready

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
        logging.info('Resetting clock')
        self.ready = False
        self.current_segment = None
        self._segment_markers = None
        self._video_total_duration = None

    # alias for video_duration_remaining
    def update_clock(self, message):
        # Throttle
        if message.timestamp - self._last_update < 0.75:
            logging.info('Throttling clock updates')
            return

        self.video_duration_remaining = message['timecode']
        self._last_update = message.timestamp
        self._clock_updated()

