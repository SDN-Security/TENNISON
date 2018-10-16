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
from mininet.topolib import TreeTopo, TorusTopo
from mininet.clean import cleanup

from mininet.util import quietRun, specialClass
from mininet.log import setLogLevel, info, warn, error, debug
from onos import ONOSCluster, ONOSOVSSwitch, ONOSCLI, RenamedTopo

from tennison import TENNISONNode

import logging
import threading
import time

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


    setLogLevel( 'info' )
    loading_bar_thread = threading.Thread(name='loading_bar', target=loading_bar)
    #loading_bar_thread.start()
    #progress(10, 100, status='Processing topology')
    # East and west control network topologies (using RenamedTopo)
    # We specify switch and host prefixes to avoid name collisions
    # East control switch prefix: 'east_cs', ONOS node prefix: 'east_onos'
    # Each network is a renamed SingleSwitchTopo of size clusterSize
    # It's also possible to specify your own control network topology
    clusterSize = 1


    update_loading_bar(5, 'Transforiming cluster toplogies')
    etopo = RenamedTopo( SingleSwitchTopo, clusterSize,
                         snew='a_cs', hnew='alpha_c' )
    wtopo = RenamedTopo( SingleSwitchTopo, clusterSize,
                         snew='b_cs', hnew='beta_c' )
    # east and west ONOS clusters
    # Note that we specify the NAT node names to avoid name collisions

    #progress(20, 100, status='Launching ONOS cluster alpha')
    
    update_loading_bar(10, 'Creating alpha cluster')
    alpha_cluster = ONOSCluster( 'alpha', topo=etopo, ipBase='192.168.123.0/24',
                        nat='alpha_nat' )


    update_loading_bar(10, 'Creating beta cluster')
    #progress(50, 100, status='Launching ONOS cluster beta')
    beta_cluster = ONOSCluster( 'beta', topo=wtopo, ipBase='192.168.124.0/24',
                        nat='beta_nat', portOffset=100 )
    # Data network topology. TODO Add link delays and change topo.

    
    #progress(70, 100, status='Initialising topology')


    update_loading_bar(10, 'Creating topology')
    topo = LinearTopo( 10 )

    #topo = TreeTopo(2)



    #progress(80, 100, status='Creating network')
    # Create network


    update_loading_bar(5, 'Compiling topologies')
    net = Mininet( topo=topo, switch=MultiSwitch, controller=[ alpha_cluster, beta_cluster ] )



    #progress(85, 100, status='Launching TENNISON instance alpha')
    
    update_loading_bar(5, 'Adding tennison alpha')
    tennison_alpha = net.addHost('alpha_t', cls=TENNISONNode, ipBase='192.168.123.1/24', ip='192.168.123.100', gw='192.168.123.2')

    net.addLink(tennison_alpha, alpha_cluster.net.get('a_cs1'))
    #progress(90, 100, status='Launching TENNISON instance beta')


    update_loading_bar(5, 'Adding tennison beta')
    tennison_beta = net.addHost('beta_t', cls=TENNISONNode, portOffset=100, ipBase='192.168.124.1/24', ip='192.168.124.100', gw='192.168.124.2')

    net.addLink(tennison_beta, beta_cluster.net.get('b_cs1'))

    # Assign switches to controllers
    count = len( net.switches )
    #TODO this will have to change depending on the topology
    for i, switch in enumerate( net.switches ):
	#progress(90+i, 100, status='Connecting switches to ONOS')
        switch.controller = alpha_cluster if i < count/2 else beta_cluster

    #TODO Need to add TENNISON here. Connect TENNISON to controller switches
    #TENNISON is a mininet Node with a direct connect to ONOS (preferably not over loopback)


    # Start up network
    #progress(99, 100, status='Loading network, please wait')
    
    update_loading_bar(5, 'Launching network, please wait')
    net.start()
     #tennison_alpha.setIP('192.168.123.2')
    #progress(100, 100, status='Complete')
    # This code should be placed in the Tennison class
    update_loading_bar(5, 'Starting tennison alpha')
    output = tennison_alpha.cmd('ifconfig alpha_t-eth0 192.168.123.100')
    output = tennison_alpha.cmd('route add default gw 192.168.123.2')
    output = tennison_alpha.cmd('ifconfig lo up')
    #info('Setting tennison alpha ip ' + output)
    tennison_alpha.start()


    update_loading_bar(5, 'Starting tennison beta')
    output = tennison_beta.cmd('ifconfig beta_t-eth0 192.168.124.100')
    output = tennison_beta.cmd('route add default gw 192.168.124.2')
    output = tennison_beta.cmd('ifconfig lo up')
    ##info('Setting tennison beta ip ' + output)
    tennison_beta.start()

    fixIPTables()


    #Install onos apps

    alpha_cluster.net.get('alpha_c1').cmd('/opt/onos/tools/dev/bash_profile')
    alpha_cluster.net.get('alpha_c1').cmd('/opt/onos-tennison-apps/install_apps_remote > onos-apps.log')

    beta_cluster.net.get('beta_c1').cmd('/opt/onos/tools/dev/bash_profile')
    beta_cluster.net.get('beta_c1').cmd('/opt/onos-tennison-apps/install_apps_remote > onos-apps.log')



    update_loading_bar(100, 'Loading complete')
    time.sleep(1)

    setLogLevel( 'info' )

    info('\n')

    global Loading
    Loading = False
    
    ONOSCLI( net )  # run our special unified Mininet/ONOS CLI

    tennison_alpha.stop()
    tennison_beta.stop()
    net.stop()

def update_loading_bar(increment, status):
    global Progress, Status
    Progress += increment
    Status = status



def fixIPTables():
    "Fix LinuxBridge warning"
    for s in 'arp', 'ip', 'ip6':
        quietRun( 'sysctl net.bridge.bridge-nf-call-%stables=0' % s )

Loading = True
Progress = 0
Status = ''
def loading_bar():
    global Loading, Progress, Status
    while(Loading):
        
        time.sleep(0.5)
        Progress +=1
        if Progress > 100:
            Progress = 100
            Loading = False
        progress(Progress, 100, status=Status) 
        time.sleep(0.5)



def progress(count, total, status=''):
    if( not Loading ):
        return
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
    try:
        run()
    except (KeyboardInterrupt, SystemExit):
        Loading = False
    except Exception as e:
        Loading = False
        error('ERROR: ' + str(e) + '\n')
       # sys.exit()
