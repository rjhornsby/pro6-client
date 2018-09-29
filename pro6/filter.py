import base64
import datetime
from collections import OrderedDict
import logging

class Filter:

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
        if payload['action'] == 'ath':
            payload['action'] = 'authenticate'
        if payload['action'] == 'csn':
            payload['slideNotes'] = payload.pop('txt')
            Filter.decode_notes(payload)
        if payload['action'] == 'vid':
            if payload['txt'] == '': return
            payload['timecode'] = Filter.str_to_time(payload.pop('txt'))

    # take the base64 encoded slide notes and convert them to a python data
    # object
    @staticmethod
    def decode_notes(slide):
        if slide['slideNotes'] == '':
            slide['segment_markers'] = None
        else:
            decoded = Filter.decode_base64(slide['slideNotes'])
            data = Filter.note_text_to_data(decoded)
            slide['segment_markers'] = data
        del slide['slideNotes']

    @staticmethod
    def decode_base64(s):
        # TODO: Make this check to ensure 's' a base64 encoded string
        try:
            decoded_string = base64.b64decode(s).decode()
            return decoded_string  # bytes to string
        except Exception:
            logging.error("Unable to decode base64 string %s" % s)
            return ''

    @staticmethod
    def note_text_to_data(notes):
        if notes == '':
            return None

        data = OrderedDict()
        for line in notes.split("\n"):
            if not line == '':  # ignore blank lines
                (in_point, out_point, clip_name) = line.split("\t")
                data[Filter.str_to_time(in_point.replace(';', ':'))] = {
                    'in': Filter.str_to_time(in_point.replace(';', ':')),
                    'out': Filter.str_to_time(out_point.replace(';', ':')),
                    'name': clip_name
                }
        return data

    @staticmethod
    def str_to_time(str_time):
        h, m, s, *trash = str_time.split(':', 3)
        return datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))
