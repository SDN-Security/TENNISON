/*
 * Copyright 2015 Open Networking Laboratory
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.onosproject.ipfix;

import static com.google.common.base.Strings.isNullOrEmpty;
import static org.onlab.util.Tools.get;

import java.util.ArrayList;
import java.util.Dictionary;
import java.util.HashMap;

import org.apache.felix.scr.annotations.Activate;
import org.apache.felix.scr.annotations.Component;
import org.apache.felix.scr.annotations.Deactivate;
import org.apache.felix.scr.annotations.Modified;
import org.apache.felix.scr.annotations.Property;
import org.apache.felix.scr.annotations.Reference;
import org.apache.felix.scr.annotations.ReferenceCardinality;
import org.apache.felix.scr.annotations.Service;
import org.onlab.packet.Ethernet;
import org.onlab.packet.IPv4;
import org.onlab.packet.IPv6;
import org.onlab.packet.Ip4Address;
import org.onlab.packet.IpAddress;
import org.onlab.packet.TpPort;
import org.onosproject.cfg.ComponentConfigService;
import org.onosproject.core.ApplicationId;
import org.onosproject.core.CoreService;
import org.onosproject.net.Device;
import org.onosproject.net.DeviceId;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.flow.DefaultTrafficSelector;
import org.onosproject.net.flow.DefaultTrafficTreatment;
import org.onosproject.net.flow.FlowEntry;
import org.onosproject.net.flow.FlowRule;
import org.onosproject.net.flow.DefaultFlowRule;
import org.onosproject.net.flow.FlowRuleEvent;
import org.onosproject.net.flow.FlowRuleListener;
import org.onosproject.net.flow.FlowRuleOperations;
import org.onosproject.net.flow.FlowRuleOperationsContext;
import org.onosproject.net.flow.FlowRuleService;
import org.onosproject.net.flow.TrafficSelector;
import org.onosproject.net.flow.DefaultTrafficSelector;
import org.onosproject.net.flow.TrafficTreatment;
import org.onosproject.net.flow.DefaultTrafficTreatment;
import org.onosproject.net.flow.criteria.Criterion;
import org.onosproject.net.flow.criteria.EthTypeCriterion;
import org.onosproject.net.flow.criteria.IPCriterion;
import org.onosproject.net.flow.criteria.IPProtocolCriterion;
import org.onosproject.net.flow.criteria.IcmpCodeCriterion;
import org.onosproject.net.flow.criteria.IcmpTypeCriterion;
import org.onosproject.net.flow.criteria.Icmpv6CodeCriterion;
import org.onosproject.net.flow.criteria.Icmpv6TypeCriterion;
import org.onosproject.net.flow.criteria.TcpPortCriterion;
import org.onosproject.net.flow.criteria.UdpPortCriterion;
import org.onosproject.net.flowobjective.DefaultForwardingObjective;
import org.onosproject.net.flowobjective.FlowObjectiveService;
import org.onosproject.net.flowobjective.ForwardingObjective;
import org.osgi.service.component.ComponentContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.common.base.Strings;

/*
TODO: Create REST interface to handle ipfix query requests.
 */

/**
 * OpenFlow to IPFIX Manager.
 */
@Component(immediate = true)
@Service
public class IpfixManager implements IpfixService, FlowRuleListener {

    private static final int DEFAULT_TIMEOUT = 10;
    private static final int DEFAULT_PRIORITY = 10;
    private int flowTimeout = DEFAULT_TIMEOUT;
    private int flowPriority = DEFAULT_PRIORITY;

    //These should be identical to the pipeline driver tables
    protected static final int TUNNEL_TABLE = 10;
    protected static final int CLEANSING_TABLE = 20;
    protected static final int BLOCK_TABLE = 100;
    protected static final int IPFIX_TABLE = 200;
    protected static final int FORWARD_TABLE = 202;

    protected final Logger log = LoggerFactory.getLogger(getClass());

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected DeviceService deviceService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected FlowRuleService flowRuleService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected FlowObjectiveService flowObjectiveService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected CoreService coreService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected ComponentConfigService cfgService;

    private ApplicationId appId;

    private static final boolean R_FWD_FLOWS_EXPORT = true;
    @Property(name = "ReactiveForwardingFlowExport", boolValue = R_FWD_FLOWS_EXPORT,
            label = "Reactive Forwarding application flows exported over IPFIX when removed")
    private boolean reactiveForwardingFlowExport = R_FWD_FLOWS_EXPORT;

