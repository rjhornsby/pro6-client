import logging
from .resolve_marker_edl import ResolveMarkerEDL
import requests
from .timecode import Timecode
import typing


class MarkerTable:

    logger = logging.getLogger(__name__)

    _cached_marker: typing.Optional[ResolveMarkerEDL]
    _markers:       typing.List[ResolveMarkerEDL]

    def __init__(self, location):
        self._headers = {}
        self._markers = []

        if location is None:
            self.logger.error('No location provided, cannot retrieve marker data')
            return

        self._cached_marker = None
        self.import_markers(location)
        self.set_out_points()
        self.logger.info(f"video duration: {self.last.out_point} / {self.last.duration}")

    def import_markers(self, location: str):
        content = self.from_url(location)

        # TODO: for now, just process this as Resolve Marker EDL
        self._headers, self._markers = ResolveMarkerEDL.parse(content)
        # sorted_list = sorted(self._markers)
        self.logger.debug(f"Found {len(self._markers)} markers")

    def set_out_points(self):
        for idx, marker in enumerate(self._markers):
            duration = int(marker.remarks.get('D', None))
            if duration > 1:
                marker.out_point = marker.in_point + Timecode(duration)
            else:
                if int(marker.out_point - marker.in_point) <= 1 and idx < len(self._markers):
                    # the next marker's in_point is our out_point
                    marker.out_point = self._markers[idx + 1].in_point

    def __getitem__(self, in_point: Timecode):
        return self.find(in_point)

    def __bool__(self):
        return len(self._markers) > 0

    def find(self, timecode: Timecode) -> typing.Optional[ResolveMarkerEDL]:
        if self._cached_marker is not None:
            if timecode in self._cached_marker: return self._cached_marker

        try:
            target_marker = [marker for marker in self._markers if timecode in marker][-1]
        except IndexError:
            target_marker = self.last

        self._cached_marker = target_marker
        return self._cached_marker

    def playing_list(self, url):
        pass

    def from_url(self, url) -> typing.Optional[str]:
        try:
            self.logger.info(f"Retrieving markers from {url}")
            with requests.get(url) as response:
                return response.content.decode()
        except requests.exceptions.HTTPError as e:
            MarkerTable.logger.warning(e)

        return None

    @property
    def dropframe(self) -> bool:
        return True if self._headers.get('FCM') == 'DROP FRAME' else False

    @property
    def list(self) -> list:
        return self._markers

    @property
    def first(self) -> typing.Optional[ResolveMarkerEDL]:
        try:
            return self._markers[0]
        except IndexError:
            return None

    @property
    def last(self) -> typing.Optional[ResolveMarkerEDL]:
        try:
            return self._markers[-1]
        except IndexError:
            return None
