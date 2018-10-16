# PigRelay

PigRelay installs the appropriate Snort rules from Mervyn and relays Snort alerts back to Mervyn. PigRelay reads these Snort alerts from a unix socket and transmits back to Mervyn using HTTP POST. The server configuration is present in examples/config.yaml

## Architecture

PigRelay starts pigrelay.py which then intialises snort.py and truffle.py as daemons. truffle.py recieves the Snort rules to add from Mervyn and sends them to snort.py which first resets the base rules file by replacing it with the template file (if it exists) and then adds the rules it recieved. Snort reads from this base rules file when its initialised and then listens for incoming packets on the interface set in the config file. When Snort generates alerts, pigrelay.py reads from the socket file and forwards the alert on to Mervyn using HTTP POST.

## Dependencies

PigRelay is built using Python 2.x. To run pigrelay, you will first need to install the necessary Python dependencies. These can be installed with:

```pip install -r requirements.txt```

## Running

Once the dependencies are installed, run pigrelay with:

```sudo python pigrelay.py```

