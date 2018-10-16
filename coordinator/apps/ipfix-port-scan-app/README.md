# IPFIX port scan app

This is a northbound application of the coordinator that queries IPFIX messages and analyses them to check for port scans. If a flow is determined to be malicous, the application then creates a threshold at the coordinator to block the flow.

## Requirements
This application has no special requirements over the rest of the system.

The app runs using python 2.7.

## Usage
To run the app do:

`./ipfixportscan.py`


Configuration of thresholds and whitelists are available at `config.json`

Logs are output to `output.log`

## TODO
Make application aware of distributed port scans.

Clean the code up. There's currently a lot of redundant code.
