import pro6
import pi
import osc
from time import sleep
import threading
from .websocket import WebSocket
from .actor import Actor
from .handler import Handler
from typing import Dict
from enum import Enum, auto


class Roles(Enum):
    DIRECTOR    = auto()
    CLOCK       = auto()
    STAGE_DSP   = auto()
    REMOTE      = auto()
    LCD_SCREEN  = auto()
    LED         = auto()
    OSC         = auto()
    # LAN_LINK    = auto()  # WIP


class Director(Actor):

    WAIT_RETRIES = 10

    def __init__(self, config, msg_queue):
        super().__init__(config)
        self._msg_queue = msg_queue
        self._message_handler = Handler(msg_queue)

        self._t = None
        self.stopping = False

        self.event = None
        self.connected = False
        self.network_up = False

        self._actors = Dict[int, Actor]
        self._actors = {}
        self.create_actors(config)
        self.create_subscriptions()

    def create_actors(self, config):

        self._actors = {
            Roles.DIRECTOR:     self,
            Roles.CLOCK:        pro6.Clock(),
            Roles.STAGE_DSP:    WebSocket(self.config['pro6'], '_pro6stagedsply', self._msg_queue),
            # CastMembers.REMOTE:     None,  # Reserved
            Roles.LCD_SCREEN:   pi.LCDScreen(None),
            Roles.LED:          pi.LED(),
            Roles.OSC:          osc.HogOSC(config['osc']),
            # Roles.LAN_LINK:     pro6.LAN(config['lan'])  # WIP
        }

        [actor.assign_role(role) for role, actor in self._actors.items()]

    def create_subscriptions(self):
        for actor in self._actors.values():
            if not actor.watching:
                continue

            [self._actors[role].subscribe(actor) for role in actor.watching]

    @property
    def watching(self):
        return [
            Roles.CLOCK,
            Roles.STAGE_DSP
        ]

    def connect_to_pro6(self):
        self.update_status()
        self.logger.debug('Connecting to pro6')

        self._actors[Roles.STAGE_DSP].discover()
        self._actors[Roles.STAGE_DSP].connect()
        self._actors[Roles.STAGE_DSP].run()

        self.logger.debug('Connecting to stage endpoint...')
        # After failing a certain number of times, we should fall back
        # to discovery
        wait_counter = 0
        while self._actors[Roles.STAGE_DSP].status is Actor.StatusEnum.OFFLINE:
            self.logger.debug('Waiting for connection (%i/%i)...', wait_counter, self.WAIT_RETRIES)
            sleep(2)
            wait_counter += 1
            if wait_counter >= self.WAIT_RETRIES:
                self.logger.warn("Failed connecting after %i tries", wait_counter)
                self._actors[Roles.STAGE_DSP].stop()
                sleep(10)
                return

    def _loop(self):
        while not self.stopping:
            if self.status is Actor.StatusEnum.OFFLINE:
                self.connect_to_pro6()
            # self.check_network()
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

    def recv_notice(self, obj, role, param, value):
        if role is Roles.STAGE_DSP:
            if param == 'status':
                self.logger.debug("New stage display status: %s" % value)
                if self._actors[Roles.STAGE_DSP].status is Actor.StatusEnum.OFFLINE:
                    self._actors[Roles.STAGE_DSP].stop()
                self.update_status()

        if param == 'message_pending':
            self.process_messages()
        elif param == 'connected':
            self.logger.info('Connected: %s', value)
            self.update_status()

    def update_status(self):
        if self._actors[Roles.STAGE_DSP].status is Actor.StatusEnum.OFFLINE:
            self.status = Actor.StatusEnum.OFFLINE
            return

        if self._actors[Roles.CLOCK].status is Actor.StatusEnum.ACTIVE:
            self.status = Actor.StatusEnum.ACTIVE
        else:
            self.status = Actor.StatusEnum.STANDBY

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
