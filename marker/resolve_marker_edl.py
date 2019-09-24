from .marker import Marker
import re
import json

# Sequence FCM can be modified by using "Get Clip Info", and change the separator from ; to :.
# ; = Drop Frame, : = Non Drop Frame.
# Frame Code Mode
#
# TITLE: 2019W35_KON_IMatter_3_Message
# FCM: NON-DROP FRAME
#
# 001  001      V     C        00:00:00:00 00:00:00:01 00:00:00:00 00:00:00:01
# {"light_cue":"38.1"} |C:ResolveColorBlue |M:countdown |D:1
#
# 002  001      V     C        00:05:06:06 00:05:06:07 00:05:06:06 00:05:06:07
# {"light_cue":"38.1"} |C:ResolveColorBlue |M:sm_talk |D:1
# D = duration (in frames)

# There are different kinds of Resolve EDL files. One of them specifically
# is the Resolve Marker EDL.

class ResolveMarkerEDL(Marker):
    def __init__(self, timecode, remarks):
        super().__init__()
        self._parse_marker(timecode, remarks)

    @property
    def name(self):
        # if a name is explicitly set, return that
        if self._name:
            return self._name

        # otherwise try to retrieve the name from the remarks dictionary
        if self._remarks['M']:
            return self._remarks['M']

        return None

    @staticmethod
    def parse(content):

        header_re = re.compile("[A-Z]+:")
        marker_re = re.compile("\d{3}\s+\d{3}\s+")

        lines = content.splitlines()

        headers = {}
        markers = []

        while lines:
            line = lines.pop(0)
            if not line: continue

            if header_re.match(line):
                key, value = ResolveMarkerEDL._header(line)
                headers[key] = value
            elif marker_re.match(line):
                remarks = lines.pop(0)
                marker = ResolveMarkerEDL(timecode=line, remarks=remarks)
                markers.append(marker)

        return headers, markers

    def _parse_marker(self, edit_decision, remarks):
        self._parse_edit_decision(edit_decision)
        self._parse_remarks(remarks)

    def _parse_edit_decision(self, edit_decision):
        # elements = edit_decision.split()
        edit_id, reel, _track_type, _transition, in_point, out_point, *_ = edit_decision.split()
        self._id = edit_id
        self.in_point = in_point
        self.out_point = out_point

    def _parse_remarks(self, remarks):
        rem_list = remarks.split('|')
        self._control_data = json.loads(rem_list[0])
        self._remarks = dict(item.split(':', 1) for item in rem_list[1:])
        # remove any excess whitespace
        self._remarks.update((k, v.strip()) for k, v in self._remarks.items())

    @staticmethod
    def _header(header):
        (key, value) = header.split(':', 1)
        return key.strip(), value.strip()