    /*
      The forwarding app that we should get flow events from.
        - {subtype: ipfix, port: 4739}
        - {subtype: prefix, port: 4740}
        - {subtype: interfix, port: 4741}
     */

    //TODO (l.fawcett1@lancs.ac.uk) Unsure why this is set to flowmonitor
    //Flowmonitor is the generic packet in module
    public static final String R_FWD_APP = "org.onosproject.flowmonitor";
    @Property(name = "ReactiveForwardingApp", value = R_FWD_APP,
            label = "Reactive Forwarding application to register IPFIX events when removed")
    private static String reactiveForwardingApp = R_FWD_APP;

    public static final String IPFIX_COLLECTOR_ADDRESS = "127.0.0.1";
    @Property(name = "ipfixCollectorAddress", value = IPFIX_COLLECTOR_ADDRESS,
            label = "IPFIX Collector IP Address")
    private String ipfixCollectorAddress = IPFIX_COLLECTOR_ADDRESS;
    protected static IpAddress ipfixCollectorIp;

    public static final int IPFIX_COLLECTOR_PORT = 4739;
    @Property(name = "ipfixCollectorPort", intValue = IPFIX_COLLECTOR_PORT,
            label = "IPFIX Collector UDP Port")
    protected static int ipfixCollectorPort = IPFIX_COLLECTOR_PORT;

    public static final String PREFIX_COLLECTOR_ADDRESS = "127.0.0.1";
    @Property(name = "prefixCollectorAddress", value = PREFIX_COLLECTOR_ADDRESS,
            label = "Prefix Collector IP Address")
    private String prefixCollectorAddress = PREFIX_COLLECTOR_ADDRESS;
    protected static IpAddress prefixCollectorIp;

    public static final int PREFIX_COLLECTOR_PORT = 4740;
    @Property(name = "prefixCollectorPort", intValue = PREFIX_COLLECTOR_PORT,
            label = "Prefix Collector UDP Port")
    protected static int prefixCollectorPort = PREFIX_COLLECTOR_PORT;

    public static final String QUERY_COLLECTOR_ADDRESS = "127.0.0.1";
    @Property(name = "queryCollectorAddress", value = QUERY_COLLECTOR_ADDRESS,
            label = "Query Collector IP Address")
    private String queryCollectorAddress = QUERY_COLLECTOR_ADDRESS;
    protected static IpAddress queryCollectorIp;

    public static final int QUERY_COLLECTOR_PORT = 4741;
    @Property(name = "queryCollectorPort", intValue = QUERY_COLLECTOR_PORT,
            label = "Query Collector UDP Port")
    protected static int queryCollectorPort = QUERY_COLLECTOR_PORT;

    private ArrayList<String> garbageIpfix = new ArrayList<>();

    @Activate
    public void activate(ComponentContext context) {
        appId = coreService.registerApplication("org.onosproject.ipfix");
        cfgService.registerProperties(getClass());
        getProperties(context);
        ipfixCollectorIp = IpAddress.valueOf(ipfixCollectorAddress);

        flowRuleService.addListener(this);

        log.info("Started. reactiveForwardingFlowExport={}" +
                        " IPFIX collector: event ip={}, event port={}",
                reactiveForwardingFlowExport, ipfixCollectorAddress, ipfixCollectorPort);
        //cfgService.setProperty("org.onosproject.fwd.ReactiveForwarding","matchIpv4Address","true"); 
        //cfgService.setProperty("org.onosproject.fwd.ReactiveForwarding","matchTcpUdpPorts","true"); 
        //cfgService.setProperty("org.onosproject.fwd.ReactiveForwarding","matchIcmpFields","true"); 
        cfgService.setProperty("org.onosproject.provider.of.device.impl.OpenFlowDeviceProvider","portStatsPollFrequency","1"); 
   }

    @Deactivate
    public void deactivate(ComponentContext context) {
        cfgService.unregisterProperties(getClass(), false);
        flowRuleService.removeListener(this);

        log.info("Stopped");
    }

    @Modified
    public void modified(ComponentContext context) {
        getProperties(context);
        flowRuleService.addListener(this);

        log.info("Modified. reactiveForwardingFlowExport={}, IPFIX collector: ip={} port={}",
                reactiveForwardingFlowExport, ipfixCollectorAddress, ipfixCollectorPort);
    }

    /**
     * Get the application that the IPFIX service should monitor flow rule additions/deletions/queries.
     * @return Application Name.
     */
    public static String getRfwdAppName() {
        return reactiveForwardingApp;
    }

    /**
     *
     * @return IPAddress for IPFIX records.
     */
    public  IpAddress getIpfixCollectorAddress() {
        return ipfixCollectorIp;
    }

