

<p align="center">
  <img src="https://github.com/SDN-Security/TENNISON/blob/master/imgs/tennison_logo.png?raw=true" alt="TENNISON logo" />
</p>

TENNISON is a novel distributed SDN security framework that combines the efficiency of SDN control and monitoring with the resilience and scalability of a distributed system. TENNISON offers effective and proportionate monitoring and remediation, compatibility with widely-available networking hardware, support for legacy networks, and a modular and extensible distributed design.

For more details of this work, please see our recently published article in the IEEE Journal on Selected Areas in Communications:

```
Lyndon Fawcett, Sandra Scott-Hayward, Matthew Broadbent, Andrew Wright, and Nicholas Race
"TENNISON: A Distributed SDN Framework for Scalable Network Security."
IEEE Journal on Selected Areas in Communications (2018).
```
The article is available here: http://eprints.lancs.ac.uk/127188/1/tennison_CA.pdf

TENNISON offers the following:
* Extensibility
* Holistic view
* Rapid reaction
* Transparency and interoperability
* Kill chain detection support
* Legacy network support

TENNISON requires multiple components to function correctly. Below shows an overview of the system architecture:

<p align="center">
  <img src="https://github.com/SDN-Security/TENNISON/blob/master/imgs/new_arch_grey_compact.png?raw=true" alt="TENNISON Overview" width="600">
</p>

As TENNISON is made of many components and is designed to work at scale, testing it can be challenging. The TENNISON testing harness automates the process in varifying functional and non-functional performance before deploying a change to production:

<p align="center">
  <img src="https://github.com/SDN-Security/TENNISON/blob/master/imgs/experimenter.png?raw=true" alt="TENNISON Experimenter design" width="600" />
</p>

To get in contact about the project, please contact Lyndon at: l.fawcett1@lancaster.ac.uk.

# License
TENNISON is licensed under the Apache 2 license and is covered by [Crown Copyright](https://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/copyright-and-re-use/crown-copyright/).

# Contributors
* [Lyndon Fawcett](https://github.com/lyndon160)
* [Jamie Bird](https://github.com/biirdy)
* Sandra Scott-Hayward
* Andrew Wright
* [Matthew Broadbent](https://github.com/broadbent)
* [Richard Withnell](https://github.com/RichardWithnell)
* [Nicholas Race](https://github.com/nickrace)

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
These applications interface with ONOS. They assist in monitoring and
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

# Screenshots from GUI and Experimenter

## TENNISON Experimenter
<p align="center">
  <img src="https://github.com/SDN-Security/TENNISON/blob/master/imgs/tennison_experimenter.png?raw=true" alt="TENNISON Experimenter" width="600" />
</p>




## TENNISON GUI
<p align="center">
  <img src="https://github.com/SDN-Security/TENNISON/blob/master/imgs/tennison_gui.png?raw=true" alt="TENNISON Flows" width="600" />
</p>


<p align="center">
  <img src="https://github.com/SDN-Security/TENNISON/blob/master/imgs/topo_gui.png?raw=true" alt="TENNISON topology" width="600" />
</p>

## TENNISON Tiered Domain Manager GUI

<p align="center">
  <img src="https://github.com/SDN-Security/TENNISON/blob/master/imgs/tiered_manager_gui.png?raw=true" alt="TENNISON Tiered Domain Manager" width="600" />
</p>



