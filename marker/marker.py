import logging
from .timecode import Timecode
import typing


class Marker:

    logger = logging.getLogger(__name__)

    def __init__(self):
        self._name = None
        self._id = None
        self._in_point = None
        self._out_point = None
        self._control_data = None
        self._remarks = {}

    @property
    def name(self):
        return self._name

    @property
    def in_point(self) -> Timecode:
        return self._in_point

    @in_point.setter
    def in_point(self, timecode):
        # TODO: This isinstance logic doesn't seem like it should be here
        if isinstance(timecode, str):
            self._in_point = Timecode.from_str(timecode)
        else:
            self._in_point = timecode

    @property
    def out_point(self) -> Timecode:
        return self._out_point

    @out_point.setter
    def out_point(self, timecode):
        # TODO: This isinstance logic doesn't seem like it should be here
        if isinstance(timecode, str):
            self._out_point = Timecode.from_str(timecode)
        else:
            self._out_point = timecode

    @property
    def duration(self) -> Timecode:
        return self._out_point - self._in_point

    @property
    def control_data(self):
        return self._control_data

    @property
    def light_cue(self):
        return self._control_data.get('light_cue', None)

    @property
    def remarks(self):
        return self._remarks

    @remarks.setter
    def remarks(self, remarks):
        pass

    def __lt__(self, other):
        return self._in_point < other.in_point