    /**
     *
     * @return Collector port for IPFIX.
     */
    public int getIpfixCollectorPort() {
        return ipfixCollectorPort;
    }

    /**
     *
     * @return IPAddress for PREFIX records.
     */
    public IpAddress getPrefixCollectorAddress() {
        return prefixCollectorIp;
    }

    /**
     *
     * @return Collector port for initial PREFIX.
     */
    public int getPrefixCollectorPort() {
        return prefixCollectorPort;
    }

    /**
     *
     * @return  IPAddress for IPFIX queries.
     */
    public static IpAddress getQueryCollectorAddress() {
        return queryCollectorIp;
    }

    /**
     *
     * @return Collector port for IPFIX queries.
     */
    public static int getQueryCollectorPort() {
        return queryCollectorPort;
    }

    /**
     * Get the properties of the IPFIX Manager, by settings interface.
     * @param context passed automatically
     */
    public void getProperties(ComponentContext context) {
        Dictionary<?, ?> properties = context.getProperties();

        // parse CollectorPort Property
        String s = get(properties, "ipfixCollectorPort");
        try {
            ipfixCollectorPort = isNullOrEmpty(s) ? ipfixCollectorPort : Integer.parseInt(s.trim());
        } catch (NumberFormatException | ClassCastException e) {
            log.info("IPFIX CollectorPort Format Exception");
        }

        s = get(properties, "prefixCollectorPort");
        try {
            prefixCollectorPort = isNullOrEmpty(s) ? prefixCollectorPort : Integer.parseInt(s.trim());
        } catch (NumberFormatException | ClassCastException e) {
            log.info("PREFIX CollectorPort Format Exception");
        }

        s = get(properties, "queryCollectorPort");
        try {
            queryCollectorPort = isNullOrEmpty(s) ? queryCollectorPort : Integer.parseInt(s.trim());
        } catch (NumberFormatException | ClassCastException e) {
            log.info("Query CollectorPort Format Exception");
        }

        // parse CollectorAddress Property
        s = get(properties, "ipfixCollectorAddress");
        ipfixCollectorAddress = isNullOrEmpty(s) ? ipfixCollectorAddress : s;
        ipfixCollectorIp = IpAddress.valueOf(ipfixCollectorAddress);

        // parse CollectorAddress Property
        s = get(properties, "prefixCollectorAddress");
        prefixCollectorAddress = isNullOrEmpty(s) ? prefixCollectorAddress : s;
        prefixCollectorIp = IpAddress.valueOf(prefixCollectorAddress);

        // parse CollectorAddress Property
        s = get(properties, "queryCollectorAddress");
        queryCollectorAddress = isNullOrEmpty(s) ? queryCollectorAddress : s;
        queryCollectorIp = IpAddress.valueOf(queryCollectorAddress);

        // parse reactiveForwardingFlowExport Property
        s = get(properties, "ReactiveForwardingFlowExport");
        reactiveForwardingFlowExport = Strings.isNullOrEmpty(s) ? R_FWD_FLOWS_EXPORT : Boolean.valueOf(s);

    }

    private TrafficSelector createIpfixSelector(String saddr, String sport, String daddr, String dport, String protocol) {
        TrafficSelector.Builder selectorBuilder = DefaultTrafficSelector.builder();

        // TODO (l.fawcett1@lancaster.ac.uk) Only IPv4 for now. Could detect address format??
        Ip4Address matchIp4SrcPrefix = Ip4Address.valueOf(saddr);
        Ip4Address matchIp4DstPrefix = Ip4Address.valueOf(daddr);
        selectorBuilder.matchEthType(Ethernet.TYPE_IPV4)
                .matchIPSrc(matchIp4SrcPrefix.toIpPrefix())
                .matchIPDst(matchIp4DstPrefix.toIpPrefix());

        if (protocol.equals("tcp")) {
            selectorBuilder.matchIPProtocol(IPv4.PROTOCOL_TCP)
                    .matchTcpSrc(TpPort.tpPort(Integer.valueOf(sport)))
                    .matchTcpDst(TpPort.tpPort(Integer.valueOf(dport)));
        } else if (protocol.equals("udp")) {
            selectorBuilder.matchIPProtocol(IPv4.PROTOCOL_UDP)
                    .matchUdpSrc(TpPort.tpPort(Short.valueOf(sport)))
                    .matchUdpDst(TpPort.tpPort(Short.valueOf(dport)));
        } else if (protocol.equals("icmp")) {
            // TODO (l.fawcett1@lancaster.ac.uk) Use ports for type and code. May switch to individual ICMP method.
            selectorBuilder.matchIPProtocol(IPv4.PROTOCOL_ICMP)
                    .matchIcmpType(Byte.valueOf(sport))
                    .matchIcmpCode(Byte.valueOf(dport));
        }


        return selectorBuilder.build();
    }

