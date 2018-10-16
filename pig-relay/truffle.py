import sys
import time
import logging
import signal
import requests
import json
import threading

from flask import Flask, jsonify, request, abort, make_response, current_app

class TruffleServer(threading.Thread):
    """Server for managing Snort alerts."""

    app = Flask(__name__)
    log = logging.getLogger('werkzeug')
    # Set logging level to avoid debug messages
    log.setLevel(logging.ERROR)

    def __init__(self, snort_daemon, addr='127.0.0.1', port=80):
        """
        Initalise TruffleServer

        Args:
          snort_daemon: Reference to the thread managing Snort.
          addr: Server address
          port: Server port
        """

        threading.Thread.__init__(self)
        self.snort = snort_daemon
        self.port = port
        self.addr = addr


    def run(self):
        """
        Start the TruffleServer.
        """
        self.app.config['truffle'] = self
        self.app.run(host=self.addr, port=self.port)

    def _reload(self):
        # Refresh Snort, reload config files
        self.snort.reload()


    def _add(self, rule):
        # Add specific rule
        self.snort.add_rule(rule)


    def _delete(self, rule):
        # Delete specific rule
        self.snort.delete_rule(rule)


    def _clear(self):
        # Clear the snort rules
        self.snort.clear_rule()


    @app.route('/snort/rule/add', methods=['POST'])
    def add_rule():
        """
        Add a set of rules to the snort config
        """
        truffle = current_app.config['truffle']
        try:
            if request.headers['Content-Type'] == 'application/json':
                req = request.json
                for rule in req['rules']:
                    truffle._add(rule)

        except Exception as e:
            print "Failed adding rule: " + e.message
        return jsonify({'returncode': 1}), 200

    @app.route('/snort/rule/delete', methods=['POST'])
    def delete_rule():
        """
        Delete a set of rules from the snort config
        """
        truffle = current_app.config['truffle']
        try:

            if request.headers['Content-Type'] == 'application/json':
                req = request.json
                for rule in req['rules']:
                    truffle._delete(rule)

        except Exception as e:
            print "Failed deleting rule: " + e.message

        return jsonify({'returncode': 1}), 200


    @app.route('/snort/rule/clear', methods=['POST'])
    def clear_rules():
        """
        Clear all the current rules from snort config
        """
        truffle = current_app.config['truffle']
        try:
            truffle._clear()
        except Exception as e:
            print "Failed clearing rule: " + e.message

        return jsonify({'returncode': 1}), 200


    @app.errorhandler(404)
    def not_found(error):
        """
        If a request does not match a path, return a 'not found' (404) response.
        """

        return make_response(jsonify({'error': 'Not found'}), 404)
