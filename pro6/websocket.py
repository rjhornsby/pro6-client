import lomond
# from lomond import WebSocket
from lomond.persist import persist
import json
import threading
import logging
from pro6.message import Message

class WebSocket:
    def __init__(self, password, service_type, host, msg_queue):
        self.connected = False
        self.ws = None
        self.host = host
        self.password = password
        self.service_type = service_type
        self.ws_params = self.get_ws_params()

        self.ws = lomond.WebSocket("ws://%s/%s" % (self.host, self.ws_params['url_path']))
        self.msg_queue = msg_queue
        self.stopping = False
        self.active_stage_uid = None
        self._t = None

    def get_ws_params(self):
        params = {}
        if self.service_type == "_pro6proremote":
            params['url_path'] = 'remote'
            params['auth_cmd'] = {
                'action': 'authenticate',
                'protocol': '600',
                'password': self.password
            }
        else:
            params['url_path'] = "stagedisplay"
            params['auth_cmd'] = {
                'acn': 'ath',
                'ptl': '610',
                'pwd': self.password
            }

        return params

    def send(self, jsonData):
        self.ws.send_json(jsonData)

    def authenticate(self):
        self.send(self.ws_params['auth_cmd'])

    def current_presentation(self):
        if self.service_type == '_pro6stagedsply':
            logging.error('Invalid service %s for request' % self.service_type)
            return

        self.send({
                'action': 'presentationCurrent',
                'presentationSlideQuality': 0
            })

    def current_slide(self):
        if self.service_type == '_pro6stagedsply':
            logging.error('Invalid service %s for request' % self.service_type)
            return
        self.send({'action': 'presentationSlideIndex'})

    def stage_uid(self):
        if self.service_type == '_pro6proremote':
            logging.error('Invalid service %s for request' % self.service_type)
            return

        self.send({'acn': 'psl'})

    def stage_configuration(self):
        if self.service_type == '_pro6proremote':
            logging.error('Invalid service %s for request' % self.service_type)
            return

        if self.active_stage_uid is None:
            # We need the stage UID. When the event loop
            # sees the `psl` action, it will call us back
            self.stage_uid()
            return

        self.send({'acn': 'fv', 'uid': self.active_stage_uid})

        # Clear the stage uid so that it isn't cached indefinitely
        self.active_stage_uid = None

    def run(self):
        self._t = threading.Thread(target=self._loop, name=self.service_type)
        self._t.daemon = True
        self._t.start()

    def stop(self):
        self.stopping = True
        if self.ws.is_active:
            self.ws.close()

    def _loop(self):
        while not self.stopping:
            for action in persist(self.ws, ping_rate=0):
                try:
                    if action.name == "ready":
                        logging.info("%s ready" % self.service_type)
                        self.connected = True
                        self.authenticate()
                    elif action.name == "poll":
                        self.ws.send_ping(b'@')
                    elif action.name == "text":
                        message = Message(json.loads(action.text), source=self.service_type, kind=Message.Kind.ACTION)

                        if message['action'] == 'psl':
                            self.active_stage_uid = message['uid']
                            self.stage_configuration()
                        self.msg_queue.put(message)
                except KeyboardInterrupt:
                    self.stop()
