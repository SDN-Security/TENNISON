import signal
import time
import math
from multiprocessing import Pool

import sys
import os
import traceback

class AlarmError(Exception):
    pass

class AlarmTimer:
    def __init__(self, timeout = 0):
        self.timeout = timeout
    def exception_handler(self, signum, frame):
        raise AlarmError("Timer ran out, over " + str(self.timeout) + "s!")
    def __enter__(self):
        if self.timeout > 0:
            signal.signal(signal.SIGALRM, self.exception_handler)
            signal.alarm(self.timeout)
    def __exit__(self, type, value, traceback):
        if self.timeout > 0:
            signal.alarm(0)

def loopperf(hosts, proto='TCP', udpBw='10M', fmt=None, seconds=3, port=5001): 
    global net
    m = None
    count = 0
    pos = 0
    timeout = seconds + 1
    if proto == 'UDP':
        pos = 1
    try:
        for h in hosts:
            while h.waiting:
                h.monitor()
        if proto == 'TCP':
            with AlarmTimer(timeout):
                m = net.iperf(hosts, proto, udpBw, fmt, seconds,  port)
        else:
            m = net.iperf(hosts, proto, udpBw, fmt, seconds,  port)
        while (m != None and (m[0+pos] == '' or m[1+pos] == '')):
            for h in hosts:
                while h.waiting:
                    h.monitor()
            if count < 3:
                if proto == 'TCP':
                    with AlarmTimer(timeout):
                        m = net.iperf(hosts, proto, udpBw, fmt, seconds,  port)
                else:
                    m = net.iperf(hosts, proto, udpBw, fmt, seconds,  port)
            	count += 1
            else:
                if m[0+pos] == '':
                    m[0+pos] = "Unknown"
                if m[1+pos] == '':
                    m[1+pos] = "Unknown"
        return m
    except KeyboardInterrupt:
        print "Interrupt"
        for h in hosts:
            h.sendInt()
            h.waitOutput()
        if m is not None:
            if m[0+pos] == '':
                m[0+pos] = "Unknown"
            if m[1+pos] == '':
                m[1+pos] = "Unknown"
        else:
            m = ["Unknown", "Unknown"]
            if proto == "UDP":
                m = [udpBw, m[0], m[1]]
        return m
    except Exception as e:
        if type(e) is AlarmError:
            print e
            m = ["Unknown", "Unknown"]
            signal.alarm(0)
            for h in hosts:
                h.sendInt()
                h.waitOutput()
            return m
        else:
            raise e

def run(net): 
    globals()['net'] = net

    udpBw = '10M'
    seconds = 3

    esttime = (len(net.hosts)*len(net.hosts)*2*seconds) + 100 + (len(net.hosts)*2*seconds)
    print("Estimated time: " + str(int(math.floor(esttime/60))) + "m" + str(esttime % 60) + "s")
    time.sleep(5)

    try:
        print("Running first pings to fix pings")
        net.ping([x for x in net.hosts if "snort" not in x.name], "1")
        time.sleep(5)          

        print("Running second pings to initialise remaining rules")
        net.ping([x for x in net.hosts if "snort" not in x.name], "1")

        print("Waiting 30s for rules to initialise (hopefully)")
        time.sleep(30)

        print("Running final pings for iperfs")
        pings = net.pingFull([x for x in net.hosts if "snort" not in x.name], "3")

        print("Waiting 30s for flows to timeout")
        time.sleep(30)

        iperfs = []
        for x in pings:
            if (x[0].pid != x[1].pid and x[2][1] == 1):
                m = loopperf([x[0], x[1]], 'TCP', seconds=seconds)
                iperfs.append([x[0].name, x[1].name, m])
            elif (x[2][1] == 0):
                iperfs.append([x[0].name, x[1].name, ["Link", "Down"]])

        iperfsudp = []
        for x in pings:
            if (x[0].pid != x[1].pid):
                m = loopperf([x[0], x[1]], 'UDP', udpBw=udpBw, seconds=seconds)
                iperfsudp.append([x[0].name, x[1].name, m[1:]])

        print("***iperf TCP Summary")
        for item in iperfs:
            if item != None:
    	        print str(item[0] + ' <> ' + item[1] + ' -> ' + item[2][0] + ' ' + item[2][1])

        print("***iperf UDP Summary at " + udpBw)
        for item in iperfsudp: 
            if item != None:
    	        print str(item[0] + ' <> ' + item[1] + ' -> ' + item[2][0] + ' ' + item[2][1])
    except Exception as e:
        print e
        print type(e)
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb)
    finally:
        for h in net.hosts:
            if "snort" not in h.name:
                while h.waiting:
                    h.monitor()
        os.kill(os.getpid(), signal.SIGINT)



