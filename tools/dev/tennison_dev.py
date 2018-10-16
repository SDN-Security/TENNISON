#!/usr/bin/python

"""
This example shows how to create an empty Mininet object
(without a topology object) and add nodes to it manually.
"""
import sys
import re 
import time
import subprocess
import requests
import os
import signal

from optparse import OptionParser

from mininet.net import Mininet, VERSION
from mininet.node import Controller, RemoteController, UserSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Intf
from mininet.term import makeTerm, makeTerms
from mininet.link import TCLink

from distutils.version import StrictVersion

procs = {}

PIG_CNT = 0

# Delays 
PIG_WAIT = 5

# Config Options
WRK_DIR = "/home/lyndon/"
ONOS_HOST = "127.0.0.1"

# Directories
PIG_DIR = WRK_DIR + "pigrelay/"
PIG_CMD = "python " + PIG_DIR + "pigrelay.py --config " + PIG_DIR + "examples/config.yaml  > /dev/null 2>&1 &"
MERVYN_DIR = WRK_DIR + "coordinator/"
MERVYN_CMD = ["python3", MERVYN_DIR + "mervyn.py", "--config", MERVYN_DIR + "examples/config.yaml", "--thresholds", MERVYN_DIR + "examples/thresholds.yaml"]
VETH_CMD = WRK_DIR + "topology/tennison-dev/multiVETH.sh"
MERVYN_ACTIVATE_CMD = WRK_DIR + "topology/tennison-dev/activate_mervyn"
MERVYN_DEACTIVATE_CMD = WRK_DIR + "topology/tennison-dev/deactivate_mervyn"
SFLOWRT_ACTIVATE_CMD = WRK_DIR + "sflow/sflow-rt/start.sh > /dev/null 2>&1 &"
SFLOWRT_KILL_CMD = "pkill -f sflowrt"
SFLOW_ACTIVATE_CMD = WRK_DIR + "sflow/sflowtool/src/sflowtool -f 127.0.0.1/7343 &"
SFLOW_KILL_CMD = "pkill sflowtool"

# Network
HOSTS = 20
networkNames = ['A', 'B', 'C']

def createNetworks():

    '''
    Three flat networks with 1, 2 and 3 switches respectivly.
    Hosts spead evenly across the switches 
    '''    

    info('*** Creating networks\n')
    singleSwitchNet = Mininet( controller=Controller, link=TCLink)
    twoSwitchNet = Mininet( controller=Controller, link=TCLink)
    threeSwitchNet = Mininet( controller=Controller, link=TCLink)

    networks = [singleSwitchNet, twoSwitchNet, threeSwitchNet]
    for ni, net in enumerate(networks):
        info( '*** Adding controller\n' )
        net.addController(name='c' + str(ni) + '0',controller=RemoteController, ip='127.0.0.1',protocol='tcp',port=6633)

        info( '*** Adding hosts\n' )

        for h in range(1, HOSTS + 1):
            net.addHost("h" + str(h), ip="10.0.0." + str(h))

        info( '*** Adding switches\n' )
        for s in range(1, ni + 2):
            net.addSwitch("s" + str(ni) + str(s))

        #info( '*** Adding snort links\n')
        #for sw in net.switches:
        #    net.addLink(sw, snort1)

        info( '*** Adding switch links\n')
        for si, sw in enumerate(net.switches):
            if si + 1 < len(net.switches):
                net.addLink(sw, net.switches[si+1])

        info( '*** Adding host links\n')
        hostsPerSwitch = len(net.hosts) / len(net.switches)
        sortedHosts = [net.hosts[i:i + hostsPerSwitch] for i in xrange(0, len(net.hosts), hostsPerSwitch)]
        for si, switch in enumerate(sortedHosts):
            for hi, h in enumerate(switch):
                # If overrun - add remainders to last switch 
                if si < len(net.switches) - 1:
                    net.addLink(net.switches[si], h, bw=1000)
                else:
                    net.addLink(net.switches[-1], h, bw=1000)

    return networks

def dev(options):

    if options.DEACTIVATE:
        onosDeactivateMervyn()

    if options.ACTIVATE:
        onosActivateMervyn()

    info('*** Clearing snort from ONOS\n')
    clearSnortFromONOS()

    networks = createNetworks()
    
    if options.NETWORK not in networkNames:
        info('*** Invalid network ' + options.NETWORK + '\n')
        info('*** Using default network A\n')
        net = networks[0]
    else: 
        net = networks[networkNames.index(options.NETWORK)]

    info('*** Starting network\n')
    net.start()

    if options.PIG:
        startPig(net, 'h1')
    
    if options.MERVYN:
        time.sleep(PIG_WAIT)
        startMervyn()

    # cmd = "sh ovs-vsctl -- --id=@sflow create sflow agent=s21 target=\"10.0.2.15\" sampling=10 polling=10 -- -- set bridge s21 sflow=@sflow"
    # NOTE: Our hardware switches only sflow to one controller, is there a mininet option to sflow to more than one?
    if options.SFLOW:
        for switch in net.switches:
            cmd = "ovs-vsctl -- --id=@sflow create sflow agent={} target=\"127.0.0.1\" sampling=10 polling=10 -- -- set bridge {} sflow=@sflow".format(switch.name, switch.name)
            print("ovs command:{}".format(cmd))
            subprocess.call( cmd, shell=True )
        # Start sflow-RT
        startSFlow()

    CLI(net)

    if options.MERVYN:
        killMervyn()
    
    if options.PIG:
        killPig()

    if options.SFLOW:
        killSFlow()

    info('Stopping network\n')  
    for net in networks:
        net.stop()
        for host in net.hosts:
                host.deleteIntfs()

