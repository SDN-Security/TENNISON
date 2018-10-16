#!/usr/bin/env python3

import zmq
import signal
import sys
import yaml
import argparse
import core.collector
import core.rpc

import logging
from core.messagehandler import MessageHandler
from core.watson import WatsonNBI
from core.interfixpoll import InterfixPoll

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from copy import deepcopy

class Tennison():
    """Central coordinator for Tennison. Creates collectors for Snort and IPFIX
    messages."""

    _collectors = []

    def __init__(self, config_path, threshold_path):
        """Initialise the Tennison coordinator.

        Load configuration file. Setup ZeroMQ socket. Ensure interrupt signals
        are handled by Tennison. Connext to the MongoDB database. Create
        collectors as defined in the configuration file.

        Args:
          config_path: Path for configuration file.
          threshold_path: Path for threshold definitions.

        """
	
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        self.log = logging.getLogger('tennison')
        self.log.info("Launching tennison")
        self.config = self._load_yaml_file(config_path)
        self._setup_thresholds(threshold_path)
        self._rpc_handler = core.rpc.RPC(self.config)
        self.message_handler = MessageHandler(self._ipfix_thresholds,
            self._snort_thresholds, self._rpc_handler)
        self._zmq_setup()
        signal.signal(signal.SIGINT, self._close)
        signal.signal(signal.SIGTERM, self._close)
        self._connect_to_database()
        self._setup_collectors()
        self._setup_interfix()
        #self._setup_snort()
        self._setup_watson()
        


    def _setup_thresholds(self, threshold_path):
        """Load the configuration file and store the IPFIX and Snort elements in
        local variables."""
        thresholds = self._load_yaml_file(threshold_path)
        self._ipfix_thresholds = self._extract_ipfix_thresholds(thresholds['ipfix'])
        self._snort_thresholds = self._extract_snort_thresholds(thresholds['snort'])

    def _extract_ipfix_thresholds(self, thresholds):
        ipfix_thresholds = {}
        for ti, threshold in enumerate(thresholds):
            if 'id' in threshold:
                ipfix_thresholds[threshold['id']] = threshold
                del(threshold['id'])
            else:
                ipfix_thresholds["default_ipfix_" + str(ti)] = threshold
        return ipfix_thresholds

    def _extract_snort_thresholds(self, thresholds):
        """Extract the Snort-related thresholds (those that start with 'snort')."""
        snort_thresholds = {}
        for ti, threshold in enumerate(thresholds):
            if 'id' in threshold:
                snort_thresholds[threshold['id']] = threshold
                del(threshold['id'])
            else:
                snort_thresholds['default_snort_' + str(ti)] = threshold
        return snort_thresholds

    def _load_yaml_file(self, path):
        """Loads the YAML file into an object."""
        with open(path, 'r') as ymlfile:
            return yaml.load(ymlfile)

    def _zmq_setup(self):
        """Create a context and bind an inter-process transport socket for
        ZeroMQ.

        This socket will listen (pull) for messages.
        """
        self.context = zmq.Context()
        self.receiver = self.context.socket(zmq.PULL)
        self.receiver.bind(self.config['ipc_path'])

    def listen(self):
        """Listen for new messages from connected collectors."""
        while True:
            sys.stdout.flush()
            sys.stderr.flush()
            message = self.receiver.recv_pyobj()
            try:
                self.log.debug("Message recieved") # + str(message))
                self.database.alerts.insert_one(message)
                self.message_handler.handle(message)
            except PyMongoError as e:
                # HACKY FIX - Having issues with packetDeltaCount > int64 size
                #   (i.e. signed int64 being overflowed by an unsigned int64).
                self.log.info("PyMongoError: " + str(e))
                self.log.info("Packet type: {}".format(message['type']))
                self.log.info(message)
            except OverflowError as e:
                #log.info(e)
                self.log.info("OverflowError")
                self.log.info("Packet type: {}".format(message['type']))
                self.log.info(message)

    def _connect_to_database(self):
        """Connect to the MongoDB database using the parameters given in the
        configuration file.

        Defines the index field and expiry time that should be used for TTL
        purposes.
        """
        mongodb_config = self.config['mongodb']
        self.mongo_client = MongoClient(mongodb_config['uri'])
        self.database = self.mongo_client[mongodb_config['database']]
        ttl = int(mongodb_config['ttl'])
        #TODO (l.fawcett1@lancaster.ac.uk) organise DB better - currently everything is put into alerts
        self.database.alerts.ensure_index('time',  expireAfterSeconds=ttl)

    def _setup_collectors(self):
        """Create collectors specified in the configuration file."""
        for type_, collectors in self.config['collectors'].items():
            for collector in collectors:
                new_controller = {'port': collector['port'], 'type': type_}
                if 'key' in self.config and 'cert' in self.config:
                    new_controller['key'] = self.config['key']
                    new_controller['cert'] = self.config['cert']
                if 'subtype' in collector:
                    new_controller['subtype'] = collector['subtype']
                self._collectors.append(self._collector_helper(**new_controller))

    def _collector_helper(self, **collector):
        """Creates and starts a collector based upon the type required.

        Args:
          collector: object containing the following fields:
              port: Port number for receiving alerts or records
              type: Specifices the type of collector (IPFIX or Snort)
              subtype: Specifies the subtype of collector, that may have
                additional semantics (ipfix, prefix, interfix, etc.)
              key: Path to key to be be used in SSL/TLS-secured communication
              cert: Path to certificate to be used in SSL/TLS-secured
                communication

        Returns:
          An object for the newly created collector.
        """
        ipc_path = self.config['ipc_path']
        if collector['type'] == 'ipfix':
            collector = core.collector.IPFIXCollector(collector, ipc_path)
        elif collector['type'] == 'snort':
            collector = core.collector.SnortCollector(collector, ipc_path)
        elif collector['type'] == 'sflowrt':
            collector = core.collector.SFlowRTCollector(collector, ipc_path)
        collector.setDaemon(True)
        collector.start()
        return collector

    #def _setup_snort(self):
    #    """Add the initial set of rules to the Snort. These are loaded from the
    #    configuration file."""
    #    self._rpc_handler.call('snort', 'clear')
    #    initial_snort_rules = self._parse_initial_snort_rules()
    #    self._rpc_handler.call('snort', 'add', payload=initial_snort_rules)

    def _setup_watson(self):
        self.watson = WatsonNBI(self.config['watson'], self.config['mongodb'], self._ipfix_thresholds, self._snort_thresholds) 
        self.watson.setDaemon(True)
        self.watson.start()

    def _setup_interfix(self):
        self.interfixpoll = InterfixPoll(self.config['onos'])
        self.interfixpoll.setDaemon(True) 
        self.interfixpoll.start()

    #def _parse_initial_snort_rules(self):
    #    """Parse the configuration options to form a set of rules that should
    #    be added to Snort at startup."""
    #    rules = {'rules' : []}
    #    sid = 100001
    #    for ri, rule in self._snort_thresholds.items():
    #        rule = str(rule['rule']) + ' (msg: "' + str(rule) + '"; sid:' + str(sid) + '; rev:1;)'
    #        rules['rules'].append(rule)
    #        sid+=1
    #    return rules

    def _close(self, signal, frame):
        """Quit the application and clean up.

        Destroy the ZeroMQ context. Close the connection to the database. Call
        the 'close' method on each of the created collectors. Send the
        appropriate system signal.
        """
        self.context.destroy()
        self.mongo_client.close()
        for collector in self._collectors:
            collector.close()
        self.watson.close()
        self.interfixpoll.close()
        sys.stdout.flush()
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
                        default="examples/config.yaml",
                        type=str,
                        help="path to YAML configuration file")
    parser.add_argument("-t", "--thresholds",
                        default="examples/thresholds.yaml",
                        type=str,
                        help="path to YAML thresholds definition file")
    args = parser.parse_args()
    Tennison(args.config, args.thresholds).listen()
