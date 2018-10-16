

<p align="center">
  <img src="https://github.com/SDN-Security/TENNISON/blob/master/imgs/tennison_logo.png?raw=true" alt="TENNISON logo" />
</p>
TENNISON is a network security framework that harnesses Software Defined Networks. This has been published in JSAC.

```
Fawcett, Lyndon, et al.
"TENNISON: A Distributed SDN Framework for Scalable Network Security."
IEEE Journal on Selected Areas in Communications (2018).
```

Article is available here: http://eprints.lancs.ac.uk/127188/1/tennison_CA.pdf


TENNISON's KSPs:
* Extensibility
* Holistic view
* Rapid reaction
* Transparency and interoperability
* Kill chain detection support
* Legacy network support

TENNISON requires multiple components to function correctly. Below shows an
overview of the system architecture.


<p align="center">
  <img src="https://github.com/SDN-Security/TENNISON/blob/master/imgs/tennison_overview.png?raw=true" alt="TENNISON Overview" />
</p>



Please contact Lyndon at l.fawcett1@lancaster.ac.uk about any questions on TENNISON.

# License
TENNISON is licensed under the Apache 2 license and is covered by [Crown Copyright](https://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/copyright-and-re-use/crown-copyright/).


# Getting started
**Details on getting started with TENNISON are available in docs/developer_guide.pdf**

---------------
This repository is laid out as follows:

#### _coordinator/_
This is the primary component of TENNISON and is where the policy engine is
located and is what decides what should happen to traffic. For extensibility it
has southbound and northbound interfaces.
The *southbound interfaces* are responsible for collecting a range of information
from networks and hosts. The *northbound interface* provides users/developers
with the ability to create their own security applications, providing TENNISON
with rapid reaction capability.


#### _onos-tennison-apps/_
These applications interface with ONOS. They assist in montiroing and
remediation, providing the primitives to interface with the network.

#### _pig-relay/_
This is a wrapper for snort that manages it, providing the coordinator with an 
ability to update rules and also a method of alerting the coordinator on attack
detection.


#### _onos-security-pipeline/_
This is the lowest level component of the system and sits at ONOS's driver layer
and is what realises the OpenFlow pipeline.
It has been created so that security and monitoring rules can be injected before
any forwarding is applied. This makes the system transparent at the control
plane meaning that it can work with any routing implementation. 

#### _tools/_
This directory provides scripts to automate the testing and deployment of
TENNISON, reducing the learning curve to working with TENNISON. Most of these
are wrapped in the *"tennison_experimenter"*
application.
