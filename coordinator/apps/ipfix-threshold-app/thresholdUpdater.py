import os
import Flow
import datetime
#import csv
import requests
from time import sleep
from time import mktime
from pprint import pprint
import json
from collections import OrderedDict
import pyflux as pf
import numpy as np
import logging

thresholds = {}
flows = {}
countTypes = {}
config = {}

def training():
    counterIncoherentFlows = 0
    timer = config['QueryTime']
    #Retrieve thresholds from previous run.
    retrieveThresholds()
    try:
        while True:
            r = requests.get('http://127.0.0.1:2401/tennison/ipfix/query/ipfix-threshold-app')
            logging.info('Quering IPfix messages')
            # Debug comments
            # pprint(r.json())
            # Pass to ordered dict, noticed that keeps order in iterations
            data = OrderedDict(r.json())
            for _,j in data.items():
                try:
                    # IPs
                    destinationIPv4 = j['destinationIPv4Address']
                    sourceIPv4Address =j['sourceIPv4Address']
                    # Ports
                    destinationTransportPort = j['destinationTransportPort']
                    sourceTransportPort = j['sourceTransportPort']
                    # Time
                    try:
                        flowStartMilliseconds = (mktime(datetime.datetime.strptime(j['flowStartMilliseconds'], "%Y-%m-%dT%H:%M:%S.%f").timetuple())) +\
                                                (datetime.datetime.strptime(j['flowStartMilliseconds'], "%Y-%m-%dT%H:%M:%S.%f").microsecond/1e6)
                    except  ValueError:
                        flowStartMilliseconds = (mktime(datetime.datetime.strptime(j['flowStartMilliseconds'], "%Y-%m-%dT%H:%M:%S").timetuple()))
                    try:
                        flowEndMilliseconds = (mktime(datetime.datetime.strptime(j['flowEndMilliseconds'],
                                                                                   "%Y-%m-%dT%H:%M:%S.%f").timetuple())) + \
                                                (datetime.datetime.strptime(j['flowEndMilliseconds'], "%Y-%m-%dT%H:%M:%S.%f").microsecond / 1e6)
                    except  ValueError:
                        flowEndMilliseconds = (mktime(datetime.datetime.strptime(j['flowEndMilliseconds'], "%Y-%m-%dT%H:%M:%S").timetuple()))
                    # Bytes count
                    octetDeltaCount = j['octetDeltaCount']
                    # Packet count
                    packetDeltaCount = j['packetDeltaCount']
                    # Type of IPfix
                    subType = j['subtype']
                    # Count the variety of IPfix Subtypes
                    if j['subtype'] in countTypes:
                        countTypes[j['subtype']] += 1
                    else:
                        countTypes[j['subtype']] = 1

                    flow = Flow.flow(destinationIPv4,sourceIPv4Address,destinationTransportPort,sourceTransportPort,flowStartMilliseconds,octetDeltaCount)#,
                    global flows
                    if flow.__hash__() in flows:
                        flowPriori = flows.get(flow.__hash__())
                        flowPriori.update(flowEndMilliseconds, octetDeltaCount, packetDeltaCount,subType)
                        flows[flow.__hash__() ] = flowPriori
                    else:
                        flow.update(flowEndMilliseconds,octetDeltaCount,packetDeltaCount,subType)
                        flows[flow.__hash__() ] = flow

                except KeyError:
                    counterIncoherentFlows += 1
                    continue

            sleep(timer)
            if config['type'] == 0:
                updateThresholds()
            elif config['type'] == 1:
                updateThresholdsLLT()
            else:
                print("Please define an ML type")


    except KeyboardInterrupt:

        logging.info("The total number of flows are:" + str(len(flows)))
        #TODO fix if needed
        # with open('flows.csv', 'w') as csv_file:
        #     writer = csv.writer(csv_file, lineterminator='\n')
        #     for key, value in flows.items():
        #         writer.writerow([key, str(value)])

        lst = []
        #print ("Printing Json of flows")
        for k,v in flows.items():
            d = {}
            d['FlowID'] = k
            d['values'] = v.__dict__
            lst.append(d)
        flowfile = os.path.dirname(os.path.realpath(__file__)) + "/flows.json"
        with open(flowfile, mode='w') as feedsjson:
            json.dump(lst, feedsjson, indent=4)

        #TODO fix this to string
        logging.info("The ipfix subTypes are: ")
        logging.info(json.dumps(countTypes))
        logging.info("The number of Ipfix which miss values (Incoherent) is : " + str(counterIncoherentFlows))
        print("Written to file and finished now!")

# Fetch and update the thresholds dictionary with the previous run of the same script
def retrieveThresholds():
    thresholdsQuery = requests.get('http://127.0.0.1:2401/tennison/thresholds/query')
    thresholdsData = thresholdsQuery.json()

    for key, value in thresholdsData.items():
        if key.startswith('ipfix_'):
            thresholds[int(key.split("_",1)[1])] =  float(value['threshold'])
    logging.info("Fetched " + str(len(thresholds))+ " previous setted thresholds")

