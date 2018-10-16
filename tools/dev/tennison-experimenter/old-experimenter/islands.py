
from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.topo import Topo

class Islands(Topo):
    """Islands topology"""


    def __init__(self):
        ONOS1_CONTROLLER_IP='192.168.123.1'

        ONOS2_CONTROLLER_IP='192.168.123.2'

        ONOS3_CONTROLLER_IP='192.168.123.3'
        Topo.__init__(self)

    # Create nodes
        h1 = self.addHost( 'h1', mac='01:00:00:00:01:00', ip='192.168.0.1/24' )
        h2 = self.addHost( 'h2', mac='01:00:00:00:02:00', ip='192.168.0.2/24' )

    # Create switches
        s1 = self.addSwitch( 's1', listenPort=6634, mac='00:00:00:00:00:01' )
        s2 = self.addSwitch( 's2', listenPort=6634, mac='00:00:00:00:00:02' )
        s3 = self.addSwitch( 's3', listenPort=6634, mac='00:00:00:00:00:03' )

        print "*** Creating links"
        self.addLink(h1, s1, )
        self.addLink(h2, s2, )   
        self.addLink(s1, s2, )  
        self.addLink(s2, s3, )  

    # Add Controllers
        onos_1 = self.addController( 'c0', controller=RemoteController, ip=ONOS1_CONTROLLER_IP, port=6633)

        onos_2 = self.addController( 'c1', controller=RemoteController, ip=ONOS2_CONTROLLER_IP, port=6633)

        onos_3 = self.addController( 'c2', controller=RemoteController, ip=ONOS2_CONTROLLER_IP, port=6633)

    # Connect each switch to a different controller
        s1.start( [onos_1] )
        s2.start( [onos_2] )
        s3.start( [onos_3] )
        s1.cmdPrint('ovs-vsctl show')

topos = { 'islands': ( lambda: Islands() ) }
