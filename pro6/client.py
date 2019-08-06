from lib.observer import Subscriber
from lib.observer import Notifier
import pro6
import pi
import osc
import logging
from time import sleep


class Client(Subscriber, Notifier):
    logger = logging.getLogger(__name__)

    def __init__(self, config, msg_queue):
        self._config = config
        self._msg_queue = msg_queue
        self._message_handler = pro6.Handler(msg_queue)
        self._p6_clock = pro6.Clock()
        self._p6_stage = None
        self._p6_remote = None

        self.lcd = pi.LCD()
        self.led = pi.LED()
        self.osc = osc.HogOSC(config['osc'])

        self.event = None
        self.connected = False
        self.create_subscriptions()

    def create_subscriptions(self):
        self._p6_clock.subscribe(self.lcd)
        self._p6_clock.subscribe(self.led)
        self._p6_clock.subscribe(self.osc)
        self.subscribe(self._p6_clock)

    def connect_to_pro6(self):
        host_list = map(lambda host: host + '.local.', self._config['pro6']['host_search'])
        # self.lcd.clear()
        # self.lcd.display_message("Searching for Pro6", lcd_line=2)
        remote_endpoint = pro6.Discovery("_pro6stagedsply", host_list).discover()

        # self.lcd.display_message("Connecting to", lcd_line=2)
        # self.lcd.display_message(remote_endpoint, lcd_line=3)
        # self.lcd.clear()

        self.init_stage(remote_endpoint)

        self.logger.debug('Connecting to stage endpoint...')
        while not self._p6_stage.connected:
            self.logger.debug('Waiting for connection...')
            sleep(1)

        # self.lcd.clear()
        # self.lcd.rtc_run()

    def init_stage(self, remote_endpoint):
        self._p6_stage = pro6.WebSocket(
            self._config['pro6']['password'],
            '_pro6stagedsply',
            remote_endpoint,
            self._msg_queue
        )

        self._p6_stage.subscribe(self)
        self._p6_stage.run()

    def stop(self):
        self._p6_stage.stop()
        self.lcd.rtc_stop()
        self.lcd.clear()

    def notify(self, obj, param, value):
        self.logger.debug("Got notification %s:%s" % (param, value))
        if param == 'message_pending':
            self.process_messages()
        elif param == 'connected':
            self.logger.info('Connected: %s', value)
            self.connected = value
            if not self.connected: self._p6_stage.stop()

    def process_messages(self):
        while not self._msg_queue.empty():
            incoming_message = self._msg_queue.get_nowait()
            if incoming_message.kind is pro6.Message.Kind.ACTION:
                self._message_handler.do(incoming_message)
            elif incoming_message.kind is pro6.Message.Kind.EVENT:
                self.event = incoming_message
            elif incoming_message.kind is pro6.Message.Kind.ERROR:
                self.event = incoming_message
            else:
                self.logger.debug("Unhandled queue object: %s" % incoming_message)
