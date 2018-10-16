import os
from ipfixportscan import IPFIXPortScan

IPFIXPortScan(os.path.dirname(os.path.realpath(__file__)) + "/config.json")
