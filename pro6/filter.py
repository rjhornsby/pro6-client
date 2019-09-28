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
            payload['markers'] = MarkerTable(payload.pop('txt'))
            # payload['slideNotes'] = payload.pop('txt')
            # Filter.decode_notes(payload)
        if payload['action'] == 'vid':
            if payload['txt'] == '': return
            # ProPresenter sends DF timecodes
            payload['timecode'] = Timecode.from_str(payload.pop('txt'), df=True)

    # take the base64 encoded slide notes and convert them to a python data
    # object
    # @staticmethod
    # def decode_notes(slide):
    #     if slide['slideNotes'] == '':
    #         slide['markers'] = None
    #     else:
    #         slide['markers'] = MarkerTable(slide['slideNotes'])
    #     del slide['slideNotes']