def updateThresholds():

        for hash, value in flows.items():
            newValues = (len(value.delta_bps_records) - value.cutoff)
            logging.info("Comparing in updater, the number of new values is : " +str(newValues))
            if newValues >= config['minimuStep']:
                logging.info("Which is above the minimum step, working on model...")
                temp = np.array(value.delta_bps_records[-newValues:])
                avg_bps = temp.mean() + temp.std()*float(config['margin'])
                # Update if exist and do not have the same value
                if hash in thresholds and thresholds[hash] != avg_bps:
                    url = "http://127.0.0.1:2401/tennison/thresholds/ipfix/update/ipfix_" + str(hash)
                    avg_bps = avg_bps*config['exponentialSmoothing'] + (1-config['exponentialSmoothing'])*thresholds[hash]
                    # Update the cutoff to the last values
                    value.cutoff = len(value.delta_bps_records)
                # If the threshold to be updated is the same skip
                elif hash in thresholds and thresholds[hash] == avg_bps:
                    continue
                #Else add a new one
                else:#import copy
                    url = "http://127.0.0.1:2401/tennison/thresholds/ipfix/add/ipfix_" + str(hash)
                payload = {"subtype": "ipfix", "treatment": "snort_mirror", "fields":{"destinationIPv4Address":value.destinationIPv4Address,"sourceIPv4Address": value.sourceIPv4Address,"destinationTransportPort":value.destinationTransportPort,
                                                                                      "sourceTransportPort":value.sourceTransportPort }, "priority": 10,"metric":"avg_bps","threshold": int(avg_bps)}
                headers = {'content-type': 'application/json'}
                response = requests.post(url, data=json.dumps(payload), headers=headers)
                logging.info("Updating Threshold for the hash: " + str(hash))
                logging.info("With resonse codes" + str(response.status_code)+ str(response.reason))
                thresholds[hash] = avg_bps
                #Update cutoff to include only the new values on the next run
                value.cutoff = len(value.delta_bps_records)

# Using the 95% top value in the Forecasting model
# The smaller the steps ("QureyTime") the more accurate and strict it becomes
def updateThresholdsLLT():

        for hash, value in flows.items():
            newValues = (len(value.delta_bps_records) - value.cutoff)
            logging.info("Comparing in updater using the LLT, the number of values is :"+ str(newValues))

            if newValues >= config['minimuStep']:
                logging.info("Which is above the minimum step, working on model...")
                data = np.array(value.delta_bps_records)
                model = pf.LLT(data=data)
                model.fit()
                # Debug output
                # x.summary()
                # estimate the values to predict from the previous forecast
                horizon = len(data)- value.cutoff
                if horizon > 10:
                    #print("You may consider using the type 0 model")
                    logging.warning("You may consider using the type 0 model, forecast horizon is greater than 10")
                pred = model.predict(horizon,intervals=True)
                # Take the 95% highest expected value to set as a threshold.
                avg_bps = pred['95% Prediction Interval'].max()
                if hash in thresholds and thresholds[hash] != avg_bps:
                    url = "http://127.0.0.1:2401/tennison/thresholds/ipfix/update/ipfix_" + str(hash)
                # If the threshold to be updated is the same skip
                elif hash in thresholds and thresholds[hash] == avg_bps:
                    continue
                # Else add a new one
                else:
                    url = "http://127.0.0.1:2401/tennison/thresholds/ipfix/add/ipfix_" + str(hash)
                payload = {"subtype": "ipfix", "treatment": "snort_mirror",
                           "fields": {"destinationIPv4Address": value.destinationIPv4Address,
                                      "sourceIPv4Address": value.sourceIPv4Address,
                                      "destinationTransportPort": value.destinationTransportPort,
                                      "sourceTransportPort": value.sourceTransportPort}, "priority": 10,
                           "metric": "avg_bps", "threshold": int(avg_bps)}
                headers = {'content-type': 'application/json'}
                response = requests.post(url, data=json.dumps(payload), headers=headers)
                logging.info("Updating Threshold for the hash: " + str(hash))
                logging.info("With resonse codes" + str(response.status_code) + str(response.reason))
                thresholds[hash] = avg_bps
                value.cutoff = len(value.delta_bps_records)

def init():
    logfile = os.path.dirname(os.path.realpath(__file__)) + "/output.log" 
    logging.basicConfig(level=logging.INFO, filename=logfile, format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.getLogger("requests").setLevel(logging.WARNING)
    config_file = os.path.dirname(os.path.realpath(__file__)) + "/config.json"
    global config
    with open(config_file) as data_file:
        config = json.load(data_file)

    training()



