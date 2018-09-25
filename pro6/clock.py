# Keep track of the current Pro6 state
import logging
from pro6.message import Message
from lib.observer import Notifier


class Clock(Notifier):
    def __init__(self, message_queue=None):
        self._ready = False
        self.message_queue = message_queue

        # self._slide_index = slide_index
        # self._presentation = presentation

        self._video_total_duration = None
        self._video_duration_remaining = None  # Will come from WS vid pro6
        self._segment_markers = None
        self._current_segment = None

        # self._presentation_updated()

    # TODO: rework these *updated methods to use an observer pattern
    def _clock_updated(self):

        if self._segment_markers is None:
            return

        event = None

        if self._current_segment is None:
            self._find_current_segment()
            # event = Message(message_content={'event': 'segment_change', 'segment': self._current_segment})
        else:
            # Update segment information
            pos = self.current_video_position
            if not (self._current_segment['in'] <= pos <= self._current_segment['out']):
                self._find_current_segment()
                # event = Message(message_content={'event': 'segment_change', 'segment': self._current_segment})
                logging.info("New segment: %s" % self._current_segment)

        if event is not None:
            self.message_queue.put(event)

    def _find_current_segment(self):
        pos = self.current_video_position
        for segment in self._segment_markers.values():
            if segment['in'] <= pos <= segment['out']:
                self._current_segment = segment
                break
        else:
            # last
            self._current_segment = self._segment_markers[next(reversed(self._segment_markers))]

        self._check_ready()

    def new_slide(self, segment_markers):
        self.reset()
        if segment_markers is None:
            logging.info('No segment data for slide')
            return

        self._segment_markers = segment_markers
        self._video_total_duration = next(reversed(self._segment_markers.values()))['out']

        self._check_ready()

    def _check_ready(self):
        if self._video_duration_remaining is None:
            self._ready = False
            return

        if self._segment_markers is None:
            self._ready = False
            return

        if self._current_segment is None:
            self._ready = False
            return

        if self._video_total_duration is None:
            self._ready = False
            return

        self._ready = True

    @property
    def ready(self):
        return self._ready

    @property
    def current_video_position(self):
        return self._video_total_duration - self._video_duration_remaining

    @property
    def video_duration_remaining(self): return self._video_duration_remaining

    @property
    def segment_name(self):
        if self._current_segment is None:
            return None

        return self._current_segment['name']

    @property
    def segment_time_remaining(self):
        return self._current_segment['out'] - self.current_video_position

    def reset(self):
        logging.info('Resetting clock')
        self._ready = False
        self._segment_markers = None
        self._current_segment = None
        self._video_total_duration = None

    # alias for video_duration_remaining
    def update_clock(self, new_time):
        self._video_duration_remaining = new_time
        self._clock_updated()

