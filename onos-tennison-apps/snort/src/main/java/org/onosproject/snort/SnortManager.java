/*
 * Copyright 2014 Open Networking Laboratory
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
package org.onosproject.snort;

import org.apache.felix.scr.annotations.Component;
import org.apache.felix.scr.annotations.Reference;
import org.apache.felix.scr.annotations.ReferenceCardinality;
import org.apache.felix.scr.annotations.Activate;
import org.apache.felix.scr.annotations.Deactivate;
import org.apache.felix.scr.annotations.Service;

import org.onlab.packet.IPv6;
import org.onlab.packet.IpAddress;
import org.onosproject.net.ConnectPoint;
import org.onosproject.net.Device;
import org.onosproject.net.DeviceId;
import org.onlab.packet.Ethernet;
import org.onlab.packet.TpPort;
import org.onlab.packet.IPv4;
import org.onlab.packet.Ip4Address;
import org.onlab.packet.Ip4Prefix;
import org.onlab.packet.VlanId;
import org.onosproject.core.ApplicationId;
import org.onosproject.core.CoreService;
import org.onosproject.core.GroupId;

import org.onosproject.net.Host;
import org.onosproject.net.Port;
import org.onosproject.net.PortNumber;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.flow.DefaultFlowRule;
import org.onosproject.net.flow.FlowEntry;
import org.onosproject.net.flow.FlowId;
import org.onosproject.net.flow.FlowRule;
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
import org.onosproject.net.host.HostEvent;
import org.onosproject.net.host.HostListener;
import org.onosproject.net.host.HostService;
import org.onosproject.net.link.LinkService;
import org.onosproject.net.group.GroupService;
import org.osgi.service.component.ComponentContext;
import org.slf4j.Logger;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.ArrayDeque;

import static org.slf4j.LoggerFactory.getLogger;

/**
 * This class manages registering snort instances, redirecting/mirroring rules.
 * Maintained by Lyndon (l.fawcett1@lancaster.ac.uk) 12/05/17.
 */
@Component(immediate = true)
@Service
public class SnortManager implements SnortService, HostListener {

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

    private static final short SNORT_VLAN_ID = 500;
    private static final int SNORT_GROUP_ID = 500;

    public static final int DEFAULT_SNORT_OUT_PORT = 1;

    private final Logger log = getLogger(getClass());

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected FlowRuleService flowRuleService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected CoreService coreService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected HostService hostService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected DeviceService deviceService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected LinkService linkService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected GroupService groupService;

    private ApplicationId appId;

    //Added snort instances that have been discovered
    private HashMap<String /*DeviceID*/, HashMap<String /*IP*/, Integer /*Port*/>> snortPorts = new HashMap<>();
    private HashMap<FlowId, FlowRule> snortDuplicationRules = new HashMap<>();

    //All snort instances including thoes yet to be discovered
    private ArrayList<String> pendingSnort;

    private HashMap<String /*DeviceId*/, ArrayList<TrafficSelector>> pendingMirror;
    private HashMap<String /*DeviceId*/, ArrayList<TrafficSelector>> pendingRedirect;

    private SnortTunnel snortTunnel;

    @Activate
    public void activate(ComponentContext context) {
        appId = coreService.registerApplication("org.onosproject.snort");
        log.info("Started", appId.id());

        pendingSnort = new ArrayList<>();
        hostService.addListener(this);
        snortTunnel = new SnortTunnel(appId, deviceService, linkService, groupService);

        pendingMirror = new HashMap<>();
        pendingRedirect = new HashMap<>();


        //Tunneling. Add Device listener to get links and how switches are configured.



    }

    @Deactivate
    public void deactivate() {
        log.info("Stopped");
    }

