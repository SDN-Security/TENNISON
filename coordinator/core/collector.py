#!/usr/bin/env python3

import socketserver
import ipfix.reader
import ipfix.ie
import zmq
import threading
import ssl
import pickle
import ipaddress
import logging
import datetime
import sys

# FIXME Fix for unpickling object scope
sys.path.append('/home/ubuntu/TENNISON/coordinator/core/')
# also FIXME : For when starting from a non-relative path
sys.path.append('/home/ubuntu/TENNISON/pig-relay/')
import alert

from scapy.layers.inet import Ether, IP
from flask import Flask, jsonify, request, abort, make_response, current_app

def zmq_setup(ipc):
    """Create a context and bind an inter-process transport socket for ZeroMQ.

    This socket will send (push) messages."""
    context = zmq.Context()
    sender = context.socket(zmq.PUSH)
    sender.connect(ipc)
    return context, sender


def form_pyobj(obj, type_, subtype=None):
    """
    Modifies an alert or record in preparation for insertion into the database.
    Adds a 'time' field for TTL use. types it to ensure the message can be
    correctly attributed to the specific collector. Expands  nested dictionaries
    and converts IP address objects into integers; this process ensures
    compliance with the BSON format used in MongoDB.

    Args:
        obj: Object to be made compliant, ready for insertion into database
        type: As multiple collectors may co-exist in Mervyn, each object will be
            labelled to ensure disaggregation at the coordinator
    """
    data = {}
    if type_:
        data['time'] = datetime.datetime.utcnow()
        data['type'] = type_
        if subtype:
            data['subtype'] = subtype
    if type(obj) is dict:
        items = obj.items()
    else:
        items = obj.__dict__.items()
    for key, value in items:
        value_type = type(value)
        if key == 'exporterIPv6Address':
            # exporterIPv6Address IPFIX field is used for the DPID
            dpid = 'of:' + ':'.join('%02x' % b for b in bytes(value.packed)[8:16])
            data[key] = dpid
        elif value_type is ipaddress.IPv4Address or value_type is ipaddress.IPv6Address:
            data[key] = str(value)
        elif key == 'sourceMacAddress' or key == 'destinationMacAddress':
            data[key] = ':'.join('%02x' % b for b in value)
        elif key == 'pkt':
            data[key] = snort_pkt_values(value)
        elif hasattr(value, '__dict__'):
            data[key] = form_pyobj(value, None)
        else:
            data[key] = value
    return data

def snort_pkt_values(pkt):
    """
    """
    res = {}

    eth = Ether(pkt.encode('latin1')[0:300])

    if hasattr(eth, 'src') and hasattr(eth, 'dst'):
        res['sourceMacAddress'] = eth.src
        res['destinationMacAddress'] = eth.dst

    if 'IP' in eth:
        ip = eth.payload
        res['sourceIPv4Address'] = ip.src
        res['destinationIPv4Address'] = ip.dst
        if 'TCP' in ip:
            tcp = ip.payload
            res['protocolIdentifier'] = "tcp"
            res['sourceTransportPort'] = tcp.sport
            res['destinationTransportPort'] = tcp.dport
        elif 'UDP' in ip:
            udp = ip.payload
            res['protocolIdentifier'] = "udp"
            res['sourceTransportPort'] = udp.sport
            res['destinationTransportPort'] = udp.dport
        elif 'ICMP' in ip:
            icmp = ip.payload
            res['protocolIdentifier'] = "icmp"
            res['sourceTransportPort'] = icmp.type
            res['destinationTransportPort'] = icmp.code

    return res

class SnortCollector(threading.Thread):
    """Threaded collector for Snort alerts."""

    app = Flask(__name__)
    log = logging.getLogger('werkzeug')
    # Set logging level to avoid debug messages
    log.setLevel(logging.DEBUG)

    def __init__(self, collector, ipc):
        """Initialise the collector.

        Create a context for SSL/TLS communication. Setup ZeroMQ socket, ready
        for sending alerts to coordinator. Call Thread object initialisation
        functions.

        Args:
            collector: dictionary containing the following values:
                port: Port number for receiving Snort alerts
                subtype: As multiple collectors may co-exist in Mervyn, each
                    will be labelled to ensure disaggregation at the coordinator
                key: Path to key to be be used in SSL/TLS-secured communication
                cert: Path to certificate to be used in SSL/TLS-secured
                    communication
            ipc: Address for inter-process transport used by ZeroMQ
        """
        #self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        #self.context.load_cert_chain(collector['cert'], collector['key'])
        self.port = collector['port']
        self.zmq_context, self.app.config['zmq_sender'] = zmq_setup(ipc)
        self.app.config['type'] = 'snort'
        threading.Thread.__init__(self)

    def run(self):
        """Run the (unsecured) application until terminated."""
        # TODO Move towards SSL connection
        # self.app.run(port=self.port, debug=True, ssl_context=self.context)
        self.app.run(host='0.0.0.0', port=self.port)

    def close(self):
        """Quit the collector.

        Remove the ZeroMQ context.
        """
        self.zmq_context.destroy()

    @app.route('/snort/alert', methods=['POST'])
    def post_alert():
        """Handle POST messages sent to the Snort alert URL path.

        Unpickle sent object. Ensure each alert conforms to a consistent format.
        Send each of these alerts to the coordinator for further processing.
        Sent via a ZeroMQ socket.
        """
        try:
            # Encoding set for Python 2.7 pickle compatibility
            alert_ = pickle.loads(request.data, encoding='latin1')
            alert_ = form_pyobj(alert_, current_app.config['type'])
            current_app.config['zmq_sender'].send_pyobj(alert_)
        except Exception as e:
            print(e)
        return jsonify({'returncode': 1}), 201

    @app.errorhandler(404)
    def not_found(error):
        """
        If a request does not match a path, return a 'not found' (404) response.
        """
        return make_response(jsonify({'error': 'Not found'}), 404)





