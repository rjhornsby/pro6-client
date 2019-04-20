import logging
import socket
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from time import sleep


class Discovery:
    logger = logging.getLogger(__name__)

    def __init__(self, service_type, host_list=None):
        self.endpoint = None
        self.pro6_discovered = False
        self.host_list = host_list
        self.service_type = service_type

    def on_service_state_change(self, zeroconf, service_type, name, state_change):
        self.logger.info("Service %s of type %s state changed: %s" % (name, service_type, state_change))

        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                if self.host_list is not None:
                    if info.server not in self.host_list:
                        logging.info("Found server %s, but not on our list" % info.server)
                        return

                self.pro6_discovered = True
                self.endpoint = "%s:%d" % (socket.inet_ntoa(info.address), info.port)
            else:
                self.logger.warning("  No info for discovered service %s of type %s" % (name, service_type))

    def discover(self):
        # logging.getLogger('zeroconf').setLevel(logging.INFO)
        zeroconf = Zeroconf()
        ServiceBrowser(zeroconf, "%s._tcp.local." % self.service_type, handlers=[self.on_service_state_change])

        while not self.pro6_discovered:
            self.logger.info("Looking for %s..." % self.service_type)
            sleep(3.0)

        zeroconf.close()
        return self.endpoint
