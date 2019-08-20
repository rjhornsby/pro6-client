from .actor import Actor
import pro6
import netifaces
import socket
from ICMP import ICMPPacket


class LAN(Actor):
    def __init__(self, config):
        super().__init__(config)

    def discover(self):
        if not self.osi_layer1():
            self.logger.error('Interface %s not connected or not available', self.config['iface'])
            return

        self.endpoint, _ = netifaces.gateways()['default'][netifaces.AF_INET]

    def osi_layer3(self):
        if not self.endpoint:
            self.logger.error('Gateway addr not set, use discover() first')

    def _send_ping(self):
        pass

    def osi_layer1(self):
        return netifaces.AF_INET in netifaces.ifaddresses(self.config['iface'])

    def watching(self):
        return [
            pro6.Roles.DIRECTOR
        ]

    def recv_notice(self, obj, param, value):
        if param == 'stopping' and value is True:
            self.stop()

    def run(self):
        pass

    def stop(self):
        pass

    def _loop(self):
        pass