    /**
     * This adds knowledge of a snort instance to ONOS.
     * Required so that onos knows where to redirect flows to.
     * @param newSnortIp
     * @return
     */
    public boolean addSnortInstance(String newSnortIp) {

        if (!pendingSnort.contains(newSnortIp)) {
            pendingSnort.add(newSnortIp);
        }

        for (final Device device : deviceService.getDevices()) {
            String deviceId = device.id().toString();
            for (Port port : deviceService.getPorts(device.id())) {
                ConnectPoint cp = new ConnectPoint(device.id(), port.number());
                for (Host host : hostService.getConnectedHosts(cp)) {
                    for (IpAddress ip : host.ipAddresses()) {
                        if (ip.toString().equals(newSnortIp)) {
                            log.info("Found connection point for snort instance " + newSnortIp +
                                             ". DeviceID: " + deviceId +
                                             " Port: " + port.number().toLong());
                            if (!snortPorts.containsKey(deviceId)) {
                                snortPorts.put(deviceId, new HashMap<>());
                            }
                            snortPorts.get(deviceId).put(newSnortIp, (int) port.number().toLong());
                            snortDuplicationBlock(true, device.id(), (int) port.number().toLong());

                            snortTunnel.addSnort(deviceId, port);

                            /*
                            * Install rules that have been waiting on a snort instance
                             */
                            if (pendingMirror.containsKey(deviceId)) {
                                log.info("Adding pending mirror rules for Device: " + deviceId);
                                for (TrafficSelector selector : pendingMirror.get(deviceId)) {
                                    applyRules(true, createMirrorRule(deviceId, selector, flowTimeout));
                                }
                                pendingMirror.remove(deviceId);
                            }

                            if (pendingRedirect.containsKey(deviceId)) {
                                log.info("Adding pending redirect rules for Device: " + deviceId);
                                for (TrafficSelector selector : pendingRedirect.get(deviceId)) {
                                    applyRules(true, createRedirectRule(deviceId, selector, flowTimeout));
                                }
                                pendingRedirect.remove(deviceId);
                            }
                        }
                    }
                }
            }
        }

        return true;
    }

    /**
     * Event hit upon a host entry.
     * This is used to detect snort instances in the network.
     * @param hostEvent
     */
    @Override
    public void event(HostEvent hostEvent) {

        /*
        * If a host has just been discovered on the network. Check if it matches
        * any pending snort instances.
         */

        if (hostEvent.type().equals(HostEvent.Type.HOST_ADDED)) {
            for (IpAddress ip : hostEvent.subject().ipAddresses()) {
                if (pendingSnort.contains(ip.toString())) {
                    log.info("Adding snort instance from HOST_ADDED event: " + hostEvent.toString());
                    addSnortInstance(ip.toString());
                }
            }
        }
    }


    /**
     * Removes single snort instance from onos and removes its block rule.
     * @param ip
     * @return
     */
    public boolean removeSnortInstance(String ip) {

        for (String deviceId : snortPorts.keySet()) {
            if (snortPorts.get(deviceId).containsKey(ip)) {
                snortDuplicationBlock(false,  DeviceId.deviceId(deviceId), snortPorts.get(deviceId).get(ip));
                snortPorts.get(deviceId).remove(ip);
                snortTunnel.removeSnort(deviceId);
            }
        }
        pendingSnort.remove(ip);

        return true;
    }

    /**
     * Removes snort instances from onos and also removes block rules.
     * @return
     */
    public boolean clearSnortInstances() {

        for (String deviceId : snortPorts.keySet()) {
            for (String snortIp : snortPorts.get(deviceId).keySet()) {
                snortDuplicationBlock(false,  DeviceId.deviceId(deviceId), snortPorts.get(deviceId).get(snortIp));
            }
        }

        snortPorts.clear();
        pendingSnort.clear();
        snortTunnel.clearSnort();

        return true;
    }

    /**
     * This will drop any messages returned from Snort to stop duplication. Alternatively try snort inline mode,
     change alert rules to drop rules in thresholds.yaml and use the option --treat-drop-as-alert in pigrelay
     when starting the snort daemon. This solution is probably easier despite having to get each switch to
     drop the returned packets.
     * @param install
     * @param deviceId
     * @param snortPort
     */
    public void snortDuplicationBlock(boolean install, DeviceId deviceId, int snortPort) {

        TrafficSelector selector = DefaultTrafficSelector.builder()
                .matchInPort(PortNumber.portNumber(snortPort)).build();

        FlowRule f = DefaultFlowRule.builder()
                .fromApp(appId).withPriority(flowPriority)
                .forDevice(deviceId)
                .withSelector(selector)
                .withTreatment(DefaultTrafficTreatment.builder().drop().build())
                .forTable(BLOCK_TABLE)
                .makePermanent()
                .build();

        if (install) {
            snortDuplicationRules.put(f.id(), f);
        } else {
            snortDuplicationRules.remove(f.id());
        }

        applyRules(install, f);
    }