def startPig(net, pig_name):
    '''
    Turns a vanilla host into a snort instance.
    Creates the veth pairs for the coordinator -> snort communication, and starts pig relay.
    The veth pairs are numbered to allow multiple snort instances, but it was later decided 
    this is not sensible in mininet due to their shared config file.
    '''

    global PIG_CNT

    int1 = str((PIG_CNT * 2) + 1)
    int2 = str((PIG_CNT * 2) + 2)
    int1veth = 'veth' + str(int1)
    int2veth = 'veth' + str(int2)
    int2addr = '192.168.' + str(PIG_CNT + 1) + '.2'

    subprocess.call(VETH_CMD + " " + int1 + " " + int2 + " " + str(PIG_CNT + 1), shell=True)
    snort = net.get(pig_name)

    '''
    # If a snort instance needs to listen on multiple interfaces, bridge.
 
    interfaces = snort.intfNames()
    snort1.cmd("brctl addbr snort_bridge")
    for intfs in interfaces:
        info('*** Adding interface ' + intfs + ' to snort_bridge' + '\n')
        snort1.cmd("brctl addif snort_bridge " + intfs)
    snort1.cmd("ifconfig snort_bridge up")
    '''

    Intf(int2veth, node=snort)

    #Inital terminal to setup a x11 tunnel for remote machines
    #TODO: add command to exit this terminal for local machines
    #net.terms += makeTerm(snort1, 'tmp')
    #time.sleep(2)
    #net.terms += makeTerm(snort1, 'Pig Relay', cmd="bash startPigrelay.sh '" + PIG_DIR+  "'")
    
    info('*** Starting PIG\n')
    snort.cmd('ifconfig ' + int2veth  + ' ' + int2addr + ' ; ' + PIG_CMD) 

    #Single ping to trigger snort discovery
    time.sleep(1)
    snort.cmd('ping 10.0.0.2 -c 1')

    PIG_CNT = PIG_CNT + 1

def clearSnortFromONOS():
    requests.get('http://' + ONOS_HOST + ':8181/mervyn/snort/clear')

def startMervyn():
    info('*** Starting Mervyn\n')
    
    if 'mervyn' in procs:
        procs['mervyn'].terminate()
 
    log = open('mervyn.out', 'a')
    procs['mervyn'] = subprocess.Popen(MERVYN_CMD, stdout=log, stderr=log, preexec_fn=os.setpgrp)

def killMervyn():
    info('*** Stopping Mervyn\n')
    procs['mervyn'].terminate()

def killPig():
    info('*** Stopping PIG\n')
    subprocess.call('pkill snort', shell=True)

def onosActivateMervyn():
    info('*** Activating ONOS Mervyn Apps\n')
    subprocess.call(MERVYN_ACTIVATE_CMD + " " + ONOS_HOST, shell=True)

def onosDeactivateMervyn():
    info('*** Deactivating ONOS Mervyn Apps\n')
    subprocess.call(MERVYN_DEACTIVATE_CMD + " " + ONOS_HOST, shell=True)

def startSFlow():
    info('*** Starting sflowtool\n')
    subprocess.call(SFLOW_ACTIVATE_CMD, shell=True)
    info('*** Starting sflow-rt\n')
    subprocess.call(SFLOWRT_ACTIVATE_CMD, shell=True)

def killSFlow():
    info('*** Killing sflowtool\n')
    subprocess.call(SFLOW_KILL_CMD, shell=True)
    info('*** Killing sflow-rt\n')
    subprocess.call(SFLOWRT_KILL_CMD, shell=True)


if __name__ == '__main__':
    setLogLevel( 'info' )

    parser = OptionParser()
    parser.add_option("-p", "--pig", dest="PIG", default=False, action="store_true", help="Start pig relay on a mininet host")
    parser.add_option("-m", "--mervyn", dest="MERVYN", default=False, action="store_true", help="Start mervyn on host machine")
    parser.add_option("-a", "--activate", dest="ACTIVATE", default=False, action="store_true", help="Active mervyn onos apps")
    parser.add_option("-d", "--deactivate", dest="DEACTIVATE", default=False, action="store_true", help="Deactivate mervyn onos apps")
    parser.add_option("-s", "--sflow", dest="SFLOW", default=False, action="store_true", help="Start mininet with sFlow")
    parser.add_option("-n", "--net", dest="NETWORK", default="A", help="Topologies A, B or C", metavar="[A/B/C]")
    (options, args) = parser.parse_args() 

    dev(options)
