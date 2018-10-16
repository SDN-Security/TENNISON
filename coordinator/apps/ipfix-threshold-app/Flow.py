import traceback

class flow:
    destinationIPv4Address = None
    sourceIPv4Address = None
    destinationTransportPort = 0
    sourceTransportPort = 0
    startTime = 0

    counter = 0

    # Count rates of bytes or packets
    byte_diff = 0
    last_OctetObserved = -1
    packet_diff = 0
    last_observed = -1
    timeM2 = 0

    avg_time_diff = 0
    std_time_diff= 0
    avg_bps = 0
    avg_pps = 0
    delta_bps_records = []
    delta_pps_records = []

    #Count Idle time
    ipfixPrevious = False
    last_observed_ipfix = -1
    avg_time_diff_ipfix = 0
    std_time_diff_ipfix = 0
    timeM2_ipfix = 0
    # Count the ipfix messages
    counterFlow = 0
    # Count per flow basis
    byte_total_avg = 0 #octetDeltaCount
    packet_total_avg = 0 #packetDeltaCount

    # Use for the thresholdUpdateper.updateThreholds()
    cutoff = 0

    #attributes for parent information
    #Endpoint used in other connections, entropy

    #Protocol type
    #blacklist or whitelist endpoint
    #Snort stats, outputs
    #weighted Moving average
    #flow intermittent time series - average interval, average outerval and w.avg of bytes

    def __init__(self, destinationIPv4Address, sourceIPv4Address, destinationTransportPort, sourceTransportPort, flowStartMilliseconds,octetDeltaCount): #,
               #  flowEndMilliseconds,soctetDeltaCount,packetDeltaCount):
        self.destinationIPv4Address = destinationIPv4Address
        self.sourceIPv4Address = sourceIPv4Address
        self.destinationTransportPort = destinationTransportPort
        self.sourceTransportPort = sourceTransportPort
        self.startTime = flowStartMilliseconds
        self.delta_bps_records = []
        self.delta_pps_records = []
        self.last_OctetObserved = octetDeltaCount
        # The subtype ipfix counters
        self.counterFlow = 0
        self.ipfixPrevious = False
        #self.last_observed_ipfix = flowStartMilliseconds #see that, change to -1

    def update(self,flowEndMilliseconds,octetDeltaCount,packetDeltaCount,subType):

        # check if ipfixes are updated if not skip
        if (octetDeltaCount - self.last_OctetObserved) > 0:
            self.byte_diff = abs(octetDeltaCount - self.byte_diff)
            self.packet_diff = abs(packetDeltaCount - self.packet_diff)
            #Assign the subtraction between the last times otherwise if first time do End - Start of the IPfix milliseconds
            time_diff = (flowEndMilliseconds - self.last_observed) if self.last_observed != -1 else (flowEndMilliseconds - self.startTime)
            try:
                # Estimate the rate of bytes & packets
                delta_bps = self.byte_diff/time_diff
                delta_pps = self.packet_diff/time_diff
                # Update average bps and pps online
                self.avg_bps = ((self.avg_bps * self.counter) + delta_bps) / (self.counter + 1)
                self.avg_pps = ((self.avg_pps * self.counter) + delta_pps) / (self.counter + 1)
                # Take the byte & packet rate into account
                self.delta_bps_records.append(delta_bps)
                self.delta_pps_records.append(delta_pps)
            except ZeroDivisionError: #TODO Update if errors occur
                traceback.print_exc()
                print(flowEndMilliseconds)
                print(self.last_observed)
                print(octetDeltaCount)
                print(self.last_OctetObserved)
                print(flowEndMilliseconds - self.last_observed)
                print(self.destinationIPv4Address,self.destinationTransportPort,self.sourceIPv4Address,self.sourceTransportPort)
                print("Fatal error with time syncorizing, press Continue...")
                raw_input()


            #Update object values
            self.last_observed = flowEndMilliseconds
            self.counter += 1


            #Calculate the Standard Deviation of the time
            deltaTime = time_diff - self.avg_time_diff
            self.avg_time_diff += deltaTime / self.counter
            delta2Time = time_diff - self.avg_time_diff
            self.timeM2 += deltaTime * delta2Time
            if self.counter > 2:
                self.std_time_diff = self.timeM2 / (self.counter - 1)

            if self.ipfixPrevious and self.last_observed_ipfix != -1:
                # Take Idle time measurements, calculate the average and standard devation of the Idle time component
                time_diff_ipfix = flowEndMilliseconds -  self.last_observed_ipfix
                deltaTime_ipfix = time_diff_ipfix - self.avg_time_diff_ipfix
                self.avg_time_diff_ipfix += deltaTime_ipfix / self.counterFlow
                delta2Time_ipfix = time_diff_ipfix - self.avg_time_diff_ipfix
                self.timeM2_ipfix += deltaTime_ipfix * delta2Time_ipfix
                if self.counterFlow > 2:
                    self.std_time_diff_ipfix = self.timeM2_ipfix / (self.counterFlow - 1)
                self.ipfixPrevious = False





        elif (octetDeltaCount - self.last_OctetObserved) < 0 and subType != "prefix":
            print(flowEndMilliseconds)
            print(self.last_observed)
            print(octetDeltaCount)
            print(self.last_OctetObserved)
            print(flowEndMilliseconds - self.last_observed)
            print(self.destinationIPv4Address, self.destinationTransportPort, self.sourceIPv4Address,
                  self.sourceTransportPort)
            print("Fatal error with time syncronising (prefix), press Continue...")
            raw_input()





        if subType == "ipfix" :
            # Start new session for the rest update values
            self.byte_diff = 0
            self.packet_diff = 0
            self.last_observed = flowEndMilliseconds
            # Estimate the byte & packet total average per flow (from IPfix to IPfix)
            self.byte_total_avg = ((self.byte_total_avg * self.counterFlow) + octetDeltaCount) / (
            self.counterFlow + 1)
            self.packet_total_avg = ((self.packet_total_avg * self.counterFlow) + packetDeltaCount) / (
            self.counterFlow + 1)
            # Update the counter
            self.counterFlow += 1
            self.ipfixPrevious = True
            self.last_observed_ipfix = flowEndMilliseconds

            self.last_OctetObserved = 0
        else:
            #update check
            self.last_OctetObserved = octetDeltaCount


    #TODO update the function if necessary
    def strConstructor(self, byte_total_avg,packet_total_avg,avg_bps,avg_pps,avg_time_diff,std_time_diff):
        self.byte_total_avg = byte_total_avg
        self.packet_total_avg = packet_total_avg
        self.avg_bps = avg_bps
        self.avg_pps = avg_pps
        self.avg_time_diff = avg_time_diff
        self.std_time_diff = std_time_diff

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        if self.destinationIPv4Address == other.destinationIPv4Address and self.sourceIPv4Address == other.sourceIPv4Address and self.destinationTransportPort \
                == other.destinationTransportPort and self.sourceTransportPort == other.sourceTransportPort:
            return True
        else:
            return False

    def __hash__(self):
        return hash((self.destinationIPv4Address,self.sourceIPv4Address,self.destinationTransportPort,self.sourceTransportPort))

    def __repr__(self):
        return "Flow IPv4.Dest:%s, IPv4.Source:%s, PortSource:%d, PortDest:%d,\n byte_total_avg:%f, packet_total_avg:%f,avg_bps:%f, avg_pps:%f, startTime:%f, avg_time_diff:%f, std_time_diff:%f" % \
          (self.destinationIPv4Address, self.sourceIPv4Address,self.destinationTransportPort,self.sourceTransportPort,self.byte_total_avg,self.packet_total_avg,self.avg_bps,self.avg_bps,self.startTime,self.avg_time_diff,self.std_time_diff)

    def __str__(self):
        return "%s,%s,%d,%d,%f,%f,%f,%f,%f,%f,%f"% (self.destinationIPv4Address, self.sourceIPv4Address,
                                  self.destinationTransportPort,self.sourceTransportPort,self.startTime,self.byte_total_avg,self.packet_total_avg,self.avg_bps,self.avg_pps,self.avg_time_diff,self.std_time_diff)