    /**
     *
     * @return
     */
    public HashMap<String, HashMap<String, Integer>> getSnortInstances() {
        return snortPorts;
    }

    /**
     * Add a redirect rule to a specific switch, matching the 5-tuple with a specific timeout.
     * Fields also accept '*' wildcard.
     *
     * @param src Source IP Address as a string. e.g. "192.168.1.1".
     * @param dst Destination IP Address as a string. e.g. "192.168.1.1".
     * @param sport Source port as a string. e.g. 5001.
     * @param dport Destination port as a string. e.g. 5001.
     * @param protocol Protocol as a string. e.g. {TCP, UDP, ICMP}.
     * @param timeout Timeout for the rule, less than 0 is unlimited.
     * @return True if successful. TODO: Error check.
     */
    public boolean addRedirectRule(String src, String dst, String sport,
                                String dport, String protocol, int timeout) {

        ArrayList<String> suitableDevices;

        // Select all suitable switches that have a snort instance connected
        suitableDevices = getSuitableSnortDevices(src, sport, dst, dport, protocol);


        if (suitableDevices.isEmpty()) {
            // Select all suitable switches
            suitableDevices = getSuitableDevices(src, sport, dst, dport, protocol);

            if (suitableDevices.isEmpty()) {
                log.info("Adding mirror rule to all switches");

                // Select all switches.
                for (final Device device : deviceService.getDevices()) {
                    suitableDevices.add(device.id().toString());
                }
            } else {
                log.info("Adding mirror rule to switches with matching flow");
            }
        } else {
            log.info("Adding mirror rule to switches with matching flow and a connected snort instance");
        }

        // Add mirror rule (or add to pending) to selected switches
        for (final String deviceid : suitableDevices) {
            TrafficSelector selector = createSelector(src, dst, sport, dport, protocol);
            if (snortPorts.containsKey(deviceid)) {
                FlowRule f = createRedirectRule(deviceid, selector, timeout);
                applyRules(true, f);
            } else {
                log.warn("No connected snort instance for " + deviceid +
                                 ". Using default and adding redirect rule to pending list.");
                if (!pendingRedirect.containsKey(deviceid)) {
                    pendingRedirect.put(deviceid, new ArrayList<>());
                }
                pendingRedirect.get(deviceid).add(selector);
                
                FlowRule f = createRedirectRule(deviceid, selector, timeout);
                applyRules(true, f);
            }
        }

        return true;
    }

    /**
     * Delete a redirect rule to a specific switch, matching the 5-tuple with a specific timeout.
     * Fields also accept '*' wildcard.
     *
     * @param src Source IP Address as a string. e.g. "192.168.1.1".
     * @param dst Destination IP Address as a string. e.g. "192.168.1.1".
     * @param sport Source port as a string. e.g. 5001.
     * @param dport Destination port as a string. e.g. 5001.
     * @param protocol Protocol as a string. e.g. {TCP, UDP, ICMP}.
     * @param timeout Timeout for the rule, less than 0 is unlimited.
     * @return True if successful. TODO: Error check.
     */
    public boolean deleteRedirectRule(String src, String dst, String sport,
                                   String dport, String protocol, int timeout) {
        for (Device device : deviceService.getDevices()) {
            FlowRule f = createRedirectRule(device.id().toString(),
                                            createSelector(src, dst, sport, dport, protocol),
                                            timeout);
            applyRules(false, f);
            if (pendingRedirect.containsKey(device.id().toString())) {
                pendingRedirect.get(device.id().toString()).remove(createSelector(src, dst, sport, dport, protocol));
            }
        }
        return true;
    }

