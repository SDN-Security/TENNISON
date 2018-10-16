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
from mininet.node import Controller, RemoteController, userSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import Intf
from mininet.term import makeTerm, makeTerms
from mininet.link import TCLink

from distutils.version import StrictVersion

PIG_WAIT = 5
NET_WAIT = 10
FLOW_WAIT = 20

# Infrastructure
PIG_DIR = "/home/user/secapp/pigrelay/"
PIG_CMD = "python /home/user/secapp/pigrelay/pigrelay.py --config /home/user/secapp/pigrelay/examples/config.yaml"
MERVYN_DIR = "/home/user/secapp/mervyn/"
MERVYN_CMD = "python3 /home/user/secapp/mervyn/mervyn.py --config /home/user/secapp/mervyn/examples/config.yaml --thresholds %s"
MERVYN_THRESHOLD = "/home/user/secapp/mervyn/examples/thresholds.yaml"
VETH_CMD = "/home/user/secapp/topology/SimpleTopology/components/resetVETH.sh"
ONOS_HOST = "xxx.xxx.xxx.xxx"
MERVYN_ACTIVATE_CMD = "/home/user/secapp/topology/SimpleTopology/components/activate_mervyn"
MERVYN_DEACTIVATE_CMD = "/home/user/secapp/topology/SimpleTopology/components/deactivate_mervyn"
MONITOR_CMD = "/home/user/secapp/topology/SimpleTopology/components/cpu.sh %s %s %d"
MONITOR_DIR = "/home/user/mnrec/"

# Experiment
HOSTS = 140
MODES = ['MERVYN']
MIRROR_FLOWS = [20, 40, 60, 80, 100]	#%
ITERATIONS = 20
SPEEDS = [1000, 10000]
IPERF_DUR = 6

networkNames = ['A', 'B', 'C']

def createNetworks(speed=1000):

    info('*** Creating networks\n')

    networks = [Mininet( controller=Controller, link=TCLink)]
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
        snort1 = net.addHost('snort1', ip='10.0.0.200')
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
                if "snort" not in h.name:
		    # If overrun - add remainders to last switch
                    if si < len(net.switches) - 1:
                        net.addLink(net.switches[si], h, bw=speed)
                    else:
                        net.addLink(net.switches[-1], h, bw=speed)

    return networks

def eval():

    # Eval
    onosActivateMervyn()

    for itr in range(0, ITERATIONS):

        for mflows in MIRROR_FLOWS:

	    for speed in SPEEDS:

		info('*** ITR ' + str(itr) + '\n')
		info('*** MIRROR ' + str(mflows) + '%\n')
		info('*** SPEED ' + str(speed) + '\n')

	    	networks = createNetworks(speed=speed)
	    	net = networks[0] # Just single switch for now

		info('*** Starting network\n')
	    	net.start()

	    	startPig(net, xterm=False)
	    	time.sleep(PIG_WAIT)
	    	createThresholds(hosts=selectHosts(net.hosts, 128), percentage=mflows)
		startMervyn()

	    	# Time to avoid inital OF handshake messages
	    	time.sleep(NET_WAIT)

		expName = '%d_%d_%d' % (mflows, speed, itr)
		#monitorPig(duration=IPERF_DUR, file=expName + "_snort.log")
		#monitorMervyn(duration=IPERF_DUR, file=expName + "_mervyn.log")
		#monitorONOS(duration=IPERF_DUR, file=expName + "_ONOS.log")
		CLI(net)
		net.iperfRec(hosts=selectHosts(net.hosts, 128), file_name=expName, seconds=IPERF_DUR, tcpdump=False)

	    	killMervyn()
	    	killPig()

	    	info( '*** Stopping network\n' )
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

def startPig(net, xterm=False):
    subprocess.call(VETH_CMD, shell=True)
    snort1 = net.get('snort1')
    interfaces = snort1.intfNames()
    snort1.cmd("brctl addbr snort_bridge")
    for intfs in interfaces:
        info('*** Adding interface ' + intfs + ' to snort_bridge' + '\n')
        snort1.cmd("brctl addif snort_bridge " + intfs)
    snort1.cmd("ifconfig snort_bridge up")

    Intf('veth1', node=snort1 )

    info('*** Starting PIG\n')
    if not xterm:
    	snort1.cmd('ifconfig veth1 192.168.100.2; ' + PIG_CMD + ' >> /dev/null 2>&1 &')
    else:
   	net.terms += makeTerm(snort1, 'tmp')
   	time.sleep(2)
   	net.terms += makeTerm(snort1, 'Pig Relay', cmd="bash startPigrelay.sh '" + PIG_DIR+  "'")


def createThresholds(hosts=None, percentage=10):

    mirrorCnt = (percentage * (len(hosts)-1)) / 100

    info('*** Creating thresholds.yaml to mirror ' + str(mirrorCnt) + ' flows\n')

    yaml = "ipfix:\n"
    for i in range(mirrorCnt):
	yaml = yaml + '    - {priority: 20, subtype: prefix, treatment: snort_mirror, fields: {sourceIPv4Address: ' + hosts[i+1].IP()  + '}}\n'
    yaml = yaml + "snort:\n    - {rule: 'alert icmp 8.8.8.8/32 any -> 8.8.8.8/32 any', priority: 10, treatment: snort_mirror, fields: {sourceIPv4Address: 8.8.8.8}}\n"

    info(yaml)
    f = open(MERVYN_THRESHOLD, 'w')
    f.write(yaml)
    f.close()


def monitorPig(file="noName", duration=10):
    cmd = MONITOR_CMD % ("snort", MONITOR_DIR + file, duration)
    subprocess.Popen(cmd, shell=True)

def monitorMervyn(file="noName", duration=10):
    cmd = MONITOR_CMD % ("python3", MONITOR_DIR + file, duration)
    subprocess.Popen(cmd, shell=True)

def monitorONOS(file="noName", duration=10):
    cmd = MONITOR_CMD % ("java", MONITOR_DIR + file, duration)
    subprocess.Popen(cmd, shell=True)

def startMervyn():
    info('*** Starting Mervyn\n')
    subprocess.call("pkill python3", shell=True)
    cmd = MERVYN_CMD % (MERVYN_THRESHOLD ,)
    subprocess.Popen(cmd, shell=True)

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
