#!/usr/bin/python

"""
This example shows how to create an empty Mininet object
(without a topology object) and add nodes to it manually.
"""
import sys
import re
import time
import subprocess

from mininet.net import Mininet, VERSION
from mininet.node import Controller, RemoteController, UserSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Intf
from mininet.term import makeTerm, makeTerms
from mininet.link import TCLink

from distutils.version import StrictVersion

PIG_WAIT = 5
NET_WAIT = 5
FLOW_WAIT = 20

# Infrastructure
PIG_DIR = "/home/user/secapp/pigrelay/"
PIG_CMD = "python /home/user/secapp/pigrelay/pigrelay.py --config /home/user/secapp/pigrelay/examples/config.yaml"
MERVYN_DIR = "/home/user/secapp/mervyn/"
MERVYN_CMD = "python3 /home/user/secapp/mervyn/mervyn.py --config /home/user/secapp/mervyn/examples/config.yaml --thresholds /home/user/secapp/mervyn/examples/thresholds.yaml"
VETH_CMD = "/home/user/secapp/topology/SimpleTopology/components/resetVETH.sh"
ONOS_HOST = "xxx.xxx.xxx.xxx"
MERVYN_ACTIVATE_CMD = "/home/user/secapp/topology/SimpleTopology/components/activate_mervyn"
MERVYN_DEACTIVATE_CMD = "/home/user/secapp/topology/SimpleTopology/components/deactivate_mervyn"
MONITOR_CMD = "/home/user/secapp/topology/SimpleTopology/components/cpu.sh %s %s %d"
MONITOR_DIR = "/home/user/mnrec/"

# Experiment
HOSTS = 130
MODES = ['MERVYN', 'NORMAL']
ITERATIONS = 20
FLOWS = [16, 32, 64, 128]
IPERF_DUR = 30

networkNames = ['A', 'B', 'C']

def createNetworks():

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

        # Snort is placed here is it has port1 on each switch
        # Easier to define in SnortManager.java
        snort1 = net.addHost('snort1', ip='10.0.0.10')
        info( '*** Adding snort links\n')
        for sw in net.switches:
            net.addLink(sw, snort1)

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

def eval():

    # Eval

    for itr in range(0, ITERATIONS):

        for mode in MODES:

	    if mode == "NORMAL":
	        info('*** Setting mode to NORMAL\n')
	        onosDeactivateMervyn()
	    elif mode == "MERVYN":
	        info('*** Setting mode to MERVYN\n')
		onosActivateMervyn()
	    else:
	        info('*** Invalid mode\n')

	    networks = createNetworks()

            for ni, net in enumerate(networks):
		info('*** Starting network: ' + str(ni) + '\n')
	        net.start()

    		if mode == "MERVYN":
		    startPig(net)
		    time.sleep(PIG_WAIT)
	    	    startMervyn()

		CLI(net)

		# Time to avoid inital OF handshake messages
		time.sleep(NET_WAIT)



		for flow in FLOWS:
		    # Time to allows previous flows to expire
		    time.sleep(FLOW_WAIT)
		    expName = '%s_%s_%d_%d' % (mode, networkNames[ni], flow, itr)
		    monitorONOS(duration=IPERF_DUR, file=expName + "_ONOS.log")
		    net.iperfRec(hosts=selectHosts(net.hosts, flow), file_name=expName, seconds=IPERF_DUR, tcpdump=False)

	    	if mode == "MERVYN":
		    killMervyn()
		    killPig()
	    	info( '*** Stopping network ' + str(ni) + '\n' )
	    	net.stop()

    for net in networks:
	for host in net.hosts:
	    host.deleteIntfs()

def selectHosts(hosts, flows):
    '''
    Try and get as much variation as possible
    TODO: What if there isn't enough hosts for fows
    '''
    suitableHosts = [h for h in hosts if "snort" not in h.name]
    if flows > len(suitableHosts) - 1:
	info('UNABLE TO SELECT HOSTS\n')
	return suitableHosts

    selectedHosts = [suitableHosts[0]]
    selectedHosts.extend(suitableHosts[-flows:])
    return selectedHosts

def startPig(net):
    subprocess.call(VETH_CMD, shell=True)
    snort1 = net.get('snort1')
    interfaces = snort1.intfNames()
    snort1.cmd("brctl addbr snort_bridge")
    for intfs in interfaces:
        info('*** Adding interface ' + intfs + ' to snort_bridge' + '\n')
        snort1.cmd("brctl addif snort_bridge " + intfs)
    snort1.cmd("ifconfig snort_bridge up")

    Intf('veth1', node=snort1 )

    #Inital terminal to setup a x11 tunnel for remote machines
    #TODO: add command to exit this terminal for local machines
    #net.terms += makeTerm(snort1, 'tmp')
    #time.sleep(2)
    #net.terms += makeTerm(snort1, 'Pig Relay', cmd="bash startPigrelay.sh '" + PIG_DIR+  "'")
    info('*** Starting PIG\n')
    snort1.cmd('ifconfig veth1 192.168.100.2; ' + PIG_CMD + ' >> /dev/null 2>&1 &')

def monitorONOS(file="noName", duration=10):
    cmd = MONITOR_CMD % ("java", MONITOR_DIR + file, duration)
    subprocess.Popen(cmd, shell=True)

def startMervyn():
    info('*** Starting Mervyn\n')
    subprocess.call("pkill python3", shell=True)
    subprocess.Popen(MERVYN_CMD, shell=True)

def killMervyn():
    info('*** Stopping Mervyn\n')
    subprocess.call("pkill python3", shell=True)

def killPig():
    info('*** Stopping PIG\n')
    subprocess.call('pkill snort', shell=True)

def onosActivateMervyn():
    info('*** Activating ONOS Mervyn Apps\n')
    subprocess.call(MERVYN_ACTIVATE_CMD + " " + ONOS_HOST, shell=True)

def onosDeactivateMervyn():
    info('*** Deactivating ONOS Mervyn Apps\n')
    subprocess.call(MERVYN_DEACTIVATE_CMD + " " + ONOS_HOST, shell=True)

if __name__ == '__main__':
    setLogLevel( 'info' )
    eval()
