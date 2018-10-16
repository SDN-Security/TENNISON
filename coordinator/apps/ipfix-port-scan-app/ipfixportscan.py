#!/usr/bin/env python
import os
import datetime
import csv
import requests
import sys
import logging
from time import sleep
from time import mktime
from pprint import pprint
import json
from collections import OrderedDict
import random
import time
thresholds = {}
flows = {}
countTypes = {}

class IPFIXPortScan():
    '''Simple Mervyn northbound application that reads ipfix/interfix records
       whilst comparing them looking for port scan attacks.'''    

    def __init__(self, config_file):
        logfile = os.path.dirname(os.path.realpath(__file__)) + "/output.log"
        logging.basicConfig(level=logging.INFO, filename=logfile, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
	logging.getLogger("requests").setLevel(logging.WARNING)

	with open(config_file) as data_file:    
    		self.config = json.load(data_file)
        logging.info('Starting ipfix port scan')
        self.flow_to_port_dict = {}
        self.treated_flows = []
        self.time_last_treat = time.time()
	#TODO Keep trying this but throw warning if doesnt work
        registered = False

	while not registered:
	    r = requests.post('http://127.0.0.1:2401/tennison/app/register/ipfix-port-scan-app')
            if r.status_code == 200:
                registered = True
            else:
                logging.warning("Something went wrong registering the app. Status code :" + str(r.status_code))
                sleep(1)
 
        try:
            self.read_ipfix()
	except KeyboardInterrupt:
	    logging.info("The total number of flows are: " + str(len(flows)))
            
            logging.info("Treated flows: " + str(len(self.treated_flows)))
            logging.info(self.treated_flows)

    def read_ipfix(self):
        '''Reads ipfix records from watson'''

	while True:
	    r = requests.get('http://127.0.0.1:2401/tennison/ipfix/query/ipfix-port-scan-app')
            
            flows = r.json()
            if len(flows) > 0:
	        logging.info("Fetching ipfix ...")
            logging.info("Retrieved records: " + str(len(flows)))
	    #data = OrderedDict(r.json())
            #flows = json.load(r.json())           
            self.flows_to_port_tracker(flows) 
            #TODO(l.fawcett1@lancs.ac.uk) Once threaded add to zmq here
            sleep(1)

    def treat_flow(self, l3flow):
        '''This method will send a call to watson NBI adding a threshold to mirror or block flow'''
        self.treated_flows.append(l3flow)
        logging.info("Treating " + str(l3flow))
        threshId = str(random.getrandbits(20))

        url = "http://127.0.0.1:2401/tennison/thresholds/ipfix/add/portscan_prefix_" + threshId
        payload = {
            "subtype": "prefix", \
            "treatment": "block", \
            "fields":{"sourceIPv4Address": l3flow[0]}, \
            "treatment_fields":{"sourceIPv4Address": l3flow[0]}, \
            "priority": 10 \
        }
	headers = {'content-type': 'application/json'}
	response = requests.post(url, data=json.dumps(payload), headers=headers)
	logging.info("Creating Threshold")
	logging.info(str(response.status_code) +  str(response.reason))

	url = "http://127.0.0.1:2401/tennison/thresholds/ipfix/add/portscan_interfix_" + threshId
	payload = {
	    "subtype": "interfix", \
	    "treatment": "block", \
	    "fields":{"sourceIPv4Address": l3flow[0]}, \
	    "treatment_fields":{"sourceIPv4Address": l3flow[0]}, \
	    "priority": 10 \
	}

	response = requests.post(url, data=json.dumps(payload), headers=headers)
	logging.info("Creating Threshold")
	logging.info(str(response.status_code) +  str(response.reason))

    def track_distributed_scan(self):
       '''This method checks for distributed scans. E.g. if one source IP was hitting a lot other nodes on the same port'''
       #TODO(l.fawcett1@lancs.ac.uk) Iterate over flow to port and determine if distributed scan occuring.

    def flows_to_port_tracker(self, flows):
        for flow in flows.values():
            self.flow_to_port_tracker(flow)

    def flow_to_port_tracker(self, flow):
        '''This extracts a L3 flow from input flow, then creates a set of ports
           that the flow is using, which are then counted.'''
        if 'sourceIPv4Address' not in flow and 'destinationIPv4Address' not in flow:
            return

	key = (flow['sourceIPv4Address'], flow['destinationIPv4Address'])
        logging.info("================")

        if key not in self.flow_to_port_dict:
            self.flow_to_port_dict[key] = {flow['destinationTransportPort']}
        else:
            if self.flow_to_port_dict[key] is not None:
                 self.flow_to_port_dict[key].add(flow['destinationTransportPort'])
        logging.info(str(key) + " has used " + str(len(self.flow_to_port_dict[key])) + " ports")
        logging.info(self.flow_to_port_dict[key])

        #If this is true then port scan has been detected
        if(len(self.flow_to_port_dict[key])>self.config['port_threshold_count']):
            if key not in self.treated_flows:
                self.time_last_treat = time.time() 
                self.treat_flow(key)
            #This is done because mirror rules now expire
            else:
                 if(time.time()-self.time_last_treat > 10):
                     self.time_last_treat = time.time() 
                     self.treat_flow(key)



