#!/usr/bin/env python
import os
import datetime
import requests
import logging
import json
from time import sleep
from datetime import datetime

class TieredManager():
    '''Tiered Manager. App collects data and sends it to a higher tier of TENNISON.'''

    def __init__(self, config_path):
        logfile = os.path.dirname(os.path.realpath(__file__)) + "/output.log"
        logging.basicConfig(level=logging.INFO, filename=logfile, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        with open(config_path) as data_file:    
    		self.config = json.load(data_file)
        logging.info('Starting Tiered Manager')

        logging.info("Registering app")
        r = requests.get('http://127.0.0.1:2401/tennison/app/register/tiered-maanger', timeout=1)

        self.read_ipfix()
