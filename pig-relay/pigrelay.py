import os
import sys
import time
import socket
import logging
import six
import requests
sys.path.append('/home/vagrant/secapp/pigrelay/')
import alert
import json
import yaml
import argparse
import pickle

from Queue import Queue
from threading import Thread
from abc import ABCMeta, abstractmethod

from flask_jsonrpc.proxy import ServiceProxy

from snort import SnortDaemon
from truffle import TruffleServer

logging.basicConfig(level=logging.INFO, filename='pig.out', format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger(__name__)

BUFSIZE = 65863

# TODO: Parse network headers, simply alert structure.
class SnortListener():
    """
    Open the UNIX socket to receive alerts from the local snort server.
    """

    def __init__(self, sockfile):
        self.unsock = None
        self.sockfile = sockfile
        self.running = True

    def start_recv(self, out_q):

        print "Start recv"
        if os.path.exists(self.sockfile):
            os.unlink(self.sockfile)

        self.unsock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.unsock.bind(self.sockfile)
        logger.info("Unix Domain Socket listening...")
        self.recv_loop_producer(out_q)

    def recv_loop_producer(self, out_q):
        print "Recv loop producer"

        while self.running:
            time.sleep(0.01)
            data = self.unsock.recv(BUFSIZE)
            if data:
                logger.debug("Send {0} bytes of data.".format
                             (sys.getsizeof(data)))
                # data == 65900 byte
                out_q.put(data)

    def stop(self):
        self.running = False


class SnortRelay():
    """
    Abstract SnortRelay.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def start_send(self, in_q):
        pass


class RawSnortRelay(SnortRelay):
    """
    Sends raw alerts over a network socket
    """

    def __init__(self, address, port):
        self.nwsock = None
        self.daddr = address
        self.dport = port
        self.running = True


    def start_send(self, in_q):
        self.nwsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.nwsock.connect((self.daddr, self.dport))
        except Exception, e:
            logger.info("Network socket connection error: %s" % e)
            sys.exit()
        logger.info("Network socket sending...")
        self._send_loop_consumer(in_q)

    def _send_loop_consumer(self, in_q):
        while self.running:
            data = in_q.get()
            self.nwsock.sendall(data)
            time.sleep(0.01)
            logger.info("Send the alert messages.")

    def stop(self):
        self.running = False

class ParsedSnortRelay(SnortRelay):
    """
    Base Parsed Sender, doesnt actually send anything.
    """

    def __init__(self, verify=True):
        self.verify = verify
        self.running = True

    def start_send(self, in_q):
        logger.info("Start send")
        self._send_loop_consumer(in_q)

    def _send_event_to_server(self, msg):
        pass

    def _send_loop_consumer(self, in_q):
        logger.info("Send loop consumer")
        buf = six.binary_type()
        while self.running:
            ret = in_q.get()
            buf += ret
            while len(buf) >= BUFSIZE:
                logger.info("Received buffer size: %d", len(buf))
                data = buf[:BUFSIZE]
                msg = alert.AlertPkt.parser(data)
                if msg:
                    try:
                        self._send_event_to_server(msg)
                    except Exception as e:
                        logger.info('Exception: ' + str(e))
                buf = buf[BUFSIZE:]

    def stop(self):
        self.running = False
        


class HttpSnortRelay(ParsedSnortRelay):
    """
    Send Alert as HTTP binary data
    """

    def __init__(self, address, port, verify=True):
        ParsedSnortRelay.__init__(self, verify)
        self.daddr = address
        self.dport = port

    def start_send(self, in_q):
        logger.info("Start send")
        self._send_loop_consumer(in_q)

    def _send_event_to_server(self, msg):
        logger.info('Sending snort alert')
        url = ''.join([self.daddr, ':', str(self.dport)])
        data = pickle.dumps(msg)
        response = requests.post(url + '/snort/alert',
                                 data=data,
                                 verify=self.verify,
                                 headers={'Content-Type':
                                          'application/octet-stream'})
        logger.info(str(response))



class JsonRPCSnortRelay(ParsedSnortRelay):
    """
    Send alert to sever as JSON-RPC
    """

    def __init__(self, verify=True):
        self.verify = verify
        self.daddr = config['address']
        self.dport = config['port']
        url = ''.join(['http://', self.daddr,
                       ':',
                       str(self.dport),
                       '/api'])
        server = ServiceProxy(url)

    def start_send(self, in_q):
        print "Start send"
        self._send_loop_consumer(in_q)

    def send_event_to_server(self, msg):
        result = server.App.post()




class PigrelayDaemon():
    """
    Instance of the relay, creates instances of the listener and the sender.
    """

    def __init__(self, sockfile, address, port):
        self.sockfile = sockfile
        self.address = address
        self.port = port
        self.q = Queue()

        self.snort_listener = SnortListener(self.sockfile)
        self.snort_relay = HttpSnortRelay(self.address, self.port)

        self.listen = Thread(target=self.snort_listener.start_recv, args=(self.q, ))
        self.relay = Thread(target=self.snort_relay.start_send, args=(self.q, ))
        self.listen.setDaemon(True)
        self.relay.setDaemon(True)

    def start(self):
        # Launch the threads
        self.listen.start()
        self.relay.start()

    def join(self):
        self.listen.join()
        self.relay.join()

    def stop(self):
        self.snort_relay.stop()
        self.snort_listener.stop()


def snort_start(snort_conf):
    snort_rules = snort_conf['rule_config']
    snort_interface = snort_conf['interface']
    snort_template = None

    if 'base_rule_config' in snort_conf:
        snort_template = snort_conf['base_rule_config']

    print '%s %s %s' % (snort_rules, snort_interface, snort_template)

    snort = SnortDaemon(snort_rules, snort_interface, template=snort_template)
    snort.start()
    return snort

def add_snort_to_onos(snort_conf, onos_conf):
    snort_ip = snort_conf['address']
    url = onos_conf['address'] + ":" + str(onos_conf['port'])  + '/mervyn/snort/add/' + snort_ip
    print url
    response = requests.get(url)
    print response

def truffle_start(snort, truffle_conf):
    print truffle_conf.keys()
    truffle_address = truffle_conf['address']
    truffle_port = truffle_conf['port']
    truffle = TruffleServer(snort, truffle_address, truffle_port)
    truffle.setDaemon(True)
    truffle.start()
    return truffle


def pigrelay_start(pig_conf):
    pig_sock = pig_conf['socket_file']
    pig_address = pig_conf['alert_server']['address']
    pig_port = pig_conf['alert_server']['port']
    pig = PigrelayDaemon(pig_sock, pig_address, pig_port)
    pig.start()
    return pig

if __name__ == '__main__':
    """
    Main
    """

    if not os.geteuid() == 0:
        sys.exit("You need root permissions to start snort.")

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
                        default="examples/config.yaml",
                        type=str,
                        help="path to YAML configuration file")
    args = parser.parse_args()

    config = None

    try:
        with open(args.config, 'r') as ymlfile:
            config = yaml.load(ymlfile)
    except:
        logger.info('Config file "%s" doesn\'t exist.' % (args.config, ))
        sys.exit(-1)

    snort = snort_start(config['snort'])
    add_snort_to_onos(config['snort'], config['onos'])
    truffle = truffle_start(snort, config['truffle'])
    pig = pigrelay_start(config['pigrelay'])

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt as ki:
        logger.info('Stopping Snort...')
        snort.stop()
        logger.info('Stopping Pig Relay...')
        pig.stop()
