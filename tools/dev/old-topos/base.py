from mininet.node import Host
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel, info
from mininet.node import RemoteController
from mininet.cli import CLI

"""
sudo -E python base.py
"""

HOSTS = 7
SWITCHES = 4

class BaseTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create base topo."

        # Initialize topology
        Topo.__init__( self )

        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        s1 = self.addSwitch('s1')

        self.addLink(h1, s1)
        self.addLink(h2, s1)


def run():
    c = RemoteController('c', '0.0.0.0', 6633)
    net = Mininet(topo=BaseTopo(), host=Host, controller=None)
    net.addController(c)
    net.start()

    CLI(net)
    net.stop()

# if the script is run directly (sudo topology/base.py):
if __name__ == '__main__':
    setLogLevel('info')
    run()
