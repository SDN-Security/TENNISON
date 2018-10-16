import threading
import json
import yaml
import copy
import os
import subprocess
import sys
import logging
from datetime import datetime

from flask import Flask, jsonify, request, abort, make_response, current_app
from flask_cors import CORS
from pymongo import MongoClient

class DateTimeEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)

class WatsonNBI(threading.Thread):

    app = Flask(__name__)
    app.json_encoder = DateTimeEncoder
    CORS(app)

    def __init__(self, watson_config, mongo_config, ipfix_thresholds, snort_thresholds):
        threading.Thread.__init__(self)

        self.port = watson_config['port']
        self.addr = watson_config['address']

        self.mongo_client = MongoClient(mongo_config['uri'])
        self.app.config['database'] = self.mongo_client[mongo_config['database']]

        self.app.config['applications'] = {}
        self.app.config['app_procs'] = {}
        self.app.config['ipfix_thresholds'] = ipfix_thresholds
        self.app.config['snort_thresholds'] = snort_thresholds

        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
        self.log = logging.getLogger('waston')
        self.app._threshold_to_file = self._threshold_to_file

    def run(self):
        """
        Start WatsonNBI.
        """
        self.log.info("Starting default applications")
        app_path = os.path.dirname(os.path.realpath(__file__)) + "/../apps"
        installed_apps = os.listdir(app_path)

        for app in installed_apps:
            app_config_path = app_path + "/" + app + "/config.json"
            if os.path.isfile(app_config_path):
                with open(app_config_path) as data_file:
                    config = json.load(data_file)
                if 'default_app' in config and config['default_app'] == True:
                    self.log.info("Starting application " + app)
                    app_exe = ["python", app_path + "/" + app + "/main.py"]
                    proc = subprocess.Popen(app_exe)
                    self.app.config['app_procs'][app] = proc

        self.log.info("Starting watson")
        self.app.run(host=self.addr, port=self.port, debug=True, use_reloader=False)

    def close(self):
        for proc in self.app.config['app_procs']:
            self.app.config['app_procs'][proc].terminate()

    @app.route('/tennison/app/register/<app_id>', methods=['POST'])
    def register_app(app_id):
        """
        """
        logging.info("Registering app")
        current_app.config['applications'][app_id] = {'last_query_ipfix' : datetime.now(), 'last_query_snort' : datetime.now(), 'last_sflowrt_query' : datetime.now()}

        return make_response(jsonify({"success" : "ok"}), 200)

    @app.route('/tennison/app/query', methods=['GET'])
    def query_app():
        """
        Get list of applications from local install folder apps/
        """
        current_apps = current_app.config['applications']
        app_procs = current_app.config['app_procs']

        app_path_name = os.path.dirname(os.path.realpath(__file__))
        app_path_name = app_path_name + "/../apps"
        installed_apps_list = os.listdir(app_path_name)

        resp = {}
        for app in installed_apps_list:

            if app in app_procs:
                resp[app] = {"status" : "active"}
            else: 
                resp[app] = {"status" : "not_active"}
            if app in current_apps:
                resp[app].update(current_apps[app])
            try:
                #Get config of installed apps
                resp[app]['config'] = json.load(open( app_path_name + '/' + app + '/config.json'))
            except Exception as e:
                log.warning(e)




        for app in current_apps:
            if app not in installed_apps_list:
                resp[app] = current_apps[app]
                resp[app]['status'] = "not_installed" 

        logging.info("Query Apps")
        return make_response(jsonify(resp), 200)

    @app.route('/tennison/app/query/<app_id>/config', methods=['GET'])
    def query_app_config(app_id):
        """
        """
        app_path_name = os.path.dirname(os.path.realpath(__file__))
        app_path_name = app_path_name + "/../apps"
        installed_apps_list = os.listdir(app_path_name)

        if app_id not in installed_apps_list:
             return make_response(jsonify({"error" : "app not installed"}), 400)

        config_file = app_path_name + "/" + app_id + "/config.json" 

        if not os.path.isfile(config_file):
            return make_response(jsonify({"error" : "no config file"}), 400)

        with open(config_file) as data_file:
            return make_response(jsonify(json.load(data_file)), 200)

    @app.route('/tennison/app/query/<app_id>/log', methods=['GET'])
    def query_app_log(app_id):
        """
        """
        app_path_name = os.path.dirname(os.path.realpath(__file__))
        app_path_name = app_path_name + "/../apps"
        installed_apps_list = os.listdir(app_path_name)

        if app_id not in installed_apps_list:
             return make_response(jsonify({"error" : "app not installed"}), 400)

        log_file = app_path_name + "/" + app_id + "/output.log"

        if not os.path.isfile(log_file):
            return make_response(jsonify({"error" : "no log file"}), 400)

        log = str(subprocess.check_output(["tail", "-n", "20", log_file]), 'utf-8')

        return make_response(jsonify({"log" : log}), 200)

    @app.route('/tennison/app/start/<app_id>', methods=['POST'])
    def start_app(app_id):
        """
        """
        current_apps = current_app.config['applications']
        app_procs = current_app.config['app_procs']

        app_path_name = os.path.dirname(os.path.realpath(__file__))
        app_path_name = app_path_name + "/../apps"
        installed_apps_list = os.listdir(app_path_name)

        # check if installed
        if app_id not in installed_apps_list:
            return make_response(jsonify({"error" : "app not installed"}), 400)

        # check if already running
        if app_id in app_procs:
            return make_response(jsonify({"error" : "already running"}), 400) 

        # start
        app_exe = "python " + app_path_name + "/" + app_id + "/main.py"
        proc = subprocess.Popen(app_exe, shell=True)
        app_procs[app_id] = proc

        return make_response(jsonify({"success" : "ok", "pid":proc.pid}), 200)

    @app.route('/tennison/app/stop/<app_id>', methods=['POST'])
    def stop_app(app_id):
        """
        """
        app_procs = current_app.config['app_procs']

        # check if app running
        if app_id not in app_procs:
            return make_response(jsonify({"error" : "app not running"}), 400)

        # stop
        logging.info("Stopping app " + app_id)
        app_procs[app_id].kill()
        del(app_procs[app_id])
        return make_response(jsonify({"success" : "ok"}), 200)

    @app.route('/tennison/ipfix/query/<app_id>', methods=['GET'])
    def query_ipfix(app_id):
        """
        """
        logging.info("IPFIX query: " + app_id)

        applications = current_app.config['applications']
        # register app if new
        if app_id not in applications:
            applications[app_id] = {'last_query_ipfix' : datetime.now(), 'last_query_snort' : datetime.now(), 'last_query_sflowrt' : datetime.now()}

        db = current_app.config['database']
        last_query = applications[app_id]['last_query_ipfix']
        
        # get all records since last query
        query = {'type':'ipfix', 'time': {'$gt': last_query}}

        data = {}
        for item in db.alerts.find(query):
            # Move ObjectID to key
            data[str(item['_id'])] = {k:v for k, v in item.items() if k != '_id'}
        
        # update last query time
        applications[app_id]['last_query_ipfix'] = datetime.now()

        return make_response(jsonify(data), 200)

    @app.route('/tennison/snort/query/<app_id>', methods=['GET'])
    def query_snort(app_id):
        """
        """
        logging.info("snort query: " + app_id)

        applications = current_app.config['applications']
        # register app if new
        if app_id not in applications:
            applications[app_id] = {'last_query_ipfix' : datetime.now(), 'last_query_snort' : datetime.now(), 'last_query_sflowrt' : datetime.now()} 

        db = current_app.config['database']
        last_query = applications[app_id]['last_query_snort']

        # get all records since last query
        query = {'type':'snort', 'time': {'$gt': last_query}}

        data = {}
        for item in db.alerts.find(query):
            # Move ObjectID to key 
            data[str(item['_id'])] = {k:v for k, v in item.items() if k != '_id'}

        # update last query time
        applications[app_id]['last_query_snort'] = datetime.now()

        return make_response(jsonify(data), 200)

    @app.route('/tennison/sflowrt/query/<app_id>', methods=['GET'])
    def query_sflow(app_id):
        """
        """
        logging.info("sflow query " + app_id)

        applications = current_app.config['applications']
        # register app if new
        if app_id not in applications:
            applications[app_id] = {'last_query_ipfix' : datetime.now(), 'last_query_snort' : datetime.now(), 'last_query_sflowrt' : datetime.now()}

        db = current_app.config['database']
        last_query = applications[app_id]['last_query_sflowrt']

        # get all records since last query
        query = {'type':'sflowrt', 'time': {'$gt': last_query}}

        data = {}
        for item in db.alerts.find(query):
            # Move ObjectID to key & remove data
            data[str(item['_id'])] = {k:v for k, v in item.items() if k != '_id' and k != 'pkt'}

        # update last query time
        applications[app_id]['last_query_sflowrt'] = datetime.now()

        return make_response(jsonify({}), 200)

    @app.route('/tennison/thresholds/query', methods=['GET'])
    def query_threshold():
        """
        """
        logging.info("threshold query")
        data = {}
        ipfix_thresholds = current_app.config['ipfix_thresholds']
        snort_thresholds = current_app.config['snort_thresholds']
        all_thresholds = dict(list(ipfix_thresholds.items()) + list(snort_thresholds.items()))
        return make_response(jsonify(all_thresholds), 200)

    @app.route('/tennison/thresholds/ipfix/query', methods=['GET'])
    def query_ipfix_threshold():
        """
        """
        logging.info("ipfix threshold query")
        data = {}
        ipfix_thresholds = current_app.config['ipfix_thresholds']

        return make_response(jsonify(ipfix_thresholds), 200)

    @app.route('/tennison/thresholds/ipfix/query/<thresh_id>', methods=['GET'])
    def query_ipfix_threshold_singe(thresh_id):
        """
        """
        logging.info("ipfix threshold query single")
        ipfix_thresholds = current_app.config['ipfix_thresholds']
        if thresh_id not in ipfix_thresholds:
            return make_response(jsonify({"error" : "threshold not found"}), 404)
        return make_response(jsonify(ipfix_thresholds[thresh_id]), 200)

    @app.route('/tennison/thresholds/snort/query', methods=['GET'])
    def query_snort_threshold():
        """
        """
        logging.info("snort threshold query")
        data = {}
        snort_thresholds = current_app.config['snort_thresholds']
        return make_response(jsonify(snort_thresholds), 200)

    @app.route('/tennison/thresholds/snort/query/<thresh_id>', methods=['GET'])
    def query_snort_threshold_single(thresh_id):
        """
        """
        logging.info("snort threshold query single")
        snort_thresholds = current_app.config['snort_thresholds']
        if thresh_id not in snort_thresholds:
            return make_response(jsonify({"error" : "threshold not found"}), 404)
        return make_response(jsonify(snort_thresholds[thresh_id]), 200)

    @app.route('/tennison/thresholds/ipfix/add/<thresh_id>', methods=['POST'])
    def add_ipfix_threshold(thresh_id):
        """
        """
        logging.info("ipfix threshold add")
        ipfix_thresholds = current_app.config['ipfix_thresholds']

        #check if already exists
        if thresh_id in ipfix_thresholds:
            return make_response(jsonify({"error" : "threshold exists"}), 400)

        if request.headers['Content-Type'] == 'application/json':

            # check for required fields 
            req = request.json
            if not all(key in req for key in ['fields', 'subtype', 'treatment', 'priority']): 
                return make_response(jsonify({"error" : "missing value"}), 400)

            ipfix_thresholds = current_app.config['ipfix_thresholds']
            ipfix_thresholds[thresh_id] = req
            current_app._threshold_to_file()
            return make_response(jsonify({"success" : "ok"}), 200)
        else:
            return make_response(jsonify({"error" : "no data"}), 400)

    @app.route('/tennison/thresholds/ipfix/update/<thresh_id>', methods=['POST'])
    def update_ipfix_threshold(thresh_id):
        """
        """
        logging.info("ipfix threshold update")
        ipfix_thresholds = current_app.config['ipfix_thresholds']

        if thresh_id not in ipfix_thresholds:
            return make_response(jsonify({"error" : "threshold not found"}), 404)

        if request.headers['Content-Type'] == 'application/json':
            req = request.json
            for key, val in req.items():
                ipfix_thresholds[thresh_id][key] = val
            current_app._threshold_to_file()
            return make_response(jsonify({"success" : "ok"}), 200)
        else:
            return make_response(jsonify({"error" : "no data"}), 400)

    @app.route('/tennison/thresholds/ipfix/remove/<thresh_id>', methods=['POST'])
    def remove_ipfix_threshold(thresh_id):
        """
        """
        logging.info("ipfix threshold remove")
        ipfix_thresholds = current_app.config['ipfix_thresholds']
        if thresh_id not in ipfix_thresholds:
            return make_response(jsonify({"error" : "threshold not found"}), 404)

        del ipfix_thresholds[thresh_id]
        current_app._threshold_to_file()
        return make_response(jsonify({"success" : "ok"}), 200)
   
    @app.route('/tennison/thresholds/snort/remove/<thresh_id>', methods=['POST'])
    def remove_snort_threshold(thresh_id):
        """
        """
        logging.info("snort threshold remove")
        snort_thresholds = current_app.config['snort_thresholds']
        if thresh_id not in snort_thresholds:
            return make_response(jsonify({"error" : "threshold not found"}), 404)

        del snort_thresholds[thresh_id]
        return make_response(jsonify({"success" : "ok"}), 200)

    @app.route('/tennison/thresholds/snort/add/<thresh_id>', methods=['POST'])
    def add_snort_threshold(thresh_id):
        """
        """
        logging.info("snort threshold add")

        snort_thresholds = current_app.config['snort_thresholds']

        # check if already exists
        if thresh_id in snort_thresholds:
            return make_response(jsonify({"error" : "threshold exists"}), 400)

        if request.headers['Content-Type'] == 'application/json':

            # check for required fields
            req = request.json
            if not all(key in req for key in ['rule', 'treatment', 'priority']): 
                return make_response(jsonify({"error" : "missing value"}), 400)
            snort_thresholds[thresh_id] = req

            current_app._threshold_to_file()
            return make_response(jsonify({"success" : "ok"}), 200)
        else:
            return make_response(jsonify({"error" : "no data"}), 400)

    @app.route('/tennison/thresholds/snort/update/<thresh_id>', methods=['POST'])
    def update_snort_threshold(thresh_id):
        """
        """
        logging.info("snort threshold update")
        snort_thresholds = current_app.config['snort_thresholds']

        if thresh_id not in snort_thresholds:
            return make_response(jsonify({"error" : "threshold not found"}), 404)

        if request.headers['Content-Type'] == 'application/json':
            req = request.json
            for key, val in req.items():
                snort_thresholds[thresh_id][key] = val

            current_app._threshold_to_file()
            return make_response(jsonify({"success" : "ok"}), 200)
        else:
            return make_response(jsonify({"error" : "no data"}), 400)

    def _threshold_to_file(self):
        """ Save current working version of thresholds to file which can the be
        [re]loaded into the system on a restart.
        """
        ipfix_thresholds = copy.deepcopy(self.app.config['ipfix_thresholds'])
        snort_thresholds = copy.deepcopy(self.app.config['snort_thresholds'])

        # save IDs
        for key, thresh in ipfix_thresholds.items():
            thresh['id'] = key
        for key, thresh in snort_thresholds.items():
            thresh['id'] = key

        # remvoe IDs
        ipfix_thresholds = list(ipfix_thresholds.values())
        snort_thresholds = list(snort_thresholds.values())
        thresholds = {'ipfix':ipfix_thresholds, 'snort':snort_thresholds}

        # save to file
        with open('/opt/mervyn/thresholds.yaml', 'w') as outfile:
            yaml.dump(thresholds, outfile)
