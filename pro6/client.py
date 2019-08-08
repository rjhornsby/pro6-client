from enum import Enum
from lib.observer import *
# import pro6
import pro6
import pi
import osc
import logging
from time import sleep
import threading

class Client(Subscriber, Notifier):

    logger = logging.getLogger(__name__)

    def __init__(self, config, msg_queue):
        self._config = config
        self._msg_queue = msg_queue
        self._message_handler = pro6.Handler(msg_queue)

        self._t = None
        self.stopping = False

        self._p6_clock = pro6.Clock()
        self._p6_stage = None
        self._p6_remote = None
        self._lcdScreen = pi.LCDScreen()

        self.led = pi.LED()
        self.osc = osc.HogOSC(config['osc'])

        self.event = None
        self.connected = False
        self.p6_state = pro6.Status.OFFLINE

        self.create_subscriptions()

    def create_subscriptions(self):
        self._p6_clock.subscribe(self._lcdScreen)
        self._p6_clock.subscribe(self.led)
        self._p6_clock.subscribe(self.osc)

        self.subscribe(self._lcdScreen)
        self.subscribe(self._p6_clock)
        self._p6_clock.subscribe(self)

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

    def _loop(self):
        while not self.stopping:
            if self.p6_state == pro6.Status.OFFLINE:
                self.connect_to_pro6()
            sleep(1)

    def run(self):
        self.logger.debug('Starting thread')
        self._t = threading.Thread(target=self._loop, name=__name__)
        self._t.daemon = True
        self._t.start()

    def stop(self):
        self.logger.debug('Stopping thread')

        # child threads should be subscribed and watching `stopping` for changes
        self.stopping = True

    def notify(self, obj, param, value):
        self.logger.debug('Notified: %s / %s / %s' % (obj, param, value))
        if type(obj) is pro6.Clock:
            if param == 'ready':
                if value:
                    self.p6_state = pro6.Status.ACTIVE
                else:
                    self.p6_state = pro6.Status.STANDBY

        if param == 'message_pending':
            self.process_messages()
        elif param == 'connected':
            self.logger.info('Connected: %s', value)
            if value:
                self.p6_state = pro6.Status.STANDBY
            else:
                self.p6_state = pro6.Status.OFFLINE

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