    /**
     * Add a mirror rule to a specific switch, matching the 5-tuple with a specific timeout.
     * Fields also accept '*' wildcard.
     *
     * @param src Source IP Address as a string. e.g. "192.168.1.1".
     * @param dst Destination IP Address as a string. e.g. "192.168.1.1".
     * @param sport Source port as a string. e.g. 5001.
     * @param dport Destination port as a string. e.g. 5001.
     * @param protocol Protocol as a string. e.g. {TCP, UDP, ICMP}.
     * @param timeout Timeout for the rule, less than 0 is unlimited.
     * @return True if successful. TODO: Error check.
     */
    public boolean addMirrorRule(String src, String dst, String sport,
                                 String dport, String protocol, int timeout) {

        ArrayList<String> suitableDevices = new ArrayList<>();

        try {
            // Select all suitable switches that have a snort instance connected
            suitableDevices = getSuitableSnortDevices(src, sport, dst, dport, protocol);
        } catch (Exception e) {
            log.error("getSuitableSnortDevices() " + e.toString());
        }

        if (suitableDevices.isEmpty()) {
            // Select all suitable switches
            suitableDevices = getSuitableDevices(src, sport, dst, dport, protocol);

            if (suitableDevices.isEmpty()) {
                log.info("Adding mirror rule to all switches");

                // Select all switches.
                for (final Device device : deviceService.getDevices()) {
                    suitableDevices.add(device.id().toString());
                }
            } else {
                log.info("Adding mirror rule to switches with matching flow");
            }
        } else {
            log.info("Adding mirror rule to switches with matching flow and a connected snort instance");
        }

        // Add mirror rule (or add to pending) to selected switches
        for (final String deviceid : suitableDevices) {

            TrafficSelector selector = createSelector(src, dst, sport, dport, protocol);

            if (snortPorts.containsKey(deviceid)) {
                FlowRule f = createMirrorRule(deviceid, selector, timeout);
                applyRules(true, f);
            } else {
                log.warn("No connected snort instance for " + deviceid +
                                 ". Installing on default port. Also adding mirror rule to pending list. " + snortPorts);
                if (!pendingMirror.containsKey(deviceid)) {
                    pendingMirror.put(deviceid, new ArrayList<>());
                }
                pendingMirror.get(deviceid).add(selector);

                FlowRule f = createMirrorRule(deviceid, selector, timeout);
                applyRules(true, f);
            }

        }

        return true;
    }

    /**
     * Delete a mirror rule to a specific switch, matching the 5-tuple with a specific timeout.
     * Fields also accept '*' wildcard.
     *
     * @param src Source IP Address as a string. e.g. "192.168.1.1".
     * @param dst Destination IP Address as a string. e.g. "192.168.1.1".
     * @param sport Source port as a string. e.g. 5001.
     * @param dport Destination port as a string. e.g. 5001.
     * @param protocol Protocol as a string. e.g. {TCP, UDP, ICMP}.
     * @param timeout Timeout for the rule, less than 0 is unlimited.
     * @return True if successful. TODO: Error check.
     */
    public boolean deleteMirrorRule(String src, String dst, String sport,
                                    String dport, String protocol, int timeout) {

        for (Device device : deviceService.getDevices()) {
            FlowRule f = createMirrorRule(device.id().toString(),
                                          createSelector(src, dst, sport, dport, protocol),
                                          timeout);
            applyRules(false, f);
            if (pendingMirror.containsKey(device.id().toString())) {
                pendingMirror.get(device.id().toString()).remove(createSelector(src, dst, sport, dport, protocol));
            }
        }

        return true;
    }

