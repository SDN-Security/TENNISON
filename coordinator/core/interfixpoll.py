import threading
import time
import requests
import logging
class InterfixPoll(threading.Thread):

    def __init__(self, config):
        self._onos = config['uri']
        self._frequency = config['interfix_frequency']
        self.running = True 
        logging.getLogger("requests").setLevel(logging.WARNING)
        threading.Thread.__init__(self)

    def run(self):
        logging.info('Starting interfix polling')
        while self.running:
            url = 'http://' + self._onos + '/mervyn/ipfix/query'
            r = requests.get(url)
            logging.info('Interfix poll: ' + str(r.status_code))
            time.sleep(self._frequency)
        logging.info('Stopping interfix poll')

    def close(self):
        self.running = False
