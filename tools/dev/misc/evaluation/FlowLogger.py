#!/usr/bin/env python
import logging
import subprocess
import time

class FlowLogger():
    "Simple topology example."

    def __init__(self):
        "Create mervyn topo."

        logging.basicConfig(level=logging.INFO, filename='experiment.log', format='%(asctime)s - %(name)s - %(message)s')
        self.log_dumpflows()

    def log_dumpflows(self):
        while True:
            flows = subprocess.check_output(['sudo', 'ovs-ofctl', 'dump-flows', 's01'])
            logging.info(flows)
            time.sleep(0.2)

# if the script is run directly (sudo topology/base.py):
if __name__ == '__main__':
    FlowLogger()
