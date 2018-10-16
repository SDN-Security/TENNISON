#!/usr/bin/python
import os
from flask import Flask, url_for, redirect, render_template, request, send_from_directory, session
from threading import Lock
import threading
import flask_admin as admin
import flask_login as login
import json
from data_handler import DataHandler
import logging
import requests
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect

from views import AdminIndexView, BlankView
from user import User

with open(os.path.dirname(os.path.realpath(__file__)) + "/config.json") as data_file:
        config = json.load(data_file)


print "thread test " + str(threading.current_thread())
# Run data collector

# Create Flask application
async_mode = None
app = Flask(__name__)
#app.config['SERVER_NAME'] = '0.0.0.0:'+config['web_port']
socketio = SocketIO(app, async_mode=async_mode)
data_handler = DataHandler(config['coordinator_ip'], config['coordinator_port'], config['coordinator_poll_time'] )
thread = None
thread_lock = Lock()


logfile = os.path.dirname(os.path.realpath(__file__)) + "/output.log"
logging.basicConfig(level=logging.INFO, filename=logfile, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')




def background_thread():
    """Sends server generated events to clients"""
    count = 0
    while True:
        socketio.sleep(1)
        if ipfix_available():
            records = get_new_ipfix()
            #Loop through messages and send them to appropriate events
            logging.info("Updating ipfix to clients")
            socketio.emit('ipfix_update',
                          records,
                          namespace='')
        if thresholds_available():
            thresholds = get_new_ipfix()
            #Loop through messages and send them to appropriate events
            logging.info("Updating thresholds to clients")
            socketio.emit('threshold_update',
                          thresholds,
                          namespace='')

        if alert_available():
            alerts = get_new_alert()
            #Loop through messages and send them to appropriate events
            logging.info("Updating alerts to clients")
            socketio.emit('alert_update',
                          alerts,
                          namespace='')

def send_alert(message):
    pass

def send_threshold(message):
    pass

def send_throughput(message):
    pass

def snort_detected(message):
    pass

def snort_disconnected(message):
    pass

def ONOS_connected(message):
    pass

def ONOS_disconnected(message):
    pass

def current_throughput(message):
    pass

def message_available():
    pass

def thresholds_available():
    if data_handler.thresholds_dirty>0:
        return True
    else:
        return False

def alert_available():
        if data_handler.alerts_dirty>0:
            return True
        else:
            return False

def get_new_alert():
    tmp_alerts = data_handler.alerts[-data_handler.alerts_dirty:]
    data_handler.alerts_dirty=0

    rtn_alerts = tmp_alerts

    return rtn_alerts


def ipfix_available():
    if data_handler.traffic_dirty>0:
        return True
    else:
        return False

def get_new_ipfix():
    tmp_records = data_handler.traffic_report[-data_handler.traffic_dirty:]
    data_handler.traffic_dirty=0

    rtn_records = []

    for report in tmp_records:
        rtn_records.append([report.get('time'), report.get('subtype'), report.get('sourceIPv4Address'),  report.get('destinationIPv4Address'), report.get('sourceTransportPort'), report.get('destinationTransportPort'), report.get('octetDeltaCount')])


    return rtn_records


def get_messages():
    pass


# bower_components
@app.route('/bower_components/<path:path>')
def send_bower(path):
    return send_from_directory(os.path.join(app.root_path, 'bower_components'), path)

@app.route('/dist/<path:path>')
def send_dist(path):
    return send_from_directory(os.path.join(app.root_path, 'dist'), path)

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory(os.path.join(app.root_path, 'js'), path)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

# Initialize flask-login
def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)

# Flask views
@app.route('/')
def index():
    return render_template("sb-admin/redirect.html", async_mode=socketio.async_mode)


@socketio.on('my_event', namespace='')
def test_message(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})


@socketio.on('connect', namespace='')
def test_connect():
    global thread
    data_handler.traffic_dirty=0
    data_handler.thresholds_dirty=0
    data_handler.alerts_dirty=0
    with thread_lock:
        if thread is None:
           thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})


@socketio.on('activate', namespace='')
def activate(message):
    logging.info("Activate: " + message['appid'])
    #Activate app
    r = requests.post('http://'+config['coordinator_ip']+':'+config['coordinator_port']+'/tennison/app/start/'+message['appid'])

    if r.status_code == 200:
        logging.info("App activated")
        logging.info(r.json())
    else:
        logging.warning("Something went wrong activating the app. Status code :" + str(r.status_code))

    data_handler.update_apps()

@socketio.on('deactivate', namespace='')
def deactivate(message):
    logging.info("Deactivate: " + message['appid'])
    #Activate app
    r = requests.post('http://'+config['coordinator_ip']+':'+config['coordinator_port']+'/tennison/app/stop/'+message['appid'])

    if r.status_code == 200:
        logging.info("App deactivated")
    else:
        logging.warning("Something went wrong deactivating the app. Status code :" + str(r.status_code))

    data_handler.update_apps()


@socketio.on('my_ping', namespace='')
def ping_pong():
    emit('my_pong')



@socketio.on('disconnect', namespace='')
def test_disconnect():
    print('Client disconnected', request.sid)



# Initialize flask-login
init_login()

# Create admin
admin = admin.Admin(app,
    'TENNISON Operator Interface',
    index_view=AdminIndexView())
#admin.add_view(BlankView(name='Blank', url='blank', endpoint='blank'))

if __name__ == '__main__':
    socketio.run(app, debug=True, use_reloader=False, host='0.0.0.0')
