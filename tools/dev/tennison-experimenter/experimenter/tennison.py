#!/usr/bin/python
from mininet.node import Controller, OVSSwitch, UserSwitch, RemoteController, Host
from mininet.util import quietRun, specialClass
import subprocess
from mininet.log import setLogLevel, info, warn, error, debug
import os
TennisonStaticInstallDir = '/home/lyndon/tennison/coordinator'
MongoStaticInstallDir = '/opt/mongodb'
TennisonRunCmd = 'tennison.py -c coordinator/examples/config_cluster.yaml -t coordinator/examples/thresholds.yaml'
MongodbRunCmd = 'mongodb/bin/mongod --dbpath db'

class TENNISONNode( Host ):
    def __init__(self, name, **kwargs ):

        self.portOffset = kwargs.pop('portOffset', 0)
        self.ipBase = kwargs.pop('ipBase', '192.168.123.0/24')
        self.ip = kwargs.pop('ip', '192.168.123.100')
        self.defaultGW = kwargs.pop('gw', '192.168.123.2')

        self.name = name
        kwargs.update( inNamespace=True )
        #self.alertAction = kwargs.pop( 'alertAction', 'exception' )
        Host.__init__( self, name, **kwargs )
        self.dir = '/tmp/%s' % self.name
        self.TENNISON_HOME = '/tmp'
        self.cmd( 'rm -rf', self.dir )
        self.TENNISON_INSTALL = self.unpackTENNISON( self.dir )
        #Need a port offset

        #setLogLevel( 'info' )
 #	self.setIP('192.168.100.1')
       
        #self.ONOS_ROOT = ONOS_ROOT


    def start( self ):
        """Start TENNISON on node
           env: environment var dict
           nodes: all nodes in cluster"""
        #env = dict( env )
        #env.update( ONOS_HOME=self.ONOS_HOME )
        #self.updateEnv( env )
       # self.cmd( 'cd ' + self.dir )
        info( '(starting %s) ' % self.name )
        self.cmd( MongodbRunCmd + ' > ' + self.dir + '/mongod.out 2>&1 &' )

        self.cmd( 'python3 ' + self.TENNISON_INSTALL + '/' + TennisonRunCmd  + ' > coordinator.out 2>&1 &' )

        #Run mongodb
       


        self.configPortForwarding( ports=[5000], action='D' )
        self.configPortForwarding( ports=[5000] )

        #Config port forwarding
        #info( '(starting %s) ' % self )

    def launchTENNISON( self ):
        self.cmd("")

    def intfsDown( self ):
        """Bring all interfaces down"""
        for intf in self.intfs.values():
            cmdOutput = intf.ifconfig( 'down' )
            # no output indicates success
            if cmdOutput:
                error( "Error setting %s down: %s " % ( intf.name, cmdOutput ) )

    def intfsUp( self ):
        """Bring all interfaces up"""
        for intf in self.intfs.values():
            cmdOutput = intf.ifconfig( 'up' )
            if cmdOutput:
                error( "Error setting %s up: %s " % ( intf.name, cmdOutput ) )

    def stop( self ):
        self.cmd( 'rm -rf', self.dir )
        #TODO confrim this works as expected
        self.cmd( 'pkill -9 python' )
        self.cmd( 'pkill -9 mongod' )


    def nodes( self ):
        "Return list of ONOS nodes"
        return [ h for h in self.net.hosts if isTENNISONNode( h ) ]


    def configPortForwarding( self, ports=[], action='A' ):
        """Start or stop port forwarding (any intf) for all nodes
           ports: list of ports to forward
           action: A=add/start, D=delete/stop (default: A)"""
        self.cmd( 'iptables -' + action, 'FORWARD -d', self.ipBase,
                  '-j ACCEPT' )
        for port in ports:
                ip, inport = self.ip, port + self.portOffset
                info('TENNISON ports ' + str(ip) + ':' +  str(port) + ' -> ' + str(inport) + ' \n')
                # Configure a destination NAT rule
                info( 'iptables -t nat -' + action,
                          'PREROUTING -t nat -p tcp --dport', inport,
                          '-j DNAT --to-destination %s:%s \n' % ( ip, port ) )

 
                os.system('iptables -t nat -' + action +
                          ' PREROUTING -t nat -p tcp --dport ' + str(inport) +
                          ' -j DNAT --to-destination ' + ip + ':' + str(port) )



    def isTENNISONNode( obj ):
        "Does obj claim to be some kind of TENNISONNode?"
        return ( isinstance( obj, TENNISONNode) or
                 'TENNISONNode' in type( obj ).__name__ )

    def unpackTENNISON(self, destDir):
        "Unpack TENNISON and return its location"
        cmds = ( 'mkdir -p "%s" && cd "%s"' % ( destDir, destDir) )

        #TODO make tennison into a static tar.

        tennisonDir = destDir

        result = self.cmd( cmds, shell=True, verbose=True )
        self.cmd( 'cp -r ' + TennisonStaticInstallDir + ' ' + tennisonDir )
        self.cmd( 'cp -r ' + MongoStaticInstallDir + ' ' + tennisonDir )
        self.cmd( 'mkdir -p ' + tennisonDir + '/db' )

        #Copy coordinator directory here
        return tennisonDir + '/coordinator'
