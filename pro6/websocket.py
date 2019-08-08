import lomond
from lomond import events
import json
import threading
import logging
from pro6.message import Message
from lib.observer import Notifier
from lib.observer import Subscriber
from time import sleep


class WebSocket(Notifier, Subscriber):
    logger = logging.getLogger(__name__)

    SOCKET_CLOSE_TIMEOUT = 2

    def __init__(self, password, service_type, host, msg_queue):
        self.connected = False
        self._ws = None
        self._host = host
        self._password = password
        self._service_type = service_type
        self._ws = lomond.WebSocket("ws://%s/%s" % (self._host, self._ws_params()['url_path']))
        self._stopping = False
        self._active_stage_uid = None
        self._t = None

        self.msg_queue = msg_queue
        self.message_pending = False

    def notify(self, obj, param, value):
        if param == 'stopping' and value is True:
            self.stop()

    def _ws_params(self):
        return {
            'url_path': 'stagedisplay',
            'auth_cmd': {'acn': 'ath', 'ptl': '610', 'pwd': self._password}
        }

    def send(self, json_data):
        self._ws.send_json(json_data)

    def authenticate(self):
        self.logger.debug('Authenticating to Pro6 websocket')
        self.send(self._ws_params()['auth_cmd'])

    def current_presentation(self):
        self.send({
                'action': 'presentationCurrent',
                'presentationSlideQuality': 0
            })

    def current_slide(self):
        self.send({'action': 'presentationSlideIndex'})

    def stage_uid(self):
        self.send({'acn': 'psl'})

    def stage_configuration(self):
        if self._active_stage_uid is None:
            # We need the stage UID. When the event loop
            # sees the `psl` action, it will call us back
            self.stage_uid()
            return

        self.send({'acn': 'fv', 'uid': self._active_stage_uid})

        # Clear the stage uid so that it isn't cached indefinitely
        self._active_stage_uid = None

    def run(self):
        self.logger.debug('Starting thread')
        self._t = threading.Thread(target=self._loop, name=self._service_type)
        self._t.daemon = True
        self._t.start()

    def stop(self):
        self.logger.debug('Stopping thread')
        self._stopping = True
        if self._ws.is_active:
            self._ws.close()
            self.logger.debug('Giving socket time to close')
            sleep(self.SOCKET_CLOSE_TIMEOUT)

    def _loop(self):
        while not self._stopping:
            self.logger.debug("Processing events")
            for event in self._ws.connect(ping_rate=0, close_timeout=self.SOCKET_CLOSE_TIMEOUT):
                try:
                    if isinstance(event, events.Ready):
                        self.logger.info("%s ready" % self._service_type)
                        self.connected = True
                        self.authenticate()
                        self.stage_configuration()
                    elif isinstance(event, events.Disconnected):
                        self.connected = False
                    elif isinstance(event, events.ConnectFail):
                        self.logger.info("Connecting to Pro6 failed")
                        sleep(3)
                    elif isinstance(event, events.Poll):
                        if not self._ws.is_closing:
                            self._ws.send_ping(b'@')
                    elif isinstance(event, events.Text):
                        message = Message(json.loads(event.text),  kind=Message.Kind.ACTION, source=self._service_type)

                        if message['action'] == 'psl':
                            self._active_stage_uid = message['uid']
                            self.stage_configuration()

                        self.msg_queue.put(message)
                        self.message_pending = True
                except KeyboardInterrupt:
                    self.stop()
