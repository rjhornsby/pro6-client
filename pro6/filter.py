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
        if payload['action'] == 'presentationCurrent':
            Filter.ungroup_slides(payload)
        if payload['action'] == 'vid':
            if payload['txt'] == '': return
            payload['timecode'] = Filter.str_to_time(payload.pop('txt'))

    # We don't care about the slide groups. They actually make things more difficult
    # because of how Pro6 handles the slides:
    # A) By default Pro6 says every slide has a slideIndex of 0.
    # B) When you get a "slide changed" message from Pro6 or ask it what is the current slide
    #    Pro6 replies with an index value accounting for all the slides regardless of group.
    # TL;DR: Sometimes Pro6 groups slides, sometimes it completely ignores the groups. This thing
    # is all over the place.
    @staticmethod
    def ungroup_slides(message):
        message['presentation']['slides'] = []
        idx = 0
        for group in message['presentation']['presentationSlideGroups']:
            for slide in group['groupSlides']:
                slide['slideIndex'] = idx
                # base64decode the slide notes while we're in the loop
                # if the decode fails, it doesn't matter
                Filter.decode_notes(slide)
                message['presentation']['slides'].append(slide)
                idx += 1
        # Remove the unneeded/now duplicate data
        del message['presentation']['presentationSlideGroups']

    # take the base64 encoded slide notes and convert them to a python data
    # object
    @staticmethod
    def decode_notes(slide):
        decoded = Filter.decode_base64(slide['slideNotes'])
        data = Filter.note_text_to_data(decoded)
        slide['segments'] = data
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
            (in_point, out_point, clip_name, duration) = line.split("\t")
            data[Filter.str_to_time(in_point)] = {
                'in': Filter.str_to_time(in_point),
                'out': Filter.str_to_time(out_point),
                'name': clip_name
            }
        return data

    @staticmethod
    def str_to_time(str_time):
        (h, m, s) = str_time.split(':')
        return datetime.timedelta(hours=int(h), minutes=int(m), seconds=int(s))