class SFlowRTCollector(threading.Thread):
    """Threaded collector for sFlowRT alerts."""

    app = Flask(__name__)
    log = logging.getLogger('werkzeug')
    # Set logging level to avoid debug messages
    log.setLevel(logging.DEBUG)

    def __init__(self, collector, ipc):
        """Initialise the collector.

        Create a context for SSL/TLS communication. Setup ZeroMQ socket, ready
        for sending alerts to coordinator. Call Thread object initialisation
        functions.

        Args:
            collector: dictionary containing the following values:
                port: Port number for receiving Snort alerts
                subtype: As multiple collectors may co-exist in Mervyn, each
                    will be labelled to ensure disaggregation at the coordinator
                key: Path to key to be be used in SSL/TLS-secured communication
                cert: Path to certificate to be used in SSL/TLS-secured
                    communication
            ipc: Address for inter-process transport used by ZeroMQ
        """
        #self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        #self.context.load_cert_chain(collector['cert'], collector['key'])
        self.port = collector['port']
        self.zmq_context, self.app.config['zmq_sender'] = zmq_setup(ipc)
        self.app.config['type'] = 'sflowrt'
        threading.Thread.__init__(self)

    def run(self):
        """Run the (unsecured) application until terminated."""
        # TODO Move towards SSL connection
        # self.app.run(port=self.port, debug=True, ssl_context=self.context)
        self.app.run(host='0.0.0.0', port=self.port)

    def close(self):
        """Quit the collector.

        Remove the ZeroMQ context.
        """
        self.zmq_context.destroy()

    @app.route('/sFlowRT/alert', methods=['POST'])
    def post_alert():
        """Handle POST messages sent to the sFlow alert URL path.

        Unpickle sent object. Ensure each alert conforms to a consistent format.
        Send each of these alerts to the coordinator for further processing.
        Sent via a ZeroMQ socket.
        """
        try:
            # Encoding set for Python 2.7 pickle compatibility
            # alert_ = pickle.loads(request.data, encoding='latin1')
            alert_ = request.get_json()
            alert_ = form_pyobj(alert_, current_app.config['type'])
            current_app.config['zmq_sender'].send_pyobj(alert_)
        except Exception as e:
            print(e)
        return jsonify({'returncode': 1}), 201


    @app.errorhandler(404)
    def not_found(error):
        """
        If a request does not match a path, return a 'not found' (404) response.
        """
        return make_response(jsonify({'error': 'Not found'}), 404)




class IPFIXCollector(threading.Thread):
    """Threaded collector for IPFIX-style (v10) exports."""

    type_ = 'ipfix'

    class CollectorDictHandler(socketserver.DatagramRequestHandler):

        def handle(self):
            """Receive and read an IPFIX packet.

            Parse each record contained within the export. Ensure each record
            conforms to a consistent format. Send each of these records to the
            coordinator for further processing. Sent via a ZeroMQ socket.
            """
            reader = ipfix.reader.from_stream(self.rfile)
            for record in reader.namedict_iterator():
                record = form_pyobj(record, self.server.type,
                                    self.server.subtype)
                self.server.zmq_sender.send_pyobj(record)

    def __init__(self, collector, ipc):
        """Initialise the collector.

        Set the default IPFIX formats. Setup ZeroMQ socket, ready for sending
        records to coordinator. Initialise UDP server with specific handler.
        Call Thread object initialisation functions.

        Args:
            collector: dictionary containing the following values:
                subtype: as multiple collectors may co-exist in Mervyn, each
                    will be labelled to ensure disaggregation at the coordinator
                port: Port number for receiving IPFIX records
            ipc: Address for inter-process transport used by ZeroMQ

        """
        self._ipfix_defaults()
        self.zmq_context, zmq_sender = zmq_setup(ipc)
        self.collector = socketserver.UDPServer(("", collector['port']),
                                                self.CollectorDictHandler)
        self.collector.zmq_sender = zmq_sender
        self.collector.type = 'ipfix'
        self.collector.subtype = collector['subtype']
        threading.Thread.__init__(self)

    def run(self):
        """Run the collector until terminated."""
        self.collector.serve_forever()

    def close(self):
        """Quit the collector.

        Close the server and remove the ZeroMQ context.
        """
        self.collector.server_close()
        self.zmq_context.destroy()

    def _ipfix_defaults(self):
        """Use the default IANA and RFC 5103 information export entities."""
        ipfix.ie.use_iana_default()
        ipfix.ie.use_5103_default()
