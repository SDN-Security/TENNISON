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
package org.onosproject;

import org.apache.felix.scr.annotations.Component;
import org.apache.felix.scr.annotations.Property;
import org.apache.felix.scr.annotations.Reference;
import org.apache.felix.scr.annotations.ReferenceCardinality;
import org.apache.felix.scr.annotations.Activate;
import org.apache.felix.scr.annotations.Deactivate;

import org.onlab.packet.Ethernet;
/*import org.onlab.packet.IpAddress;
import org.onlab.packet.TpPort;
import org.onlab.packet.IPv4;
import org.onlab.packet.IPv6;
import org.onlab.packet.Ip4Prefix;
import org.onlab.packet.Ip6Prefix;
import org.onlab.packet.ICMP;
import org.onlab.packet.ICMP6;
import org.onlab.packet.UDP;
import org.onlab.packet.TCP;*/
import org.onlab.packet.IpAddress;
import org.onosproject.cfg.ComponentConfigService;
import org.onosproject.core.ApplicationId;
import org.onosproject.core.CoreService;
import org.onosproject.ipfix.IpfixEvent;
import org.onosproject.net.HostId;
import org.onosproject.net.Device;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.flow.FlowEntry;
import org.onosproject.net.flow.FlowRuleService;
import org.onosproject.net.flow.TrafficSelector;
import org.onosproject.net.flow.DefaultTrafficSelector;
//import org.onosproject.net.flow.TrafficTreatment;
//import org.onosproject.net.flow.DefaultTrafficTreatment;
//import org.onosproject.net.flowobjective.DefaultForwardingObjective;
import org.onosproject.net.flowobjective.FlowObjectiveService;
//import org.onosproject.net.flowobjective.ForwardingObjective;
import org.onosproject.net.packet.PacketService;
import org.onosproject.net.packet.PacketPriority;
import org.onosproject.net.packet.PacketProcessor;
import org.onosproject.net.packet.PacketContext;
import org.onosproject.net.packet.InboundPacket;
import org.onosproject.snort.SnortService;
import org.onosproject.ipfix.IpfixService;
import org.onosproject.ipfix.IpfixManager;
import org.onosproject.ipfix.packet.*;
import org.onosproject.ipfix.*;
import org.osgi.service.component.ComponentContext;
import org.slf4j.Logger;

import java.util.List;
import java.util.Dictionary;

import static org.onlab.util.Tools.get;
import static org.slf4j.LoggerFactory.getLogger;

/**
 * Flow Monitor Manager
 *
 * Installs flow objectives for packet in messages, with an empty treatment.
 */
@Component(immediate = true)
public class FlowMonitorManager {

    private static final int DEFAULT_TIMEOUT = 10;
    private static final int DEFAULT_PRIORITY = 10;
    private int flowTimeout = DEFAULT_TIMEOUT;
    private int flowPriority = DEFAULT_PRIORITY;

