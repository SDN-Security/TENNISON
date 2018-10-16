import os
import sys
import subprocess
import signal
import atexit
import time

logfile = os.path.dirname(os.path.realpath(__file__)) + "/output.log"
f = open(logfile, "w")

proc = subprocess.Popen([sys.executable, os.path.dirname(os.path.realpath(__file__)) + "/app.py"], stdout=f, stderr=f)

def cleanup(signum, frame):
    print("Stopping gui")
    proc.terminate()
    f.close()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

while True:
    time.sleep(1)
