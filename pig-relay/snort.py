import os
import sys
import time
import logging
import signal
import json
import subprocess
import threading

from shutil import copyfile

from Queue import Queue
from Queue import Empty

logger = logging.getLogger(__name__)

class SnortUpdateThread(threading.Thread):
    """
    threading.Thread to deal with writing to the snort file
    """

    def __init__(self, queue, cb, rule_file, rule_template=None):
        """
        """

        threading.Thread.__init__(self)
        self._queue = queue
        self.rule_file = rule_file
        self.rule_template = rule_template
        self.running = True
        self.cb = cb

    def run(self):
        """
        """

        while self.running:
            try:
                rule = self._queue.get(timeout=1)
                logger.info(str(rule))
                self._process_rule(rule)
                if self.cb != None:
                    self.cb()
            except Empty as empty:
                pass
            except Exception as e:
                print 'Exception processing rule: ' + e.message
                print(type(e))
                print(e)


    def stop(self):
        """
        """
        self.running = False


    def _process_rule(self, rule):
        # Process the rule queue
        if rule['type'] == 'add':
            self._add_rule(rule['rule'])
        elif rule['type'] == 'delete':
            self._delete_rule(rule['rule'])
        elif rule['type'] == 'clear':
            self._clear_rules()


    def _check_rule(self, rule):
        #TODO: Validate a rule && compare with current config file
        pass


    def _clear_rules(self):
        # Clear all rules and replace with the template, or an empty file
        # if the template does not exist.
        logger.info('Clearing rules')
        if self.rule_template is not None:
            logger.info('Using the rule template ' + self.rule_template)
            copyfile(self.rule_template, self.rule_file)
        else:
            with open(self.rule_file, 'w'):
                pass


    def _add_rule(self, rule):
        # Append a literal Snort Rule to the rules file
        logger.info('Adding a rule')
        with open(self.rule_file, 'a') as f:
            f.write(rule + '\n')


    def _delete_rule(self, rule):
        # Delete a literal Snort Rule from the rules file
        lines = []
        logger.info('Deleting a rule')
        with open(self.rule_file, 'r') as f:
            lines = f.readlines()

        with open(self.rule_file, 'w') as f:
            for line in lines:
                if line != rule + '\n':
                    f.write(line)


class SnortDaemon(object):
    """
    Instance of Snort
    """

    def __init__(self, rule_file, interface='eth0', template=None):
        """
        """
        self.rule_file = rule_file
        self.rule_template = template
        self.interface = interface
        self._queue = Queue()
        self._lock = threading.RLock()

        def callback():
            self.reload()

        self._update_thread = SnortUpdateThread(self._queue,
                                                callback,
                                                rule_file,
                                                rule_template=template)
        self._update_thread.setDaemon(True)


    def start(self):
        """
        """
        with self._lock:
            if not hasattr(self, '_proc'):
                self._update_thread.start()

            command = ['snort', '-i', self.interface, '-A', 'unsock', '-l', '/tmp', '-c', self.rule_file]
            logger.info('Starting Snort')
            f = open("snort.out", "w")
            self._proc = subprocess.Popen(command, stdout=f, stderr=f)

    def stop(self):
        """
        """

        with self._lock:
            if not hasattr(self, '_proc'):
                return
            try:
                if self._proc.poll() is None:
                    self._proc.kill()
            except Exception as e:
                print 'Failed stopping update thread'
                print(type(e))
                print(e)

    def _send_sighup(self):
        """
        """

        self._proc.send_signal(signal.SIGHUP)


    def reload(self):
        """
        """
        logger.info("Reloading Snort")
        self._send_sighup()
        self.stop()
        self.start()

    def add_rule(self, rule):
        """
        """

        self._queue.put({'type':'add', 'rule': rule})


    def delete_rule(self, rule):
        """
        """

        self._queue.put({'type':'delete', 'rule': rule})


    def clear_rule(self):
        """
        """

        self._queue.put({'type':'clear'})