    private final Logger log = getLogger(getClass());

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected PacketService packetService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected FlowObjectiveService flowObjectiveService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected CoreService coreService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected ComponentConfigService cfgService;


    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected SnortService snortService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected FlowRuleService flowRuleService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected DeviceService deviceService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY_UNARY)
    protected IpfixService ipfixService;

    private FlowMonitorPacketProcessor processor = new FlowMonitorPacketProcessor();

    private ApplicationId appId;

    private static final String DEFAULT_MIRROR = "NO";
    @Property(name = "flowmonDefaultMirror", value = DEFAULT_MIRROR,
            label = "Mirror by default")
    private String flowmonDefaultMirror = DEFAULT_MIRROR;

    private static final boolean DEFAULT_USE_ONOS_INTERCEPTS = false; //A general purpose intercept is instead added by SecurityPipeline.
    @Property(name = "flowmonIntercepts", boolValue = DEFAULT_USE_ONOS_INTERCEPTS,
            label = "Use ONOS Intercepts")
    private boolean flowmonIntercepts = DEFAULT_USE_ONOS_INTERCEPTS;

    private static final boolean DEFAULT_IPFIX_IMMEDIATE = true; 
    @Property(name = "flowmonImmediateIPFIX", boolValue = DEFAULT_IPFIX_IMMEDIATE,
            label = "Install IPFIX immediately")
    private boolean flowmonImmediateIPFIX = DEFAULT_IPFIX_IMMEDIATE;

    /**
     * Start the component, called automatically.
     */
    @Activate
    public void activate(ComponentContext context) {
        appId = coreService.registerApplication("org.onosproject.flowmonitor");
        packetService.addProcessor(processor, PacketProcessor.director(1));
        cfgService.registerProperties(getClass());
        getProperties(context);
        if (flowmonIntercepts) {
            requestIntercepts();
        }
        log.info("Started", appId.id());
    }

    /**
     * Stop the component, called automatically.
     */
    @Deactivate
    public void deactivate() {
        if (flowmonIntercepts) {
            withdrawIntercepts();
        }
        log.info("Stopped");
    }

    /**
     * Get the properties configured by settings command line.
     */
    public void getProperties(ComponentContext context) {
        Dictionary<?, ?> properties = context.getProperties();

        // parse CollectorPort Property
        String s = get(properties, "flowmonDefaultMirror");
        flowmonDefaultMirror = s;

    }

    /**
     * Request packet in via packet service.
     */
    private void requestIntercepts() {
        TrafficSelector.Builder selector = DefaultTrafficSelector.builder();
        selector.matchEthType(Ethernet.TYPE_IPV4);
        packetService.requestPackets(selector.build(), PacketPriority.REACTIVE, appId);
        selector.matchEthType(Ethernet.TYPE_ARP);
        packetService.requestPackets(selector.build(), PacketPriority.REACTIVE, appId);
        selector.matchEthType(Ethernet.TYPE_IPV6);
        packetService.requestPackets(selector.build(), PacketPriority.REACTIVE, appId);
    }

    /**
     * Cancel request for packet in via packet service.
     */
    private void withdrawIntercepts() {
        TrafficSelector.Builder selector = DefaultTrafficSelector.builder();
        selector.matchEthType(Ethernet.TYPE_IPV4);
        packetService.cancelPackets(selector.build(), PacketPriority.REACTIVE, appId);
        selector.matchEthType(Ethernet.TYPE_ARP);
        packetService.cancelPackets(selector.build(), PacketPriority.REACTIVE, appId);
        selector.matchEthType(Ethernet.TYPE_IPV6);
        packetService.cancelPackets(selector.build(), PacketPriority.REACTIVE, appId);
    }

    /**
     *
     */
    private class FlowMonitorPacketProcessor implements PacketProcessor {

        String src = "*";
        String dst = "*";
        String sp = "*";
        String dp = "*";
        String p = "*";

        /**
         *
         * @param eth Packet to check type.
         * @return Indicates whether this is a control packet, e.g. LLDP, BDDP
         */
        private boolean isControlPacket(Ethernet eth) {
            short type = eth.getEtherType();
            return type == Ethernet.TYPE_LLDP || type == Ethernet.TYPE_BSN;
        }

        private boolean isIPPacket(Ethernet eth) {
            short type = eth.getEtherType();
            return type == Ethernet.TYPE_IPV4 || type == Ethernet.TYPE_IPV6;
        }

        @Override
        public void process(PacketContext context) {

            // Check if this packet has already been handled by another PacketProcessor.
            if (context.isHandled()) {
                return;
            }

            InboundPacket pkt = context.inPacket();
            Ethernet inPkt = pkt.parsed();
            //TrafficSelector.Builder selectorBuilder = DefaultTrafficSelector.builder();
            //HostId id = HostId.hostId(inPkt.getDestinationMAC());

            if(inPkt == null){
                log.warn("Packet in is null. Dropping packet.");
                return;
            }

            // Check if we are actually interested in monitoring this packet
            if (isControlPacket(inPkt)) {
                return;
            }

            // We only want ipv4 or ipv6 packets.
            if (!isIPPacket(inPkt)) {
                return;
            }

            //
            //if (id.mac().isLinkLocal()) {
            //    return;
            //}

            if(ipfixService == null){
                log.warn("Ipfix service is null. Ipfix not installed. Might be fixed using static vars");
                return;
            }

            if(deviceService == null){
                log.warn("Device service is null. Ipfix not installed. osgi problem");
                return;
            }

            if (flowmonImmediateIPFIX) { //Immediately add IPFIX to save time.
                log.info("Adding IPFIX immediately.");
                AbstractIpRecordInterface record = (AbstractIpRecordInterface) IpfixEvent.interpretIPPacket(deviceService, pkt);
                if (record == null) {
                    log.info("Packet could not be interpreted.");
                    return;
                }
                List<Data> dataList = record.getData();
                String saddr = "";
                String sport = "";
                String daddr = "";
                String dport = "";
                String protocol = "";
                for (Data d : dataList) {
                    String dataName = d.getDataName();
                    if (dataName.equals("sourceIPv4Address")) {
                        saddr = d.getDataValue().toString();
                    } else if (dataName.equals("destinationIPv4Address")) {
                        daddr = d.getDataValue().toString();
                    } else if (dataName.equals("sourceIPv6Address")) {
                        saddr = d.getDataValue().toString();
                    } else if (dataName.equals("destinationIPv6Address")) {
                        daddr = d.getDataValue().toString();
                    } else if (dataName.equals("sourceTransportPort")) {
                        sport = d.getDataValue().toString();
                    } else if (dataName.equals("destinationTransportPort")) {
                        dport = d.getDataValue().toString();
                    } else if (dataName.equals("protocolIdentifier")) {
                        Byte protoByte = (Byte) d.getDataValue();
                        int protoVal = protoByte.intValue();
                        if (protoVal == 1) {
                            protocol = "icmp";
                        } else if (protoVal == 6) {
                            protocol = "tcp";
                        } else if (protoVal == 17) {
                            protocol = "udp";
                        }
                    }
                }
                int templateId = record.getTemplateId();
                if (templateId == 333) {
                    //IpfixManager does not support IPv6 in the createIpfixSelector method.
                    log.warn("IPv6 is not supported");
                    return;
                }
                log.info("SRC PORT: "+sport+" DST PORT: "+dport);
                ipfixService.addSingleIpfix(saddr, sport, daddr, dport, protocol, pkt.receivedFrom().deviceId().toString());
            }

            //Send prefix message
            IpfixEvent.createIpfixFlowRecord(deviceService, pkt,
                                             IpAddress.valueOf(IpfixManager.PREFIX_COLLECTOR_ADDRESS),
                                             IpfixManager.PREFIX_COLLECTOR_PORT);

            /*
            // Add MAC addresses to the selector
            selectorBuilder.matchEthSrc(inPkt.getSourceMAC())
                    .matchEthDst(inPkt.getDestinationMAC());

            //Configure selector for specific IP Version
            if (inPkt.getEtherType() == Ethernet.TYPE_IPV4) {
                IPv4 ipv4Packet = (IPv4) inPkt.getPayload();
                byte ipv4Protocol = ipv4Packet.getProtocol();
                Ip4Prefix matchIp4SrcPrefix =
                        Ip4Prefix.valueOf(ipv4Packet.getSourceAddress(),
                                Ip4Prefix.MAX_MASK_LENGTH);
                Ip4Prefix matchIp4DstPrefix =
                        Ip4Prefix.valueOf(ipv4Packet.getDestinationAddress(),
                                Ip4Prefix.MAX_MASK_LENGTH);
                selectorBuilder.matchEthType(Ethernet.TYPE_IPV4)
                        .matchIPSrc(matchIp4SrcPrefix)
                        .matchIPDst(matchIp4DstPrefix);

                // Match Ports
                if (ipv4Protocol == IPv4.PROTOCOL_TCP) {
                    TCP tcpPacket = (TCP) ipv4Packet.getPayload();
                    selectorBuilder.matchIPProtocol(ipv4Protocol)
                            .matchTcpSrc(TpPort.tpPort(tcpPacket.getSourcePort()))
                            .matchTcpDst(TpPort.tpPort(tcpPacket.getDestinationPort()));
                    sp = Integer.toString(tcpPacket.getSourcePort());
                    dp = Integer.toString(tcpPacket.getDestinationPort());
                    p = "TCP";
                } else if (ipv4Protocol == IPv4.PROTOCOL_UDP) {
                    UDP udpPacket = (UDP) ipv4Packet.getPayload();
                    selectorBuilder.matchIPProtocol(ipv4Protocol)
                            .matchUdpSrc(TpPort.tpPort(udpPacket.getSourcePort()))
                            .matchUdpDst(TpPort.tpPort(udpPacket.getDestinationPort()));
                    sp = Integer.toString(udpPacket.getSourcePort());
                    dp = Integer.toString(udpPacket.getDestinationPort());
                    p = "UDP";
                } else if (ipv4Protocol == IPv4.PROTOCOL_ICMP) {
                    ICMP icmpPacket = (ICMP) ipv4Packet.getPayload();
                    selectorBuilder.matchIPProtocol(ipv4Protocol)
                            .matchIcmpType(icmpPacket.getIcmpType())
                            .matchIcmpCode(icmpPacket.getIcmpCode());
                    sp = Integer.toString(icmpPacket.getIcmpType());
                    dp = Integer.toString(icmpPacket.getIcmpCode());
                    p = "ICMP";
                }

                log.info("Packet In ({}): {} -> {}", context.inPacket().receivedFrom().port(),
                        IPv4.fromIPv4Address(ipv4Packet.getSourceAddress()),
                        IPv4.fromIPv4Address(ipv4Packet.getDestinationAddress()));

                src = IPv4.fromIPv4Address(ipv4Packet.getSourceAddress());
                dst = IPv4.fromIPv4Address(ipv4Packet.getDestinationAddress());

            } else if (inPkt.getEtherType() == Ethernet.TYPE_IPV6) {
                // Match on an IPV6 Packet.

                IPv6 ipv6Packet = (IPv6) inPkt.getPayload();
                byte ipv6NextHeader = ipv6Packet.getNextHeader();
                Ip6Prefix matchIp6SrcPrefix =
                        Ip6Prefix.valueOf(ipv6Packet.getSourceAddress(),
                                Ip6Prefix.MAX_MASK_LENGTH);
                Ip6Prefix matchIp6DstPrefix =
                        Ip6Prefix.valueOf(ipv6Packet.getDestinationAddress(),
                                Ip6Prefix.MAX_MASK_LENGTH);
                selectorBuilder.matchEthType(Ethernet.TYPE_IPV6)
                        .matchIPv6Src(matchIp6SrcPrefix)
                        .matchIPv6Dst(matchIp6DstPrefix);

                if (ipv6NextHeader == IPv6.PROTOCOL_TCP) {
                    TCP tcpPacket = (TCP) ipv6Packet.getPayload();
                    selectorBuilder.matchIPProtocol(ipv6NextHeader)
                            .matchTcpSrc(TpPort.tpPort(tcpPacket.getSourcePort()))
                            .matchTcpDst(TpPort.tpPort(tcpPacket.getDestinationPort()));
                } else if (ipv6NextHeader == IPv6.PROTOCOL_UDP) {
                    UDP udpPacket = (UDP) ipv6Packet.getPayload();
                    selectorBuilder.matchIPProtocol(ipv6NextHeader)
                            .matchUdpSrc(TpPort.tpPort(udpPacket.getSourcePort()))
                            .matchUdpDst(TpPort.tpPort(udpPacket.getDestinationPort()));
                } else if (ipv6NextHeader == IPv6.PROTOCOL_ICMP6) {
                    ICMP6 icmp6Packet = (ICMP6) ipv6Packet.getPayload();
                    selectorBuilder.matchIPProtocol(ipv6NextHeader)
                            .matchIcmpv6Type(icmp6Packet.getIcmpType())
                            .matchIcmpv6Code(icmp6Packet.getIcmpCode());
                }

                log.info("Packet In ({}): {} -> {}", context.inPacket().receivedFrom().port(),
                        ipv6Packet.getSourceAddress(),
                        ipv6Packet.getDestinationAddress());

            }

            TrafficSelector selector = selectorBuilder.build();
            if (checkIfMonitored(selector)) {
                log.info("Flow already monitored");
            } else {
                log.info("Flow not monitored");
                // Create an empty treatment as we just want a flow rule for monitoring
                TrafficTreatment treatment = DefaultTrafficTreatment.builder().build();

                //Create the forwarding objective with our selector and empty treatment
                ForwardingObjective forwardingObjective = DefaultForwardingObjective.builder()
                        .withSelector(selector)
                        .withTreatment(treatment)
                        .withPriority(flowPriority)
                        .withFlag(ForwardingObjective.Flag.SPECIFIC)
                        .fromApp(appId)
                        .makeTransparent(true)
                        .makeTemporary(flowTimeout)
                        .add();

                //Install the flowrule.
                flowObjectiveService.forward(context.inPacket().receivedFrom().deviceId(), forwardingObjective);
            }*/
        }
    }


    /**
    * Checks to see if ipfix has already been made for flow.
    *
    */
    private boolean checkIfMonitored(TrafficSelector selector) {

        if (deviceService == null) {
            log.info("DeviceService is null");
            return false;
        }

        // Get the set of switches
        final Iterable<Device> devices = deviceService.getDevices();

        if (devices == null) {
            log.info("devices is null");
            return false;
        }

        // Iterate over all switches the controller is aware of.
        for (final Device device : devices) {
            // Iterate over all the flow entries for each switch.
            for (final FlowEntry entry : flowRuleService.getFlowEntries(device.id())) {

                if (entry.appId() != appId.id()) {
                    log.info("AppID no match " + entry.appId() + " " + appId.id());
                    continue;
                }

                if (entry.selector().equals(selector)) {
                    return true;
                }
            }
        }

        return false;
    }
}
