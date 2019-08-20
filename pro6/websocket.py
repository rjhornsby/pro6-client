import lomond
from lomond import events
import json
import threading
from time import sleep
from .message import Message
from .actor import Actor
from .discovery import Discovery


class WebSocket(Actor):
    SOCKET_CLOSE_TIMEOUT = 2

    def __init__(self, config, service_type, msg_queue):
        super().__init__(config)
        self.status = Actor.StatusEnum.OFFLINE
        self._ws = None
        self._password = self.config['password']
        self._service_type = service_type
        self._ws = None
        self._stopping = False
        self._active_stage_uid = None
        self._t = None
        #
        # message_pending is watched by director.
        # when the value is updated, the notification
        # causes the director to process the msg_queue.
        self.message_pending = False
        self._msg_queue = msg_queue

    def discover(self):
        host_list = map(lambda host: host + '.local.', self.config['host_search'])
        remote_endpoint = Discovery(self._service_type, host_list).discover()
        if remote_endpoint:
            self.discovered = True
            self.endpoint = remote_endpoint
        else:
            raise Exception("Unable to discover endpoint")

    def connect(self):
        self._ws = lomond.WebSocket("ws://%s/%s" % (self.endpoint, self._ws_params()['url_path']))

    def recv_notice(self, obj, param, value):
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
        self._stopping = False
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
                        self.status = Actor.StatusEnum.ACTIVE
                        self.authenticate()
                        self.stage_configuration()
                    elif isinstance(event, events.Disconnected):
                        self.status = Actor.StatusEnum.OFFLINE
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

                        self._msg_queue.put(message)
                        self.message_pending = True
                except KeyboardInterrupt:
                    self.stop()