    /**
     *
     * @param saddr IP source address as a string. e.g. "192.168.1.1".
     * @param sport Transport Source Port as String. e.g. 47393.
     * @param daddr IP source address as a string. e.g. "192.168.1.101".
     * @param dport Transport Source Port as String. e.g. 5001.
     * @param protocol Transport Protocol as String. e.g. {TCP, UDP, ICMP, ICMP6}.
     */
    @Override
    public void addIpfix(String saddr, String sport, String daddr, String dport, String protocol) {

        log.info("Adding IPFIX rule to all devices.");

        TrafficSelector selector = createIpfixSelector(saddr, sport, daddr, dport, protocol);
        for (Device device : deviceService.getDevices()) {
            installIpfixRule(selector, device.id());
        }
    }
	
	 /**
     *
     * @param saddr IP source address as a string. e.g. "192.168.1.1".
     * @param sport Transport Source Port as String. e.g. 47393.
     * @param daddr IP source address as a string. e.g. "192.168.1.101".
     * @param dport Transport Source Port as String. e.g. 5001.
     * @param protocol Transport Protocol as String. e.g. {TCP, UDP, ICMP, ICMP6}.
	 * @param deviceId Device ID to install IPFIX rule on e.g 00:00:00:00:00:01
     */
    @Override
    public void addSingleIpfix(String saddr, String sport, String daddr, String dport, String protocol, String deviceId) {

        log.info("Adding IPFIX rule to single device.");

        TrafficSelector selector = createIpfixSelector(saddr, sport, daddr, dport, protocol);
        installIpfixRule(selector, DeviceId.deviceId(deviceId));
    }

    private void installIpfixRule(TrafficSelector selector, DeviceId deviceId) {
        TrafficTreatment treatment = DefaultTrafficTreatment.builder().transition(FORWARD_TABLE).build();
        
        FlowRule rule = DefaultFlowRule.builder()
                .fromApp(appId).withPriority(flowPriority)
                .forDevice(deviceId)
                .withSelector(selector)
                .withTreatment(treatment)
                .forTable(IPFIX_TABLE)
                .makeTemporary(flowTimeout)
                .build();

        applyRules(true, rule);
    }

    /**
     * Apply the flow rules, adding to the flow rule service.
     * @param install true if to be installed, false otherwise.
     * @param rule The FlowRule to be installed.
     */
    private void applyRules(boolean install, FlowRule rule) {
        FlowRuleOperations.Builder ops = FlowRuleOperations.builder();

        ops = install ? ops.add(rule) : ops.remove(rule);
        flowRuleService.apply(ops.build(new FlowRuleOperationsContext() {
            @Override
            public void onSuccess(FlowRuleOperations ops) {
                log.info("ONOSFW provisioned table" + rule.tableId());
            }

            @Override
            public void onError(FlowRuleOperations ops) {
                log.info("ONOSFW failed to provision " + rule.tableId() + " table");
            }
        }));
    }

    /**
     * Fired on a flow rule event, e.g. addition or deletion.
     * This is only fired after a flow moves to the added state, leading to a small delay.
     * @param event The specific flow rule event.
     */
    @Override
    public void event(FlowRuleEvent event) {
        FlowRule rule = event.subject();

        switch (event.type()) {
            case RULE_ADDED:
                break;
            case RULE_REMOVED:

                // Only interested in monitoring rules
                if (rule.appId() == appId.id()) {

                    /*// Send final IPFIX - Need to check that this isn't from from clean up
                    if (!garbageIpfix.contains(rule.id().toString())) {*/ //Legacy code from cleanIpfixRules().
                        log.info("IPFIX Rule Removed timeout");
                        IpfixEvent.createIpfixFlowRecord(deviceService, (FlowEntry) rule,
                                                         getIpfixCollectorAddress(),
                                                         getIpfixCollectorPort());
                    /*} else {
                        log.info("IPFIX Rule Removed garbage collection");
                        garbageIpfix.remove(rule.id().toString());
                    }*/ //Legacy code from cleanIpfixRules().
                }
            default:
                break;
        }
         
		//Seems to be legacy code to remove duplication.
        //cleanIpfixRules();
    }

