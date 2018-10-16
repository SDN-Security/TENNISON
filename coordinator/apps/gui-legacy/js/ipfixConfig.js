//general ipfix configuration, add/edit as needed
var ipfixConfig = 
{
    "port": "9911",
    "appId": "ipfix-visual",
    "flowActiveDuration":20000,
    "addr": "148.88.226.119"
};

//plot graph variables, add/edit as needed
var plotConfig = 
{
    //time intervals to show on the x-axis
    "axisIntervalsInMinutes" : 2
};


var referenceIpFixThreshold = 
{  
   "subtype":"none",
   "treatment":"none",
   "fields":{  
      "sourceIPv4Address":"none",
      "sourceTransportPort":-1,
      "destinationTransportPort":-1,
      "destinationIPv4Address":"none",
      "protocolIdentifier":"none"
   },
   "treatment_fields":{  
      "sourceIPv4Address":"none",
      "sourceTransportPort":-1,
      "destinationMacAddress":"none",
      "destinationTransportPort":-1,
      "sourceMacAddress":"none",
      "protocolIdentifier":"none",
      "destinationIPv4Address":"none"
   },
   "priority":-1,
   "metric":"none",
   "threshold":-1
};

var referenceSnortThreshold = {
    "alertmsg": "none", 
    "priority": -1,
    "rule":"none",
    "treatment": "block", 
    "treatment_fields":{  
      "sourceIPv4Address":"none",
      "sourceTransportPort":-1,
      "destinationMacAddress":"none",
      "destinationTransportPort":-1,
      "sourceMacAddress":"none",
      "protocolIdentifier":"none",
      "destinationIPv4Address":"none"
   }
};


var mandatoryIpFixThresholdFields = ["subtype","fields","treatment","priority"];

var digitIpfixThresholdFields = ["sourceTransportPort","destinationTransportPort","priority","threshold"];

var mandatorySnortThresholdFields = ["alertmsg","treatment","priority"];

var digitSnortThresholdFields = ["sourceTransportPort","destinationTransportPort","priority"];

