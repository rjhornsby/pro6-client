# from collections import OrderedDict
import logging
from marker.table import MarkerTable
from marker.timecode import Timecode


class Filter:
    logger = logging.getLogger(__name__)

    # Fix the garbage nonsense where the same message is sent
    # different ways depending on the endpoint.
    @staticmethod
    def normalize(payload):
        if 'acn' in payload:
            payload['action'] = payload.pop('acn')
        if 'err' in payload:
            payload['error'] = payload.pop('err')
        if 'authenticated' in payload:
            payload['authenticated'] = (payload['authenticated'] == 1)
        if 'ath' in payload:
            payload['authenticated'] = payload.pop('ath')

        if 'action' in payload:
            Filter.process_action(payload)

    @staticmethod
    def process_action(payload):
        if payload['action'] == 'ath':
            # rewrite the action so it's consistent across WS service types
            payload['action'] = 'authenticate'
        if payload['action'] == 'csn':
            payload['slideNotes'] = payload.pop('txt')
            Filter.decode_notes(payload)
        if payload['action'] == 'vid':
            if payload['txt'] == '': return
            # ProPresenter sends DF timecodes
            payload['timecode'] = Timecode.from_str(payload.pop('txt'), df=True)

    # take the base64 encoded slide notes and convert them to a python data
    # object
    @staticmethod
    def decode_notes(slide):
        if slide['slideNotes'] == '':
            slide['markers'] = None
        else:
            slide['markers'] = MarkerTable(slide['slideNotes'])
            # decoded = Filter.decode_base64(slide['slideNotes'])
            # data = Filter.markers_to_data(decoded)
            # slide['segment_markers'] = data
        del slide['slideNotes']

    # @staticmethod
    # def decode_base64(s):
    #     # TODO: Make this check to ensure 's' is a base64 encoded string
    #     try:
    #         decoded_string = base64.b64decode(s).decode(encoding='utf-16')
    #         return decoded_string  # bytes to string
    #     except Exception as e:
    #         Filter.logger.error("Unable to decode base64 string %s" % e)
    #         return ''
    #
    # @staticmethod
    # def markers_to_data(markers):
    #     if not markers: return None
    #
    #     # Premiere's format:
    #     # Marker Name	    Description	In	Out	Duration	Marker Type
    #     # countdown		control_data    00;00;00;00	00;00;00;00	00;00;00;00	Comment
    #     # Note the two tabs after the name
    #
    #     data = OrderedDict()
    #     for line in markers.split("\n"):
    #         if not line or line.startswith('Marker Name'): continue
    #         Filter.logger.debug(line)
    #         (marker_name, control_data, in_point, out_point, _) = line.split("\t", 4)
    #         data[Filter.str_to_time(in_point.replace(';', ':'))] = {
    #             'in': Filter.str_to_time(in_point.replace(';', ':')),
    #             'out': Filter.str_to_time(out_point.replace(';', ':')),
    #             'name': marker_name,
    #             'control_data': Filter.from_json(control_data)
    #         }
    #     Filter.set_out_points(data)
    #     return data
    #
    # @staticmethod
    # def set_out_points(data):
    #     # The out point of the current segment is the in point of the
    #     # _next_ segment.
    #     for idx, in_point in enumerate(data):
    #         marker = data[in_point]
    #         if marker['in'] == marker['out'] and idx < len(data):
    #             marker['out'] = list(data.values())[idx+1]['in']
    #
    # @staticmethod
    # def from_json(json_str):
    #     try:
    #         return json.JSONDecoder().decode(json_str)
    #     except json.JSONDecodeError as e:
    #         Filter.logger.error('Cannot process control data: %s', e.msg)
    #         return None

    # @staticmethod
    # def note_text_to_data(notes):
    #     if notes == '':
    #         return None
    #
    #     data = OrderedDict()
    #     for line in notes.split("\n"):
    #         if not line == '':  # ignore blank lines
    #             (in_point, out_point, clip_name) = line.split("\t")
    #             data[Filter.str_to_time(in_point.replace(';', ':'))] = {
    #                 'in': Filter.str_to_time(in_point.replace(';', ':')),
    #                 'out': Filter.str_to_time(out_point.replace(';', ':')),
    #                 'name': clip_name
    #             }
    #     return data

    # @staticmethod
    # def str_to_time(str_time):
    #     if str_time == '--:--:--':
    #         return datetime.timedelta(hours=0, minutes=0, seconds=0)
    #     h, m, s, *_ = str_time.split(':', 3)
    #     return datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))