    /**
     * Add a block rule to a specific switch, matching the 5-tuple with a specific timeout.
     * Fields also accept '*' wildcard.
     *
     * @param src Source IP Address as a string. e.g. "192.168.1.1".
     * @param dst Destination IP Address as a string. e.g. "192.168.1.1".
     * @param sport Source port as a string. e.g. 5001.
     * @param dport Destination port as a string. e.g. 5001.
     * @param protocol Protocol as a string. e.g. {TCP, UDP, ICMP}.
     * @param timeout Timeout for the rule, less than 0 is unlimited.
     * @return True if successful. TODO: Error check.
     */
    public boolean addBlockRule(String src, String dst, String sport,
                                String dport, String protocol, int timeout) {

        final ArrayList<String> suitableDevices = getSuitableDevices(src, sport, dst, dport, protocol);

        // If no suitable devices - consider all
        if (suitableDevices.isEmpty()) {
            log.warn("No suitable devices for block - considering all devices");
            deviceService.getDevices().forEach(device -> suitableDevices.add(device.id().toString()));
        }

        // Install rules
        for (final String deviceid : suitableDevices) {
            FlowRule f = createBlockRule(deviceid, src, dst, sport, dport, protocol, timeout);
            applyRules(true, f);
        }

        //Delete redirect/mirror rules as we don't need to send data to SNORT anymore.
        deleteRedirectRule(src, dst, sport, dport, protocol, timeout);
        deleteMirrorRule(src, dst, sport, dport, protocol, timeout);
        return true;
    }

    /**
     * Delete a block rule to a specific switch, matching the 5-tuple with a specific timeout.
     * Fields also accept '*' wildcard.
     * @param src Source IP Address as a string. e.g. "192.168.1.1".
     * @param dst Destination IP Address as a string. e.g. "192.168.1.1".
     * @param sport Source port as a string. e.g. 5001.
     * @param dport Destination port as a string. e.g. 5001.
     * @param protocol Protocol as a string. e.g. {TCP, UDP, ICMP}.
     * @param timeout Timeout for the rule, less than 0 is unlimited.
     * @return True if successful. TODO: Error check.
     */
    public boolean deleteBlockRule(String src, String dst, String sport,
                                   String dport, String protocol, int timeout) {
        for (Device device : deviceService.getDevices()) {
            FlowRule f = createBlockRule(device.id().toString(), src, dst, sport, dport, protocol, timeout);
            applyRules(false, f);
        }
        return true;
    }

    /**
     * Create a selector for the identifying 5-tuple. Fields also accept '*' wildcard.
     * @param src Source IP Address as a string. e.g. "192.168.1.1".
     * @param dst Destination IP Address as a string. e.g. "192.168.1.1".
     * @param sport Source port as a string. e.g. 5001.
     * @param dport Destination port as a string. e.g. 5001.
     * @param protocol Protocol as a string. e.g. {TCP, UDP, ICMP}.
     * @return TrafficSelector mtaching on the tuple.
     */
    private TrafficSelector createSelector(String src, String dst, String sport,
                                           String dport, String protocol) {
        TrafficSelector.Builder selectorBuilder = DefaultTrafficSelector.builder();
        //Configure selector for specific IP Version

        selectorBuilder = selectorBuilder.matchEthType(Ethernet.TYPE_IPV4);
        if (!src.equals("*")) {
            Ip4Prefix matchIp4SrcPrefix = Ip4Prefix.valueOf(Ip4Address.valueOf(src), Ip4Prefix.MAX_MASK_LENGTH);
            selectorBuilder = selectorBuilder.matchIPSrc(matchIp4SrcPrefix);
        }
        if (!dst.equals("*")) {
            Ip4Prefix matchIp4DstPrefix = Ip4Prefix.valueOf(Ip4Address.valueOf(dst), Ip4Prefix.MAX_MASK_LENGTH);
            selectorBuilder = selectorBuilder.matchIPDst(matchIp4DstPrefix);
        }

        if (protocol.toLowerCase().equals("tcp")) {
            selectorBuilder = selectorBuilder.matchIPProtocol(IPv4.PROTOCOL_TCP);
            if (!sport.equals("*")) {
                selectorBuilder = selectorBuilder.matchTcpSrc(TpPort.tpPort(Integer.parseInt(sport)));
            }
            if (!dport.equals("*")) {
                selectorBuilder = selectorBuilder.matchTcpDst(TpPort.tpPort(Integer.parseInt(dport)));
            }
        } else if (protocol.toLowerCase().equals("udp")) {
            selectorBuilder = selectorBuilder.matchIPProtocol(IPv4.PROTOCOL_UDP);
            if (!sport.equals("*")) {
                selectorBuilder = selectorBuilder.matchUdpSrc(TpPort.tpPort(Integer.parseInt(sport)));
            }
            if (!dport.equals("*")) {
                selectorBuilder = selectorBuilder.matchUdpDst(TpPort.tpPort(Integer.parseInt(dport)));
            }
        } else if (protocol.toLowerCase().equals("icmp")) {
            selectorBuilder = selectorBuilder.matchIPProtocol(IPv4.PROTOCOL_ICMP);
            if (!sport.equals("*")) {
                selectorBuilder = selectorBuilder.matchIcmpType((byte) Integer.parseInt(sport));
            }
            if (!dport.equals("*")) {
                selectorBuilder = selectorBuilder.matchIcmpCode((byte) Integer.parseInt(dport));
            }
        }

        return selectorBuilder.build();
    }

