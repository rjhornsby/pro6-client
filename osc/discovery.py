import logging
import netifaces as ni
import netaddr
from scapy.all import srp, Ether, ARP


class Discovery:
    logger = logging.getLogger(__name__)

    def __init__(self, mac_addr, iface_name=None):
        self.iface_name = None

        self.mac_addr = mac_addr
        self.detect_iface_name(iface_name)

    def detect_iface_name(self, default=None):
        iface_opts = ['en4', 'eth0', 'en0', 'wlan0']
        for iface in iface_opts:
            if iface in ni.interfaces():
                self.logger.info('Checking interface %s', iface)
                self.iface_name = iface
                if not self.network():
                    self.logger.warning("Failed, trying next interface")
                    continue
                else:
                    return

        self.logger.error('No suitable network interface available')

    def network(self):
        try:
            addrs = ni.ifaddresses(self.iface_name)
            return addrs[ni.AF_INET]
        except KeyError:
            self.logger.warning(f"No AF_INET entry for interface {self.iface_name}")

    def local_network(self):
        af_inet_entry = self.network()[0]
        ip = netaddr.IPAddress(af_inet_entry['addr'])
        netmask = netaddr.IPAddress(af_inet_entry['netmask'])
        net = netaddr.IPNetwork(str(ip) + '/' + str(netmask))
        return str(net.network) + '/' + str(net.prefixlen)

    def discover(self):
        if self.iface_name is None:
            self.logger.error('OSC discovery failed: no interface')
            return None

        self.logger.debug('Querying ' + self.local_network() + ' for OSC server @ ' + self.mac_addr)
        answered, unanswered = srp(Ether(dst=self.mac_addr)/ARP(pdst=self.local_network()), timeout=1, verbose=True)
        if len(answered) > 0:
            for snd, rcv in answered:
                self.logger.debug('Found ' + rcv.sprintf(r"%Ether.src% @ %ARP.psrc%"))
                return rcv.sprintf(r"%ARP.psrc%")
        elif len(unanswered) > 0:
            self.logger.warning(f"{unanswered[0].getlayer(ARP).pdst} cannot be reached")
            return None

