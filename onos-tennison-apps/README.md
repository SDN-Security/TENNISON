# ONOS-Mervyn-Apps

## Applications

This repository contains various applications needed to use the Mervyn coordinator with ONOS

## Architecture

The MervynAPI app recieves HTTP POST requests from Mervyn. These are either Snort requests or IPFix requests. If the request is a Snort request, the app forwards the message onto the Snort App.
The Snort app adds or removes a flow rule (mirror/redirect/block) by sending ONOS a FlowRuleOperations message. Redirect and Mirror rules are stored in the SNORT table, Block rules are installed in the BLOCK table.
The port to forward to Snort for the mirror/redirect rule is hardcoded into the Snort app.
If the request to MervynAPI was a IPFix request then the IPFix service is queried, sending an InterFix event back to Mervyn.

The FlowMonitor app recieves packets from ONOS by registering as a packet processor and installs flow rules that match against each individual packet for monitoring in the IPFIX table.
The IPFix app registers to recieve FlowRuleEvents from ONOS when a flow rule is added or removed by the FlowMonitor app. When a flow rule is added a PreFix event is sent to Mervyn and when the rule is removed an IpFix event is sent to Mervyn

## Compile

To compile the apps just run the command below in the main folder.

```
mvn clean install
```

If the ONOS artifacts cannot be found you may need to run:

```
onos-buck-publish-local
```

## Install
Set OC1 in install_apps to the IP address of the (master) controller.

./install_apps

## Disclaimer
As onos updates and moves to buck, the applications may have to change over to using buck. Currently there is no guide/repositories to doing this so ONOS apps will still require maven.