    /**
     *
     */
    private void cleanIpfixRules() {

        // Organise FlowEntires into IPFIX flows
        HashMap<String, ArrayList<FlowEntry>> monitoringRules = new HashMap<>();
        for (Device device : deviceService.getDevices()) {
            for (FlowEntry entry : flowRuleService.getFlowEntries(device.id())) {
                // Only monitoring flows
                if (entry.appId() == appId.id()) {
                    String flowKey = entry.selector().criteria().toString();
                    if (!monitoringRules.containsKey(flowKey)) {
                        monitoringRules.put(flowKey, new ArrayList<>());
                    }

                    monitoringRules.get(flowKey).add(entry);
                }
            }
        }

        for (ArrayList<FlowEntry> entryList : monitoringRules.values()) {

            log.info("Cleaning up monitoring flows for: " + entryList.get(0).selector().criteria().toString());

            // Find most active rule
            long maxActivity = 0;
            for (FlowEntry entry : entryList) {
                if (entry.bytes() > maxActivity) {
                    maxActivity = entry.bytes();
                }
            }

            if (maxActivity == 0 || entryList.size() <= 1) {
                log.info("Nothing to clean up");
                continue;
            }

            //Remove all entries except one with maxActivity
            boolean selectedRuleFound = false;
            for (FlowEntry entry : entryList) {

                if (entry.bytes() == maxActivity && !selectedRuleFound) {
                    selectedRuleFound = true;
                    continue;
                }

                log.info("Removing inactive mon monitoring rule on: " + entry.deviceId().toString());
                garbageIpfix.add(entry.id().toString());
                flowRuleService.removeFlowRules(entry);
            }
        }

    }

    /**
     * Trigger IPFIX records to be sent to the collector for all flow entries installed in each switch.
     */
    @Override
    public void getFlowEntries() {
        log.info("getFlowEntries()");

        if (deviceService == null) {
            log.info("DeviceService is null");
            return;
        }

        if (flowRuleService == null) {
            log.info("flowRuleService is null");
            return;
        }

        final Iterable<Device> devices = deviceService.getDevices();

        if (devices == null) {
            log.info("devices is null");
            return;
        }

        // Iterate through all switches
        for (final Device device : devices) {
            log.info("Device: " + device.id());

            // Get the list of flow entries
            final Iterable<FlowEntry> flowEntries = flowRuleService.getFlowEntries(device.id());
            if (flowEntries != null) {
                log.info("Creating IPFIX records for /query");
                // Iterate through all flow entries.
                for (final FlowEntry entry : flowEntries) {
                    if (entry.appId() == coreService.getAppId(IpfixManager.getRfwdAppName()).id() ||
                            entry.appId() == appId.id()) {
                        IpfixEvent.createIpfixFlowRecord(deviceService,
                                entry, getQueryCollectorAddress(), getQueryCollectorPort());
                    }
                }
            }
        }
    }


