#!/usr/bin/env python
import os
import datetime
import requests
import logging
import json
from time import sleep
from datetime import datetime

class IPFIXDDoS():
    '''Tracks many sources to a destination to detect potential ddos attack.'''

    def __init__(self, config_path):
        logfile = os.path.dirname(os.path.realpath(__file__)) + "/output.log"
        logging.basicConfig(level=logging.INFO, filename=logfile, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        with open(config_path) as data_file:    
    		self.config = json.load(data_file)
        logging.info('Starting IPFIX DDoS')

        self.source_count = {}
        self.possible_attacks = []

        logging.info("Registering app")
        r = requests.get('http://127.0.0.1:2401/tennison/app/register/ipfix-ddos-app', timeout=1)

        self.read_ipfix()

    def read_ipfix(self):
        '''Reads ipfix records from watson'''

	while True:
	    r = requests.get('http://127.0.0.1:2401/tennison/ipfix/query/ipfix-ddos-app', timeout=1)
	    logging.info("Fetching ipfix ...")
            self.source_tracker(r.json()) 
            #TODO(l.fawcett1@lancs.ac.uk) Once threaded add to zmq here
            sleep(self.config['ipfix_interval'])

    def source_tracker(self, messages):
        '''Follows many sources to single dest of traffic to determine possible ddos attack'''
        self.sources_clean_up()
        for key, message in messages.items():

            if 'destinationIPv4Address' not in message or 'sourceIPv4Address' not in message:
                continue

            destination_key = (message['destinationIPv4Address'])
            source_key = (message['sourceIPv4Address'], message['sourceTransportPort'])
            
            # New destination
            if destination_key not in self.source_count:
                logging.info("New destination " + str(destination_key))
                self.source_count[destination_key] = {}

            # If new source - add to list
            self.source_count[destination_key][source_key] = datetime.now() 

            #logging.info("Source count for " + str(destination_key) + " on " + str(len(self.source_count[destination_key])))
            if len(self.source_count[destination_key]) > self.config['source_count_threshold']:
                if message['destinationIPv4Address'] not in self.possible_attacks:
                    logging.info("Source count for " + str(destination_key) + " exceeded with " + str(len(self.source_count[destination_key])))
                    self.install_mirror(message['destinationIPv4Address'])
                    #self.possible_attacks.append(message['destinationIPv4Address'])

    def sources_clean_up(self):
        '''Removes sources after grace period to stop false positives'''
        for dst, src_list in self.source_count.items(): 
            for src, time in src_list.items():
                age = (datetime.now() - time).total_seconds()
                if age > self.config['period']:
                    logging.info("Removing source " + str(src))
                    #del(self.possible_attacks[dst])
                    del(src_list[src]) 

    def install_mirror(self, dst):
        '''Tells the coordinator to install a mirror rule to onos.'''
        data_prefix = {'subtype' : 'prefix',
            'priority' : 10,
            'treatment' : 'snort_mirror',
            'fields' : {'destinationIPv4Address' : dst},
            'treatment_fields' : {'destinationIPv4Address' : dst}
        }


        data_interfix = {'subtype' : 'interfix',
            'priority' : 10,
            'treatment' : 'snort_mirror',
            'fields' : {'destinationIPv4Address' : dst},
            'treatment_fields' : {'destinationIPv4Address' : dst}
        }


        headers = {'content-type': 'application/json'}
        url = 'http://127.0.0.1:2401/tennison/thresholds/ipfix/add/ddos-mirror-%s-prefix' % dst.replace('.','_') 
        logging.info(url)        
        r = requests.post(url, data=json.dumps(data_prefix), headers=headers, timeout=1)

        if r.status_code != 200:
            logging.info(r.json())
        else:
            logging.warning(r.status_code)
        url2 = 'http://127.0.0.1:2401/tennison/thresholds/ipfix/add/ddos-mirror-%s-interfix' % dst.replace('.','_') 
        r = requests.post(url2, data=json.dumps(data_interfix), headers=headers, timeout=1)

        if r.status_code != 200:
            logging.info(r.json())
        else:
            logging.warning(r.status_code)
