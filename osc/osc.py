import pro6
from pro6.actor import Actor
from osc4py3.as_eventloop import *
from osc4py3 import oscbuildparse
from .discovery import Discovery


class HogOSC(Actor):

    def __init__(self, config):
        super().__init__(config)
        if not self.enabled: return

        self.mac_addr = config['mac_addr']
        self.endpoint = self.discover()

        if self.endpoint is None:
            self.logger.warning('Could not reach OSC server, disabling functionality')
            self.disable()
            return

        osc_startup()
        osc_udp_client(self.endpoint, config['port'], "hog")

        self._cuelist_id = None

    def __del__(self):
        osc_terminate()

    def discover(self):
        return Discovery(self.mac_addr).discover()

    def recv_notice(self, obj, role, param, value):
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
        if not self.enabled: return
        if cuelist_id is None or cuelist_id is '':
            self.logger.info('No cuelist_id, cowardly refusing to send OSC command')
            return

        self.logger.debug('Sending OSC cuelist_id ' + str(cuelist_id))
        msg = oscbuildparse.OSCMessage('/hog/playback/go/0', None, [str(cuelist_id)])
        osc_send(msg, "hog")
        osc_process()

    def _reset(self):
        self._cuelist_id = None