    /**
     * TODO: Make this generic. Allow requests from specific switches, for specific flows as well as catch all.
     *
     * Trigger an IPFIX query for a specific flow entry, matching on 5-tuple + protocol.
     *
     * @param saddr IP source address as a string. e.g. "192.168.1.1".
     * @param sport Transport Source Port as String. e.g. 47393.
     * @param daddr IP source address as a string. e.g. "192.168.1.101".
     * @param dport Transport Source Port as String. e.g. 5001.
     * @param protocol Transport Protocol as String. e.g. {TCP, UDP, ICMP, ICMP6}.
     */
    @Override
    public void getFlowEntry(String saddr, String sport, String daddr, String dport, String protocol) {

        log.info(String.format("getFlowEntry(%s, %s, %s, %s, %s)", saddr, sport, daddr, dport, protocol));

        if (deviceService == null) {
            log.info("DeviceService is null");
            return;
        }

        if (flowRuleService == null) {
            log.info("flowRuleService is null");
            return;
        }

        // Get the set of switches
        final Iterable<Device> devices = deviceService.getDevices();

        if (devices == null) {
            log.info("devices is null");
            return;
        }

        // Iterate over all switches the controller is aware of.
        for (final Device device : devices) {
            log.info("Device: " + device.id());
            final Iterable<FlowEntry> flowEntries = flowRuleService.getFlowEntries(device.id());
            if (flowEntries != null) {
                log.info("Flow Entries not null: ");

                // Iterate over all the flow entries for each switch.
                for (final FlowEntry entry : flowEntries) {

                    // Only look at flows from the defined monitoring application.
                    if (entry.appId() == coreService.getAppId(IpfixManager.getRfwdAppName()).id()) {

                        log.debug("Flow Entry");

                        if (entry.selector() == null) {
                            log.debug("Entry Selector is null");
                        }

                        if (entry.selector().criteria() == null) {
                            log.debug("Entry Selector get Criterion is null");
                        }

                        if (entry.selector().getCriterion(Criterion.Type.ETH_TYPE) == null) {
                            log.debug("Entry Selector get Criterion is null");
                        }

                        // We are only interested in Ethernet at the moment.
                        EthTypeCriterion ethTypeCrit = (EthTypeCriterion) entry.selector()
                                .getCriterion(Criterion.Type.ETH_TYPE);

                        Short ethType = (ethTypeCrit == null) ? 0x0000 : ethTypeCrit.ethType().toShort();
                        // Raw match for IP address type
                        if (ethType == 0x0800 && saddr.contains(".")) {
                            // Get the IP4 source
                            IPCriterion srcIpCrit = (IPCriterion) entry.selector()
                                    .getCriterion(Criterion.Type.IPV4_SRC);
                            // Get the IP6 source
                            IPCriterion dstIpCrit = (IPCriterion) entry.selector()
                                    .getCriterion(Criterion.Type.IPV4_DST);

                            // Check IP4 address matches the requested params
                            if ((!srcIpCrit.ip().address().toString().equals(saddr) && !saddr.equals("*")) ||
                                    !dstIpCrit.ip().address().toString().equals(daddr) && !daddr.equals("*")) {
                                log.info("IPv4 Addresses do not match");
                                continue;
                            }
                        } else if (ethType == 0x86DD && saddr.contains(":")) {
                            // Get IP6 source address
                            IPCriterion srcIp6Crit = (IPCriterion) entry.selector()
                                    .getCriterion(Criterion.Type.IPV6_SRC);

                            // Get IP4 source address
                            IPCriterion dstIp6Crit = (IPCriterion) entry.selector()
                                    .getCriterion(Criterion.Type.IPV6_DST);

                            // Check IP6 address matches the requested params
                            if ((!srcIp6Crit.ip().address().toString().equals(saddr) && !saddr.equals("*")) ||
                                    !dstIp6Crit.ip().address().toString().equals(daddr) && !daddr.equals("*")) {
                                log.info("IPv6 Addresses do not match");
                                continue;
                            }
                        }

                        IPProtocolCriterion protocolCrit = (IPProtocolCriterion) entry.selector()
                                .getCriterion(Criterion.Type.IP_PROTO);

                        byte ipProtocol = (protocolCrit == null) ? (byte) 0xff : (byte) protocolCrit.protocol();
                        int srcPort = 0;
                        int dstPort = 0;
                        if (ipProtocol == IPv4.PROTOCOL_TCP && protocol.equalsIgnoreCase("tcp")) {
                            // Get the TCP source and dest ports
                            TcpPortCriterion tcpCrit;
                            tcpCrit = (TcpPortCriterion) entry.selector().getCriterion(Criterion.Type.TCP_SRC);
                            srcPort = (tcpCrit == null) ? 0 : tcpCrit.tcpPort().toInt();
                            tcpCrit = (TcpPortCriterion) entry.selector().getCriterion(Criterion.Type.TCP_DST);
                            dstPort = (tcpCrit == null) ? 0 : tcpCrit.tcpPort().toInt();
                        } else if (ipProtocol == IPv4.PROTOCOL_UDP && protocol.equalsIgnoreCase("udp")) {
                            // Get the UDP source and dest ports
                            UdpPortCriterion udpCrit;
                            udpCrit = (UdpPortCriterion) entry.selector().getCriterion(Criterion.Type.UDP_SRC);
                            srcPort = (udpCrit == null) ? 0 : udpCrit.udpPort().toInt();
                            udpCrit = (UdpPortCriterion) entry.selector().getCriterion(Criterion.Type.UDP_DST);
                            dstPort = (udpCrit == null) ? 0 : udpCrit.udpPort().toInt();
                        } else if (ipProtocol == IPv4.PROTOCOL_ICMP && protocol.equalsIgnoreCase("icmp")) {
                            // Get the ICMP type and code, using the port fields.
                            IcmpTypeCriterion icmpTypeCrit = (IcmpTypeCriterion) entry.selector()
                                    .getCriterion(Criterion.Type.ICMPV4_TYPE);
                            Short icmpType = (icmpTypeCrit == null) ? 0 : icmpTypeCrit.icmpType();
                            IcmpCodeCriterion icmpCodeCrit = (IcmpCodeCriterion) entry.selector()
                                    .getCriterion(Criterion.Type.ICMPV4_CODE);
                            Short icmpCode = (icmpCodeCrit == null) ? 0 : icmpCodeCrit.icmpCode();
                            srcPort = icmpType;
                            dstPort = icmpCode;
                        } else if (ipProtocol == IPv6.PROTOCOL_ICMP6 && protocol.equalsIgnoreCase("icmp6")) {
                            // Get the ICMP6 type and code, using the port fields.
                            Icmpv6TypeCriterion icmpv6TypeCrit =
                                    (Icmpv6TypeCriterion) entry.selector().getCriterion(Criterion.Type.ICMPV6_TYPE);
                            Short icmpType = (icmpv6TypeCrit == null) ? 0 : icmpv6TypeCrit.icmpv6Type();
                            Icmpv6CodeCriterion icmpv6CodeCrit =
                                    (Icmpv6CodeCriterion) entry.selector().getCriterion(Criterion.Type.ICMPV6_CODE);
                            Short icmpCode = (icmpv6CodeCrit == null) ? 0 : icmpv6CodeCrit.icmpv6Code();
                            srcPort = icmpType;
                            dstPort = icmpCode;
                        }

                        // Check the ports match the request
                        if ((!Integer.toString(srcPort).equals(sport) && !sport.equals("*"))
                                || (!Integer.toString(dstPort).equals(dport) && !dport.equals("*"))) {
                            log.info("Ports do not match");
                            continue;
                        }

                        // Trigger the IPFIX to send a record to the collector.
                        if (entry.appId() == coreService.getAppId(IpfixManager.getRfwdAppName()).id() ||
                                entry.appId() == appId.id()) {
                            IpfixEvent.createIpfixFlowRecord(deviceService,
                                    entry, getQueryCollectorAddress(), getQueryCollectorPort());
                        }
                    }
                }
            } else {
                log.info("Flow Entries is null");
            }
        }
    }



