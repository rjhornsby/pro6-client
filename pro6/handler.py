import logging
from pro6.message import Message

class Handler:
    def __init__(self, manager_queue):
        self.manager_queue = manager_queue

    def do(self, message):
        handler_method = getattr(self, "_%s" % message.name, None)
        if callable(handler_method):
            handler_method(message)
        else:
            logging.warning("No method to handle action %s" % message.name)

    def _csn(self, message):
        event = Message(message_content={'event': 'slide_change', 'segment_markers': message['segment_markers']})
        self.manager_queue.put(event)

    def _vid(self, message):
        if message['timecode'] is None: return
        event = Message(message_content={'event': 'video_advance', 'timecode': message['timecode']})
        self.manager_queue.put(event)

    # selected stage layout (p = pro...)
    def _psl(self, message):
        logging.info('Got stage uid %s' % message['uid'])

    # field values for stage layout
    def _fv(self, message):
        # FV contains a set of actions in an array
        # so to process those we need to push each
        # array item back into the queue as if it came
        # directly from the websocket message queue
        for fv_item in message['ary']:
            if fv_item['acn'] != 'fv':  # for sanity
                self.manager_queue.put(Message(message_content=fv_item, kind=Message.Kind.ACTION, source='fv'))

    @staticmethod
    def _authenticate(message):
        if not message['authenticated']:
            logging.critical('Authentication failed for %s: %s' % (message.source, message.error))
            return False
        return True
