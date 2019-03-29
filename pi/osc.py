from lib.observer import Subscriber
import pro6
from osc4py3.as_eventloop import *
from osc4py3 import oscbuildparse
import logging


class KonnectOSC(Subscriber):

    def __init__(self, config):
        self.disabled = config['disabled']
        if self.disabled: return
        osc_startup()
        osc_udp_client(config['ip_addr'], config['port'], "hog")

        self._cuelist_id = None

    def __del__(self):
        osc_terminate()

    def notify(self, obj, param, value):
        if type(obj) is pro6.clock.Clock:
            clock = obj
        else:
            return

        if param == 'ready':
            self._reset()

        if not clock.ready: return

        if self._cuelist_id is None or param == 'current_segment':
            self._send_osc_command(clock.cuelist_id)
            self._cuelist_id = clock.cuelist_id

    def _send_osc_command(self, cuelist_id):
        if self.disabled: return
        if cuelist_id is None or cuelist_id is '':
            logging.info('No cuelist_id, cowardly refusing to send OSC command')
            return

        logging.info('Sending OSC cuelist_id ' + str(cuelist_id))
        msg = oscbuildparse.OSCMessage('/hog/playback/go/0', None, [str(cuelist_id)])
        osc_send(msg, "hog")
        osc_process()

    def _reset(self):
        self._cuelist_id = None
