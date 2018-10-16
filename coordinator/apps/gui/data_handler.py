import requests
import threading
import time
import uuid
import logging
import os
import pprint
import psutil
from requests import ConnectionError
import errno
class DataHandler():

        logfile = os.path.dirname(os.path.realpath(__file__)) + "/output.log"
        logging.basicConfig(level=logging.INFO, filename=logfile, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')


        logging.info("Loading data handler")

        __instance = None

        @staticmethod
        def getInstance():
            if DataHandler.__instance == None:
                DataHandler()
            return DataHandler.__instance


        def __init__(self, ip, port, poll_time):
            """ init singleton. """
            logging.info("Starting data handler")
            if DataHandler.__instance != None:
                raise Exception("This class is a singleton!")
            else:
                DataHandler.__instance = self

            self.apps = {}

            self.ip = ip
            self.port = port
            self.poll_time = poll_time
            self.average_traffic_count_config = 10

            #Ordered list of recorded throughput compiled from IPFIX
            self.traffic_report = []
            self.old_thresholds_length = -1

            self.traffic_dirty=0
            self.alerts_dirty=0
            self.thresholds_dirty=0

            self.traffc_average = 0

            self.disk={"used":0, "free": 0, "p_used":0, "p_free": 0}

            #List of observed alerts
            self.alerts = []

            #List of thresholds. Completely updated every poll.
            self.thresholds = []

            #Number of ONOS instances detected.
            self.ONOS_instances = []

            #Number of TENNISON instances detected.
            self.Tennison_instances = []

            th = threading.Thread(target=self.poll_coordinator)
            th.daemon=True
            th.start()


        def calculate_average_traffic():
            tmp_avg_traffic = self.traffic_report[-self.average_traffic_count_config:]
            #Bit complicated. Need to find time on traffic then average for each second.

        def update_apps(self):
            r = requests.get('http://'+self.ip+':'+self.port+'/tennison/app/query', timeout=20)

            for key, value in r.json().iteritems():
                logging.info(pprint.pformat(key))
                logging.info(pprint.pformat(value))

            self.apps = r.json()

        def poll_coordinator(self):
            #Setup connection to coordinator
            session_id = str(uuid.uuid4())

            registered = False

            while not registered:
                try:
                    r = requests.post('http://'+self.ip+':'+self.port+'/tennison/app/register/GUI-'+session_id)


                    if r.status_code == 200:
                        logging.info("Registered with coordinator")
                        registered = True
                    else:
                        logging.warning("Something went wrong registering the app. Status code :" + str(r.status_code))
                        time.sleep(1)
                except ConnectionError:
                    logging.warning("Failed to connect to " + self.ip +":"+self.port+", retrying in 1 second: ")
                    time.sleep(1)

            self.update_apps()

            while True:

                #Get IPFIX
                r = requests.get('http://'+self.ip+':'+self.port+'/tennison/ipfix/query/GUI-'+session_id, timeout=20)
                for key, value in r.json().iteritems():
                    #logging.info(pprint.pformat(value))
                    self.traffic_report.append(value)
                    self.traffic_dirty+=1


                #Get Thresholds
                r = requests.get('http://'+self.ip+':'+self.port+'/tennison/thresholds/ipfix/query', timeout=20)

                #Check if thresholds popluated yet.

                if self.thresholds != [] and self.old_thresholds_length != -1:
                    if len(self.thresholds) > self.old_thresholds_length:
                        self.thresholds_dirty = len(self.thresholds) - self.old_thresholds_length
                #logging.info(pprint.pformat(r.json()))
                logging.info("Dirty thresholds: " + str(self.thresholds_dirty))


                self.old_thresholds_length = len(self.thresholds)
                self.thresholds=[]
                for key, value in r.json().iteritems():

                    if "treatment_fields" not in value:
                        value['treatment_fields'] = ''

                    self.thresholds.append([key, str(value['fields']), value['priority'], value['subtype'], value['treatment'], str(value['treatment_fields'])])
                    #logging.info(pprint.pformat(key))
                    #logging.info(pprint.pformat(value))


                #Get Alerts
                r = requests.get('http://'+self.ip+':'+self.port+'/tennison/snort/query/GUI-'+session_id, timeout=20)
                for key, value in r.json().iteritems():
                    alert = [value.get('time'), value.get('alertmsg'), value.get('pkt').get('sourceIPv4Address'), value.get('pkt').get('destinationIPv4Address'), value.get('pkt').get('sourceTransportPort'), value.get('pkt').get('destinationTransportPort'), value.get('pkt').get('protocolIdentifier')]
                    self.alerts.append(alert)
                    self.alerts_dirty+=1

                #Get storage
                tmp_disk=psutil.disk_usage("/")
                self.disk['used'] = tmp_disk.used/1073741824
                self.disk['free'] = tmp_disk.free/1073741824
                self.disk['p_used'] = tmp_disk.percent
                self.disk['p_free'] = 100-tmp_disk.percent

                time.sleep(self.poll_time)
