import logging
import socket
from zeroconf import ServiceBrowser, ServiceStateChange, Zeroconf
from time import sleep


class Discovery:

    def __init__(self, service_type, host=None):
        self.endpoint = None
        self.pro6_discovered = False
        self.host = host
        self.service_type = service_type

    def on_service_state_change(self, zeroconf, service_type, name, state_change):
        print("Service %s of type %s state changed: %s" % (name, service_type, state_change))

        if state_change is ServiceStateChange.Added:
            info = zeroconf.get_service_info(service_type, name)
            if info:
                if self.host is not None:
                    if self.host != info.server:
                        logging.info("Found server %s, but it does not match %s" % (info.server, self.host))
                        return

                self.pro6_discovered = True
                self.endpoint = "%s:%d" % (socket.inet_ntoa(info.address), info.port)
            else:
                logging.warning("  No info for discovered service %s of type %s" % (name, service_type))

    def discover(self):
        logging.getLogger('zeroconf').setLevel(logging.INFO)
        zeroconf = Zeroconf()
        ServiceBrowser(zeroconf, "%s._tcp.local." % self.service_type, handlers=[self.on_service_state_change])

        try:
            while not self.pro6_discovered:
                logging.info("Looking for %s..." % self.service_type)
                sleep(1.0)
        except KeyboardInterrupt:
            pass
        finally:
            zeroconf.close()
            return self.endpoint