    /**
     * Create a redirect flow rule.
     *
     * @param deviceid The string device id, e.g. of:0ff7843497029540.
     * @param timeout Timeout for the rule, less than 0 is unlimited.
     * @return FlowRule matching the input params.
     */
    private FlowRule createRedirectRule(String deviceid, TrafficSelector selector, int timeout) {

        int forTable = TUNNEL_TABLE;
        //Check if we know the port, otherise default is 0
        //int sp = (int) snortPorts.get(deviceid).values().toArray()[0];

        int sp = getSnortPort(deviceid);
        //.setOutput(PortNumber.portNumber(sp))

        TrafficTreatment tb = DefaultTrafficTreatment.builder()
                .pushVlan()
                .setVlanId(VlanId.vlanId(SNORT_VLAN_ID))
                .group(new GroupId(SNORT_GROUP_ID))
                .build();

        FlowRule.Builder ruleBuilder = DefaultFlowRule.builder()
                .fromApp(appId).withPriority(flowPriority)
                .forDevice(DeviceId.deviceId(deviceid))
                .withSelector(selector)
                .withTreatment(tb)
                .forTable(forTable);

        if (timeout > 0) {
            ruleBuilder.makeTemporary(timeout);
        } else {
            ruleBuilder.makePermanent();
        }


        return ruleBuilder.build();
    }

    /**
     * Create a mirror flow rule.
     *
     * @param deviceid The string device id, e.g. of:0ff7843497029540
     * @param timeout Timeout for the rule, less than 0 is unlimited.
     * @return FlowRule matching the input params.
     */
    private FlowRule createMirrorRule(String deviceid, TrafficSelector selector, int timeout) {

        int forTable = TUNNEL_TABLE;
        int transition = CLEANSING_TABLE;

        //Check if we know the port, otherise default is 0
        //int sp = (int) snortPorts.get(deviceid).values().toArray()[0];

        int sp = getSnortPort(deviceid);
        //.setOutput(PortNumber.portNumber(sp))

        TrafficTreatment tb = DefaultTrafficTreatment.builder()
                .pushVlan()
                .setVlanId(VlanId.vlanId(SNORT_VLAN_ID))
                .group(new GroupId(SNORT_GROUP_ID))
                .transition(transition)
                .build();

        FlowRule.Builder ruleBuilder = DefaultFlowRule.builder()
                .fromApp(appId).withPriority(flowPriority)
                .forDevice(DeviceId.deviceId(deviceid))
                .withSelector(selector)
                .withTreatment(tb)
                .forTable(forTable);

        if (timeout > 0) {
            ruleBuilder.makeTemporary(timeout);
        } else {
            ruleBuilder.makePermanent();
        }

        return ruleBuilder.build();
    }



