import logging
import netifaces as ni
import netaddr
from scapy.all import srp, Ether, ARP


class OSCDiscovery:
    logger = logging.getLogger(__name__)

    def __init__(self, mac_addr, iface_name=None):
        self.iface_name = self.detect_iface_name()
        self.mac_addr = mac_addr
        self.disabled = False

    def detect_iface_name(self):
        iface_opts = ['en4', 'eth0', 'en0', 'wlan0']
        for iface in iface_opts:
            if iface in ni.interfaces():
                self.logger.debug('Using interface %s', iface)
                return iface

        self.logger.error('No suitable network interface available, OSC discovery failed')
        self.disabled = True

    def network(self):
        addrs = ni.ifaddresses(self.iface_name)
        return addrs[ni.AF_INET]

    def local_network(self):
        ip = netaddr.IPAddress(self.network()[0]['addr'])
        netmask = netaddr.IPAddress(self.network()[0]['netmask'])
        net = netaddr.IPNetwork(str(ip) + '/' + str(netmask))
        return str(net.network) + '/' + str(net.prefixlen)

    def discover(self):
        if self.disabled: return
        self.logger.debug('Querying ' + self.local_network() + ' for OSC server @ ' + self.mac_addr)
        answered, unanswered = srp(Ether(dst=self.mac_addr)/ARP(pdst=self.local_network()), timeout=1, verbose=True)
        if len(answered) > 0:
            for snd, rcv in answered:
                self.logger.debug('Found ' + rcv.sprintf(r"%Ether.src% @ %ARP.psrc%"))
                return rcv.sprintf(r"%ARP.psrc%")
        elif len(unanswered) > 0:
            self.disabled = True
            self.logger.warning(unanswered[0].getlayer(ARP).pdst, " cannot be reached")

