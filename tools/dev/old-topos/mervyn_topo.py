#!/usr/bin/env python

from mininet.node import Host
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.node import RemoteController
from mininet.cli import CLI

"""
sudo -E python mervyn.py
"""

HOSTS = 9
SWITCHES = 4

class MervynTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create mervyn topo."

        # Initialize topology
        Topo.__init__( self )

        hosts = []
        switches = []

        for i in range(0, HOSTS):
            hosts.append(self.addHost('h%d' % (i,)))

        for i in range(0, SWITCHES):
            switches.append(self.addSwitch('s%d' % (i,)))
            if (i > 0):
                print 'Connect s%d to s%d' % (0, i)
                self.addLink(switches[0], switches[i])

        sw_link = lambda x: 1 + (x % (SWITCHES - 1))

        for i in range(0, HOSTS):
            print 'Connect h%d to s%d' % (i, sw_link(i))
            self.addLink(hosts[i], switches[sw_link(i)])


def run():
    c = RemoteController('c', '0.0.0.0', 6633)
    net = Mininet(topo=MervynTopo(), host=Host, controller=None)
    net.addController(c)
    net.start()

    CLI(net)
    net.stop()

# if the script is run directly (sudo topology/base.py):
if __name__ == '__main__':
    setLogLevel('info')
    run()