    /**
     * Create a blocking flow rule.
     *
     * @param deviceid The string device id, e.g. of:0ff7843497029540.
     * @param src Source IP Address as a string. e.g. "192.168.1.1".
     * @param dst Destination IP Address as a string. e.g. "192.168.1.1".
     * @param sport Source port as a string. e.g. 5001.
     * @param dport Destination port as a string. e.g. 5001.
     * @param protocol Protocol as a string. e.g. {TCP, UDP, ICMP}.
     * @param timeout Timeout for the rule, less than 0 is unlimited.
     * @return Blocking FlowRule matching the input params.
     */
    private FlowRule createBlockRule(String deviceid, String src, String dst, String sport,
                                    String dport, String protocol, int timeout) {

        int forTable = BLOCK_TABLE;

        TrafficSelector selector = createSelector(src, dst, sport, dport, protocol);

        TrafficTreatment tb = DefaultTrafficTreatment.builder()
                .drop()
                .build();

        FlowRule.Builder ruleBuilder = DefaultFlowRule.builder()
                .fromApp(appId).withPriority(flowPriority)
                .forDevice(DeviceId.deviceId(deviceid))
                .withSelector(selector)
                .withTreatment(tb)
                .forTable(forTable);

        if (timeout > 0) {
            ruleBuilder.makeTemporary(timeout);
        } else {
            ruleBuilder.makePermanent();
        }

        return ruleBuilder.build();
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
    * Gets the snort port for the switch.
    * If no snort port, then use default.
    * @param deviceId
    */
    private int getSnortPort(String deviceId){
        if(snortPorts.containsKey(deviceId))
            return (int) snortPorts.get(deviceId).values().toArray()[0];
        else
            return DEFAULT_SNORT_OUT_PORT;
    }

    /**
     * Returns any snort instances that see the input flow.
     * @param saddr
     * @param sport
     * @param daddr
     * @param dport
     * @param protocol
     * @return
     */
    private ArrayList<String> getSuitableSnortDevices(String saddr, String sport,
                                                      String daddr, String dport,
                                                      String protocol) {
        ArrayList<String> suitableDevices = getSuitableDevices(saddr, sport, daddr, dport, protocol);

        HashMap<String, HashMap<String, Integer>> snortInstances = getSnortInstances();
        try{
            for (String device : new ArrayList<String>(suitableDevices)) {
                if (!snortInstances.containsKey(device)) {
                    suitableDevices.remove(device);
                }
            }

        } catch (Exception e) {
            log.error("Searching for snort instances connected to switches " + e.toString());
        }
        return suitableDevices;
    }

    /**
     * Returns all switches that have seen input flow.
     * @param saddr
     * @param sport
     * @param daddr
     * @param dport
     * @param protocol
     * @return
     */
    private ArrayList<String> getSuitableDevices(String saddr, String sport,
                                                 String daddr, String dport,
                                                 String protocol) {

        log.info(String.format("getSuitableDevices(%s, %s, %s, %s, %s)", saddr, sport, daddr, dport, protocol));

        ArrayList<String> suitableDevices = new ArrayList<>();

        // Get the set of switches
        final Iterable<Device> devices = deviceService.getDevices();

        if (devices == null) {
            log.info("devices is null");
            return suitableDevices;
        }

        // Iterate over all switches the controller is aware of.
        for (final Device device : devices) {
            log.info("Device: " + device.id());
            final Iterable<FlowEntry> flowEntries = flowRuleService.getFlowEntries(device.id());
            if (flowEntries != null) {

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

                        if (entry.selector().getCriterion(Criterion.Type.IPV4_SRC) == null ||
                                entry.selector().getCriterion(Criterion.Type.IPV4_DST) == null) {
                            log.info("IP criteria null");
                            continue;
                        }

                        // Get the IP4 source
                        IPCriterion srcIpCrit = (IPCriterion) entry.selector()
                                .getCriterion(Criterion.Type.IPV4_SRC);
                        // Get the IP4 dst
                        IPCriterion dstIpCrit = (IPCriterion) entry.selector()
                                .getCriterion(Criterion.Type.IPV4_DST);

                        // Check IP4 address matches the requested params
                        if ((!srcIpCrit.ip().address().toString().equals(saddr) && !saddr.equals("*")) ||
                                !dstIpCrit.ip().address().toString().equals(daddr) && !daddr.equals("*")) {
                            log.info("IPv4 Addresses do not match");
                            continue;
                        }
                    } else if (ethType == 0x86DD && saddr.contains(":")) {

                        if (entry.selector().getCriterion(Criterion.Type.IPV6_SRC) == null ||
                                entry.selector().getCriterion(Criterion.Type.IPV6_DST) == null) {
                            log.info("IP criteria null");
                            continue;
                        }

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

                    //Suitable Device
                    suitableDevices.add(device.id().toString());
                }
            } else {
                log.info("Flow Entries is null");
            }
        }

        return suitableDevices;
    }
}
