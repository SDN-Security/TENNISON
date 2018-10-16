import os

from ipfix_ddos import IPFIXDDoS

IPFIXDDoS(os.path.dirname(os.path.realpath(__file__)) + "/config.json")
