import pro6
from pro6.actor import Actor
from osc4py3.as_eventloop import *
from osc4py3 import oscbuildparse
from .discovery import Discovery
from marker.marker import Marker

class HogOSC(Actor):

    def __init__(self, config):
        super().__init__(config)

        self.mac_addr = config['mac_addr']
        self.endpoint = self.config.get('discovery_override', self.discover())

        if self.endpoint is None:
            self.logger.error('Could not reach OSC server, disabling functionality')
            self.disable()
            return

        self.logger.info(f"Discovered OSC server @ {self.endpoint}")

        osc_startup()
        osc_udp_client(self.endpoint, config['port'], "hog")

        # self._cuelist_id = None
        self.status = Actor.StatusEnum.ACTIVE

    def __del__(self):
        osc_terminate()

    def discover(self):
        return Discovery(self.mac_addr).discover()

    @property
    def watching(self):
        return [
            pro6.Roles.CLOCK
        ]

    def recv_notice(self, obj, role, param, value):
        if self.status is Actor.StatusEnum.DISABLED:
            return

        target = getattr(self, 'h_%s_%s' % (role.name.lower(), param), None)
        if target is None:
            self.logger.debug('No handler for %s:%s:%s', type(obj), role, param)
            return

        target(value)

        # if role is pro6.Roles.CLOCK and self._clock is not obj:
        #     self._clock = obj

        # if param == 'ready':
        #     self._reset()
        #
        # if not clock.ready: return
        #
        # if self._cuelist_id is None or param == 'current_marker':
        #     self._send_osc_command(clock.cuelist_id)
        #     self._cuelist_id = clock.cuelist_id

    def h_clock_current_marker(self, marker: Marker):
        if not marker: return
        self._send_osc_command(marker.light_cue)

    def h_clock_tcr_negative(self, *_):
        osc_process()

    def _send_osc_command(self, cuelist_id):
        if not self.enabled: return
        if not cuelist_id:
            self.logger.info('No cuelist_id, cowardly refusing to send OSC command')
            return

        self.logger.info('Sending OSC cuelist_id ' + str(cuelist_id))
        msg = oscbuildparse.OSCMessage('/hog/playback/go/0', None, [str(cuelist_id)])
        osc_send(msg, "hog")
        osc_process()

    # def _reset(self):
    #     self._cuelist_id = None
