#!/usr/bin/python

"""
This example shows how to create an empty Mininet object
(without a topology object) and add nodes to it manually.
"""
import sys
import re 
import time

from mininet.net import Mininet, VERSION
from mininet.node import Controller, RemoteController, UserSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Intf
from mininet.term import makeTerm, makeTerms

from distutils.version import StrictVersion

def emptyNet():

    MININET_VERSION = re.sub(r'[^\d\.]', '', VERSION)

    "Create an empty network and add nodes to it."

    net = Mininet( controller=Controller)

    info( '*** Adding controller\n' )
    net.addController(name='c0',
                      controller=RemoteController,
                      ip='127.0.0.1',
                      protocol='tcp',
                      port=6633)

    
    #This is the 3 host, 1 switch topology. 
    #The Switch IDs is of:0000000000000001.
    #The port for Snort is 4.
    #You must make sure this set in SnortManager.java in the Snort app to get it to work correctly.
    
    info( '*** Adding hosts\n' )
    h1 = net.addHost('h1', ip='10.0.0.1')
    h2 = net.addHost('h2', ip='10.0.0.2')
    h3 = net.addHost('h3', ip='10.0.0.3')
    snort1 = net.addHost('snort1', ip='10.0.0.4')


    info( '*** Adding switch\n' )
    s1 = net.addSwitch( 's1' )

    info( '*** Creating links\n' )
    net.addLink(s1, h1)
    net.addLink(s1, h2)
    net.addLink(s1, h3)
    net.addLink(snort1, s1)

    _intf = Intf('veth1', node=snort1 )

    ''' 
    #This is the 9 host, 4 switch topology.
    #The Switch IDs go from of:0000000000000001 to of:0000000000000004.
    #The port for Snort is 4 for of:0000000000000001 and 5 for the rest.
    #You must make sure this set in SnortManager.java in the Snort app to get it to work correctly.

    info( '*** Adding hosts\n' )
    h1 = net.addHost('h1', ip='10.0.0.1')
    h2 = net.addHost('h2', ip='10.0.0.2')
    h3 = net.addHost('h3', ip='10.0.0.3')
    h4 = net.addHost('h4', ip='10.0.0.4')
    h5 = net.addHost('h5', ip='10.0.0.5')
    h6 = net.addHost('h6', ip='10.0.0.6')
    h7 = net.addHost('h7', ip='10.0.0.7')
    h8 = net.addHost('h8', ip='10.0.0.8')
    h9 = net.addHost('h9', ip='10.0.0.9')
    snort1 = net.addHost('snort1', ip='10.0.0.10')


    info( '*** Adding switches\n' )
    s1 = net.addSwitch( 's1' )
    s2 = net.addSwitch( 's2' )
    s3 = net.addSwitch( 's3' )
    s4 = net.addSwitch( 's4' )

    info( '*** Creating links\n' )
    net.addLink(s1, s2)
    net.addLink(s1, s3)
    net.addLink(s1, s4)

    net.addLink(s2, h1)
    net.addLink(s2, h2)
    net.addLink(s2, h3)
    net.addLink(s3, h4)
    net.addLink(s3, h5)
    net.addLink(s3, h6)
    net.addLink(s4, h7)
    net.addLink(s4, h8)
    net.addLink(s4, h9)
    
    net.addLink(s1, snort1)
    net.addLink(s2, snort1)
    net.addLink(s3, snort1)
    net.addLink(s4, snort1)
    '''

    
    info( '*** Starting network\n')
    net.start()

    #This will find interfaces on the snort machine (excluding veth1) and bridge them into one interface.
    interfaces = net.get("snort1").intfNames()[:-1]
    snort1.cmd("brctl addbr snort_bridge")
    for intfs in interfaces:
	info('*** Adding interface ' + intfs + ' to snort_bridge' + '\n')
        snort1.cmd("brctl addif snort_bridge " + intfs)
    snort1.cmd("ifconfig snort_bridge up")

    #Inital terminal to setup a x11 tunnel for remote machines
    #TODO: add command to exit this terminal for local machines
    net.terms += makeTerm(snort1, 'tmp')
    time.sleep(2)

    net.terms += makeTerm(snort1, 'Pig Relay', cmd="bash startPigrelay.sh '" + sys.argv[1]+  "'") 
    info( '*** Running CLI\n' )
    CLI( net )

    h1.deleteIntfs()
    h2.deleteIntfs()
    h3.deleteIntfs()
    snort1.deleteIntfs()

    info( '*** Stopping network\n' )
    net.stop()
    
    
if __name__ == '__main__':
    setLogLevel( 'info' )
    emptyNet()
