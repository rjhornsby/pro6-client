from lib.observer import Subscriber
import pro6
from osc4py3.as_eventloop import *
from osc4py3 import oscbuildparse
import logging
import osc


class KonnectOSC(Subscriber):

    logger = logging.getLogger(__name__)

    def __init__(self, osc_config):
        self.disabled = osc_config['disabled']

        if self.disabled: return

        osc_server = self.discover_osc_server(osc_config['mac_addr'])
        if osc_server is None:
            self.logger.warning('Could not reach OSC server, disabling functionality')
            self.disabled = True
            return

        osc_startup()
        osc_udp_client(osc_server, osc_config['port'], "hog")

        self._cuelist_id = None

    def __del__(self):
        osc_terminate()

    def discover_osc_server(self, mac_addr):
        d = osc.OSCDiscovery(mac_addr)
        return d.discover()

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

        self.logger.debug('Sending OSC cuelist_id ' + str(cuelist_id))
        msg = oscbuildparse.OSCMessage('/hog/playback/go/0', None, [str(cuelist_id)])
        osc_send(msg, "hog")
        osc_process()

    def _reset(self):
        self._cuelist_id = None
