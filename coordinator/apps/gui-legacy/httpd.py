import SimpleHTTPServer
import SocketServer
import os
import signal
import sys
import socket
import time

PORT = 80

os.chdir(os.path.dirname(os.path.realpath(__file__)))

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

SocketServer.TCPServer.allow_reuse_address = True
httpd = SocketServer.TCPServer(("", PORT), Handler)    

def close(signum, frame):
    print("Stopping httpd")
    httpd.server_close()
    sys.exit(0)

signal.signal(signal.SIGINT, close)
signal.signal(signal.SIGTERM, close)

print("Starting httpd")

httpd.serve_forever()