    /**
     *
     * @param saddr
     * @param sport
     * @param daddr
     * @param dport
     * @param protocol
     * @return
     */
    private ArrayList<DeviceId> getSuitableDevices(String saddr, String sport,
                                                 String daddr, String dport,
                                                 String protocol) {

        log.info(String.format("getSuitableDevices(%s, %s, %s, %s, %s)", saddr, sport, daddr, dport, protocol));

        ArrayList<DeviceId> suitableDevices = new ArrayList<>();

        // Get the set of switches
        final Iterable<Device> devices = deviceService.getDevices();

        if (devices == null) {
            log.warn("devices is null");
            return suitableDevices;
        }

        // Iterate over all switches the controller is aware of.
        for (final Device device : devices) {
            log.info("Device: " + device.id());
            final Iterable<FlowEntry> flowEntries = flowRuleService.getFlowEntries(device.id());
            if (flowEntries != null) {
                log.info("Flow Entries not null: ");

                // Iterate over all the flow entries for each switch.
                for (final FlowEntry entry : flowEntries) {

                    if (entry.selector() == null) {
                        log.debug("Entry Selector is null");
                        continue;
                    }

                    if (entry.selector().criteria() == null) {
                        log.debug("Entry Selector get Criterion is null");
                        continue;
                    }

                    if (entry.selector().getCriterion(Criterion.Type.ETH_TYPE) == null) {
                        log.debug("Entry Selector get Criterion is null");
                        continue;
                    }

                    // We are only interested in Ethernet at the moment.
                    EthTypeCriterion ethTypeCrit = (EthTypeCriterion) entry.selector()
                            .getCriterion(Criterion.Type.ETH_TYPE);

                    Short ethType = (ethTypeCrit == null) ? 0x0000 : ethTypeCrit.ethType().toShort();
                    // Raw match for IP address type
                    if (ethType == 0x0800 && saddr.contains(".")) {
                        // Get the IP4 source
                        IPCriterion srcIpCrit = (IPCriterion) entry.selector()
                                .getCriterion(Criterion.Type.IPV4_SRC);
                        // Get the IP6 source
                        IPCriterion dstIpCrit = (IPCriterion) entry.selector()
                                .getCriterion(Criterion.Type.IPV4_DST);

                        // Check IP4 address matches the requested params
                        if ((!srcIpCrit.ip().address().toString().equals(saddr) && !saddr.equals("*")) ||
                                !dstIpCrit.ip().address().toString().equals(daddr) && !daddr.equals("*")) {
                            log.info("IPv4 Addresses do not match");
                            continue;
                        }
                    } else if (ethType == 0x86DD && saddr.contains(":")) {
                        // Get IP6 source address
                        IPCriterion srcIp6Crit = (IPCriterion) entry.selector()
                                .getCriterion(Criterion.Type.IPV6_SRC);

                        // Get IP4 source address
                        IPCriterion dstIp6Crit = (IPCriterion) entry.selector()
                                .getCriterion(Criterion.Type.IPV6_DST);

                        // Check IP6 address matches the requested params
                        if ((!srcIp6Crit.ip().address().toString().equals(saddr) && !saddr.equals("*")) ||
                                !dstIp6Crit.ip().address().toString().equals(daddr) && !daddr.equals("*")) {
                            log.info("IPv6 Addresses do not match");
                            continue;
                        }
                    }

                    IPProtocolCriterion protocolCrit = (IPProtocolCriterion) entry.selector()
                            .getCriterion(Criterion.Type.IP_PROTO);

                    byte ipProtocol = (protocolCrit == null) ? (byte) 0xff : (byte) protocolCrit.protocol();
                    int srcPort = 0;
                    int dstPort = 0;
                    if (ipProtocol == IPv4.PROTOCOL_TCP && protocol.equalsIgnoreCase("tcp")) {
                        // Get the TCP source and dest ports
                        TcpPortCriterion tcpCrit;
                        tcpCrit = (TcpPortCriterion) entry.selector().getCriterion(Criterion.Type.TCP_SRC);
                        srcPort = (tcpCrit == null) ? 0 : tcpCrit.tcpPort().toInt();
                        tcpCrit = (TcpPortCriterion) entry.selector().getCriterion(Criterion.Type.TCP_DST);
                        dstPort = (tcpCrit == null) ? 0 : tcpCrit.tcpPort().toInt();
                    } else if (ipProtocol == IPv4.PROTOCOL_UDP && protocol.equalsIgnoreCase("udp")) {
                        // Get the UDP source and dest ports
                        UdpPortCriterion udpCrit;
                        udpCrit = (UdpPortCriterion) entry.selector().getCriterion(Criterion.Type.UDP_SRC);
                        srcPort = (udpCrit == null) ? 0 : udpCrit.udpPort().toInt();
                        udpCrit = (UdpPortCriterion) entry.selector().getCriterion(Criterion.Type.UDP_DST);
                        dstPort = (udpCrit == null) ? 0 : udpCrit.udpPort().toInt();
                    } else if (ipProtocol == IPv4.PROTOCOL_ICMP && protocol.equalsIgnoreCase("icmp")) {
                        // Get the ICMP type and code, using the port fields.
                        IcmpTypeCriterion icmpTypeCrit = (IcmpTypeCriterion) entry.selector()
                                .getCriterion(Criterion.Type.ICMPV4_TYPE);
                        Short icmpType = (icmpTypeCrit == null) ? 0 : icmpTypeCrit.icmpType();
                        IcmpCodeCriterion icmpCodeCrit = (IcmpCodeCriterion) entry.selector()
                                .getCriterion(Criterion.Type.ICMPV4_CODE);
                        Short icmpCode = (icmpCodeCrit == null) ? 0 : icmpCodeCrit.icmpCode();
                        srcPort = icmpType;
                        dstPort = icmpCode;
                    } else if (ipProtocol == IPv6.PROTOCOL_ICMP6 && protocol.equalsIgnoreCase("icmp6")) {
                        // Get the ICMP6 type and code, using the port fields.
                        Icmpv6TypeCriterion icmpv6TypeCrit =
                                (Icmpv6TypeCriterion) entry.selector().getCriterion(Criterion.Type.ICMPV6_TYPE);
                        Short icmpType = (icmpv6TypeCrit == null) ? 0 : icmpv6TypeCrit.icmpv6Type();
                        Icmpv6CodeCriterion icmpv6CodeCrit =
                                (Icmpv6CodeCriterion) entry.selector().getCriterion(Criterion.Type.ICMPV6_CODE);
                        Short icmpCode = (icmpv6CodeCrit == null) ? 0 : icmpv6CodeCrit.icmpv6Code();
                        srcPort = icmpType;
                        dstPort = icmpCode;
                    }

                    // Check the ports match the request
                    if ((!Integer.toString(srcPort).equals(sport) && !sport.equals("*"))
                            || (!Integer.toString(dstPort).equals(dport) && !dport.equals("*"))) {
                        log.info("Ports do not match: " + srcPort + " " + dstPort + " -> " + sport + " " + dport);
                        continue;
                    }

                    //Suitable Device
                    suitableDevices.add(device.id());
                }
            } else {
                log.info("Flow Entries is null");
            }
        }

        return suitableDevices;
    }
}
