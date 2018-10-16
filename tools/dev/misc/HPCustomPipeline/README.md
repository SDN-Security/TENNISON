*HP Custom Pipeline
This shows how it is possible to create a custom pipeline from within ONOS. It has been added as an additional "handshake" after the default handshake when ONOS finds a new switch. However, as it is implemented this way it means that the pipeline must be known and set before finding the switch. It could possibly be done elsewhere. There is an example pipeline that shows how it can be done. Read the OF v1.3 spec and look for "OFPMP_TABLE_FEATURES". 

**Physical Switch
This has not been tested.

Place the HPSwitchHandshaker.java file in $ONOS_ROOT/drivers/default/src/main/java/org/onosproject/driver/handshaker. In here, we add an additional handshake to the end of the default handshake that sets up the topology we want.

Change the "HP" driver to use the handshaker by adding an additional behaviour in onos-drivers.xml in $ONOS_ROOT/drivers/default/src/main/:

    <driver name="hp" extends="default"
            manufacturer="HP" hwVersion="" swVersion="">
        <behaviour api="org.onosproject.net.behaviour.Pipeliner"
                   impl="org.onosproject.driver.pipeline.SecurityPipeline"/>
        <behaviour api="org.onosproject.openflow.controller.driver.OpenFlowSwitchDriver"
                   impl="org.onosproject.driver.handshaker.HPSwitchHandshaker"/>
    </driver>

Then, you can customise the pipeline within the setCustomPipeline method in the handshaker file.

Build ONOS fully using mvn clean install or just the modules changed with mvn clean install -pl :onos-drivers,:onos-of-ctl

**Mininet with CPqD
OVS does not support multipart requests yet so to be able to use custom pipelines in Mininet we must another switch. We decided to use CPqD. Follow these instructions to install CPqD:
http://tocai.dia.uniroma3.it/compunet-wiki/index.php/Installing_and_setting_up_OpenFlow_tools#Installing_OpenFlow_1.3_software_switch_.28CPqD.29

***Mininet
In your mininet topology, change the switches so they use CPqD:
s0 = net.addSwitch( 's0' , cls=UserSwitch)

or:

net = Mininet( controller=Controller, switch=UserSwitch)

***ONOS
Place the HPSwitchHandshaker.java file in $ONOS_ROOT/drivers/default/src/main/java/org/onosproject/driver/handshaker. In here, we add an additional handshake to the end of the default handshake that sets up the topology we want.

Change the "spring-open-cpqd" driver to use the handshaker by adding an additional behaviour in onos-drivers.xml in $ONOS_ROOT/drivers/default/src/main/:

    <driver name="spring-open-cpqd" extends="default"
            manufacturer="Stanford University, Ericsson Research and CPqD Research"
            hwVersion="OpenFlow 1.3 Reference Userspace Switch" swVersion=".*">
        <behaviour api="org.onosproject.net.behaviour.Pipeliner"
                   impl="org.onosproject.driver.pipeline.SpringOpenTTP"/>
        <behaviour api="org.onosproject.openflow.controller.driver.OpenFlowSwitchDriver"
                   impl="org.onosproject.driver.handshaker.HPSwitchHandshaker"/>
    </driver>

Replace the OFChannelHandler.java file in $ONOS_ROOT/protocols/openflow/ctl/src/main/java/org/onosproject/openflow/controller/impl. This has a fix that stops the CpQD handshake failing.

Then, change customise the pipeline and build ONOS as detailed above.

