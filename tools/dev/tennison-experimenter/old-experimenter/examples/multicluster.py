#!/usr/bin/python

"""
multicluster.py: multiple ONOS clusters example

We create two ONOSClusters, "east" and "west", and
a LinearTopo data network where the first and second halves
of the network are connected to each ONOSCluster,
respectively.

The size of the ONOSCluster is determined by its
topology. In this example the topology is a
SingleSwitchTopo of size 1, so the "Cluster" is
actually a single node (for performance and
resource usage reasons.) However, it is possible
to use larger cluster sizes in a large (!) Mininet VM,
(e.g. 12 GB of RAM for two 3-node ONOS clusters.)

The MultiSwitch class is a customized version of
ONOSOVSSwitch that has a "controller" instance variable
(and parameter)
"""

from mininet.net import Mininet
from mininet.topo import LinearTopo, SingleSwitchTopo
from mininet.log import setLogLevel
from mininet.topolib import TreeTopo
from mininet.clean import cleanup

from mininet.log import setLogLevel, info, warn, error, debug
from onos import ONOSCluster, ONOSOVSSwitch, ONOSCLI, RenamedTopo

from tennison import TENNISONNode

import sys

from colorama import init
init(strip=not sys.stdout.isatty()) # strip colors if stdout is redirected
from termcolor import cprint 
from pyfiglet import figlet_format


class MultiSwitch( ONOSOVSSwitch ):
    "Custom OVSSwitch() subclass that connects to different clusters"

    def __init__( self, *args, **kwargs ):
        "controller: controller/ONOSCluster to connect to"
        self.controller = kwargs.pop( 'controller', None )
        ONOSOVSSwitch.__init__( self, *args, **kwargs )

    def start( self, controllers ):
        "Start and connect to our previously specified controller"
        return ONOSOVSSwitch.start( self, [ self.controller ] )


def run():
    "Test a multiple ONOS cluster network"
    #setLogLevel( 'error' )
    cprint(figlet_format('TENNISON', font='slant'), 'red')


    progress(10, 100, status='Processing topology')
    # East and west control network topologies (using RenamedTopo)
    # We specify switch and host prefixes to avoid name collisions
    # East control switch prefix: 'east_cs', ONOS node prefix: 'east_onos'
    # Each network is a renamed SingleSwitchTopo of size clusterSize
    # It's also possible to specify your own control network topology
    clusterSize = 1
    etopo = RenamedTopo( SingleSwitchTopo, clusterSize,
                         snew='a_cs', hnew='alpha_c' )
    wtopo = RenamedTopo( SingleSwitchTopo, clusterSize,
                         snew='b_cs', hnew='beta_c' )
    # east and west ONOS clusters
    # Note that we specify the NAT node names to avoid name collisions

    progress(20, 100, status='Launching ONOS cluster alpha')
    
    alpha = ONOSCluster( 'alpha', topo=etopo, ipBase='192.168.123.0/24',
                        nat='alpha_nat' )


    progress(50, 100, status='Launching ONOS cluster beta')
    beta = ONOSCluster( 'beta', topo=wtopo, ipBase='192.168.124.0/24',
                        nat='beta_nat', portOffset=100 )
    # Data network topology. TODO Add link delays and change topo.

    
    progress(70, 100, status='Initialising topology')
    topo = LinearTopo( 10 )



    progress(80, 100, status='Creating network')
    # Create network
    net = Mininet( topo=topo, switch=MultiSwitch, controller=[ alpha, beta ] )



    progress(85, 100, status='Launching TENNISON instance alpha')
    tennison_alpha = net.addHost('alpha_t', cls=TENNISONNode)

    net.addLink(tennison_alpha, alpha.net.get('a_cs1'))
    error(type(tennison_alpha))
    progress(90, 100, status='Launching TENNISON instance beta')
    tennison_beta = net.addHost('beta_t', cls=TENNISONNode)

    # Assign switches to controllers
    count = len( net.switches )
    #TODO this will have to change depending on the topology
    for i, switch in enumerate( net.switches ):
	progress(90+i, 100, status='Connecting switches to ONOS')
        switch.controller = alpha if i < count/2 else beta

    #TODO Need to add TENNISON here. Connect TENNISON to controller switches
    #TENNISON is a mininet Node with a direct connect to ONOS (preferably not over loopback)


    # Start up network
    progress(99, 100, status='Loading network, please wait')
    net.start()
     #tennison_alpha.setIP('192.168.123.2')
    progress(100, 100, status='Complete')
    setLogLevel( 'info' )

    # This code should be placed in the Tennison class
    output = tennison_alpha.cmd('ifconfig alpha_t-eth0 192.168.123.2')
    info('Setting tennison ip ' + output)
    tennison_alpha.start()
    
    ONOSCLI( net )  # run our special unified Mininet/ONOS CLI

    tennison_alpha.stop()
    tennison_beta.stop()
    net.stop()





def progress(count, total, status=''):
    sys.stdout.write("\033[K")
    bar_len = 46
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('\r[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush() 


# Add a "controllers" command to ONOSCLI

def do_controllers( self, line ):
    "List controllers assigned to switches"
    cmap = {}
    for s in self.mn.switches:
        c = getattr( s, 'controller', None ).name
        cmap.setdefault( c, [] ).append( s.name )
    for c in sorted( cmap.keys() ):
        switches = ' '.join( cmap[ c ] )
        print '%s: %s' % ( c, switches )

ONOSCLI.do_controllers = do_controllers


if __name__ == '__main__':
    run()
