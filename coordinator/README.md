# Coordinator

The TENNISON Coordinator is responsible for receiving messages from potentially multiple IPFIX and Snort exporters. It will collect then parse these messages, and determine appropriate courses of action. The action will be determined by the highest matching threshold in the thresholds.yaml file. This may include upgrading monitoring from lightweight-detection (IPFIX) to heavyweight-detection (Snort). 

## Architecture

When initialised, tennison.py reads all the thresholds and asks rpc.py to send a list of all the Snort rules to add to pigrelay. tennison.py then starts up multiple collectors (collector.py) as daemons, with each collector only collecting one type of event (prefix, ipfix, interfix, snort, sFlowRT). These parse collected packets and place them into a distributed messaging queue (ZeroMQ). These messages are collected by tennison.py, to be passed on to messagehandler.py. At the same time a copy of the packet is sent to MongoDB. The message handler finds the highest matching threshold and sends the packet to treatment.py where the appropriate treatment from the threshold is picked. rpc.py sends a message on to the TENNISONAPI app with a request that matches the treatment. 

## Dependencies

TENNISON Coordinator is built using Python 3.x. It uses a MongoDB database to store messages received from the collectors. This can be located remotely if necessary. Please see the sample configuration file (examples/config.yaml) for details on how to connect to a remote database.

## Installation

To run the coordinator, you will first need to install the necessary Python dependencies. These can be installed with:

```pip3 install -r pip3.3requirements.txt```

```pip install -r pip2.7requirements.txt```


TODO add requirements for applications and bower.

Install python3 python python3-pip python-pip npm bower

## Running

Once the dependencies are installed, run the coordinator with:

```sudo python3 tennison.py```

Alternatively, the coordinator can also be run with a different configuration file:

```sudo python3 tennison.py --config=other_configuration_file.yaml```
