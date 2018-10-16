package org.onosproject.ipfix;

import org.onlab.packet.ICMP;
import org.onlab.packet.ICMP6;
import org.onlab.packet.Ip4Address;
import org.onlab.packet.Ip6Address;
import org.onlab.packet.IpAddress;
import org.onlab.packet.IPv4;
import org.onlab.packet.IPv6;
import org.onlab.packet.MacAddress;
import org.onlab.packet.Ethernet;

import org.onlab.packet.TCP;
import org.onlab.packet.UDP;
import org.onosproject.ipfix.packet.DataRecord;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.flow.FlowEntry;
import org.onosproject.net.flow.criteria.Criterion;
import org.onosproject.net.flow.criteria.PortCriterion;
import org.onosproject.net.flow.criteria.EthCriterion;
import org.onosproject.net.flow.criteria.EthTypeCriterion;
import org.onosproject.net.flow.criteria.VlanIdCriterion;
import org.onosproject.net.flow.criteria.IPCriterion;
import org.onosproject.net.flow.criteria.IPProtocolCriterion;
import org.onosproject.net.flow.criteria.UdpPortCriterion;
import org.onosproject.net.flow.criteria.TcpPortCriterion;
import org.onosproject.net.flow.criteria.IPv6FlowLabelCriterion;
import org.onosproject.net.flow.criteria.IPDscpCriterion;
import org.onosproject.net.flow.criteria.IPEcnCriterion;
import org.onosproject.net.flow.criteria.IcmpTypeCriterion;
import org.onosproject.net.flow.criteria.Icmpv6TypeCriterion;
import org.onosproject.net.flow.criteria.IcmpCodeCriterion;
import org.onosproject.net.flow.criteria.Icmpv6CodeCriterion;


import com.google.common.primitives.Ints;
import com.google.common.primitives.Longs;
import com.google.common.primitives.Shorts;
import org.onosproject.net.flow.instructions.Instruction;
import org.onosproject.net.flow.instructions.Instructions;
import org.onosproject.net.packet.InboundPacket;
import org.onosproject.openflow.controller.Dpid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.nio.ByteBuffer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Created by richard on 14/01/16.
 */
public final class IpfixEvent {

    private IpfixEvent() {
    }

    protected static final Logger log = LoggerFactory.getLogger(IpfixEvent.getInstance().getClass());


    private static IpfixEvent event = null;

    private static IpfixEvent getInstance() {
        if (event == null) {
            event = new IpfixEvent();
        }
        return event;
    }

    /**
     * Added as a work around to Google API's not linking properly.
     * @param l the long to convert.
     * @return a byte array representation of the long.
     */
    private static byte[] longToByteArray(long l) {
        byte[] bytes = ByteBuffer.allocate(Long.SIZE / Byte.SIZE).putLong(l).array();
        return bytes;
    }



private final static char[] hexArray = "0123456789ABCDEF".toCharArray();
public static String bytesToHex(byte[] bytes) {
    char[] hexChars = new char[bytes.length * 2];
    for ( int j = 0; j < bytes.length; j++ ) {
        int v = bytes[j] & 0xFF;
        hexChars[j * 2] = hexArray[v >>> 4];
        hexChars[j * 2 + 1] = hexArray[v & 0x0F];
    }
    return new String(hexChars);
}
	
	/**
     * Interpret an IP packet for adding an IPFIX flow.
     * Should only be called on IP packets.
     *
     * @param pkt
     */
    public static DataRecord interpretIPPacket(DeviceService deviceService, InboundPacket pkt) {
        String deviceIp = deviceService.getDevice(pkt.receivedFrom().deviceId()).annotations().toString().split("=")[3].split(":")[0];
        // Exporters
        IpAddress exporterIpv4 = IpAddress.valueOf(deviceIp);

        // dpid to exportIPv6
        long dpid = Dpid.dpid(pkt.receivedFrom().deviceId().uri()).value();
        byte[] byteExporterIpv6 = new byte[16];
        System.arraycopy(longToByteArray(0), 0, byteExporterIpv6, 0, 8);
        System.arraycopy(longToByteArray(dpid), 0, byteExporterIpv6, 8, 8);
        Ip6Address exporterIpv6 = Ip6Address.valueOf(byteExporterIpv6);

        // Timestamps, octets, packets
        long start = System.currentTimeMillis();
        long end = System.currentTimeMillis();
        long octets = 0;
        long packets = 0;

        // Input and Output ports
        int intfIn = (int) pkt.receivedFrom().port().toLong();
        int intfOut = 0;

        Ethernet eth = pkt.parsed();

        // Ethernet MACs, Ethertype and VLAN
        MacAddress srcMac = eth.getSourceMAC();
        MacAddress dstMac = eth.getDestinationMAC();
        Short ethType = eth.getEtherType();
        Short vlan = eth.getVlanID();

        if (ethType == Ethernet.TYPE_IPV4) {
            //Send IPv4 data record
            IPv4 ipv4Packet = (IPv4) eth.getPayload();
            byte ipProtocol = ipv4Packet.getProtocol();

            //qos
            byte dscp = ipv4Packet.getDscp();
            byte ecn = ipv4Packet.getEcn();
            byte tos = (byte) ((byte) (dscp << 2) | ecn);

            //address
            IpAddress srcIp = Ip4Address.valueOf(ipv4Packet.getSourceAddress());
            IpAddress dstIp = Ip4Address.valueOf(ipv4Packet.getDestinationAddress());

            int srcPort = 0;
            int dstPort = 0;
            if (ipProtocol == IPv4.PROTOCOL_TCP) {
                TCP tcpPacket = (TCP) ipv4Packet.getPayload();
                srcPort = tcpPacket.getSourcePort();
                dstPort = tcpPacket.getDestinationPort();
            } else if (ipProtocol == IPv4.PROTOCOL_UDP) {
                UDP udpPacket = (UDP) ipv4Packet.getPayload();
                srcPort = udpPacket.getSourcePort();
                dstPort = udpPacket.getDestinationPort();
            } else if (ipProtocol == IPv4.PROTOCOL_ICMP) {
                ICMP icmpPacket = (ICMP) ipv4Packet.getPayload();
                Short icmpType = (short) icmpPacket.getIcmpType();
                Short icmpCode = (short) icmpPacket.getIcmpCode();
                srcPort = icmpType;
                dstPort = icmpCode;
            }

         //   log.info("Byte array length : " + Ints.toByteArray(srcPort).length);

            DataRecordRfwdIpv4 record = new DataRecordRfwdIpv4(
                    exporterIpv4, exporterIpv6,
                    start, end,
                    octets, packets,
                    intfIn, intfOut,
                    srcMac, dstMac,
                    ethType, vlan,
                    srcIp, dstIp,
                    ipProtocol, tos,
                    srcPort, dstPort);
/*
           try{
           String tempStr = bytesToHex(record.getBytes());

           String tempStr2 = bytesToHex(Ints.toByteArray(srcPort));
           String tempStr3 = bytesToHex( Arrays.copyOfRange(Ints.toByteArray(srcPort),2,4));
           log.info(tempStr);
           log.info(tempStr2);
           log.info(tempStr3);
           } catch(Exception e){}*/
           return record;

        } else if (ethType == Ethernet.TYPE_IPV6) {
            //Send IPv6 data record
            IPv6 ipv6Packet = (IPv6) eth.getPayload();
            byte ipProtocol = ipv6Packet.getNextHeader();

            // Is this relevant with v6??
            byte tos = 0x00;
            int flowLabelIpv6 = ipv6Packet.getFlowLabel();

            Ip6Address srcIp = Ip6Address.valueOf(ipv6Packet.getSourceAddress());
            Ip6Address dstIp = Ip6Address.valueOf(ipv6Packet.getDestinationAddress());

            int srcPort = 0;
            int dstPort = 0;
            if (ipProtocol == IPv6.PROTOCOL_TCP) {
                TCP tcpPacket = (TCP) ipv6Packet.getPayload();
                srcPort = tcpPacket.getSourcePort();
                dstPort = tcpPacket.getDestinationPort();
            } else if (ipProtocol == IPv6.PROTOCOL_UDP) {
                UDP udpPacket = (UDP) ipv6Packet.getPayload();
                srcPort = udpPacket.getSourcePort();
                dstPort = udpPacket.getDestinationPort();
            } else if (ipProtocol == IPv6.PROTOCOL_ICMP6) {
                ICMP6 icmpPacket = (ICMP6) ipv6Packet.getPayload();
                Short icmpType = (short) icmpPacket.getIcmpType();
                Short icmpCode = (short) icmpPacket.getIcmpCode();
                srcPort = icmpType;
                dstPort = icmpCode;
            }
            DataRecordRfwdIpv6 record = new DataRecordRfwdIpv6(
                    exporterIpv4, exporterIpv6,
                    start, end,
                    octets, packets,
                    intfIn, intfOut,
                    srcMac, dstMac,
                    ethType, vlan,
                    srcIp, dstIp,
                    flowLabelIpv6,
                    ipProtocol, tos,
                     srcPort, dstPort);
			return record;
        }
		return null; //Should really throw an error.
    }

    /**
     * Handle ONOS Reactive forwarding application flow removal.
     * When flow is removed, generate and send IPFIX record.
     *
     * @param pkt
     */
    public static void createIpfixFlowRecord(DeviceService deviceService, InboundPacket pkt,
                                             IpAddress collectorIp, int collectorPort) {
        
        log.info("Creating ipfix flow record");
        String deviceIp = deviceService.getDevice(pkt.receivedFrom().deviceId()).annotations().toString().split("=")[3].split(":")[0];
        // Exporters
        IpAddress exporterIpv4 = IpAddress.valueOf(deviceIp);

        // dpid to exportIPv6
        long dpid = Dpid.dpid(pkt.receivedFrom().deviceId().uri()).value();
        byte[] byteExporterIpv6 = new byte[16];
        System.arraycopy(longToByteArray(0), 0, byteExporterIpv6, 0, 8);
        System.arraycopy(longToByteArray(dpid), 0, byteExporterIpv6, 8, 8);
        Ip6Address exporterIpv6 = Ip6Address.valueOf(byteExporterIpv6);

        // Timestamps, octets, packets
        long start = System.currentTimeMillis();
        long end = System.currentTimeMillis();
        long octets = 0;
        long packets = 0;

        // Input and Output ports
        int intfIn = (int) pkt.receivedFrom().port().toLong();
        int intfOut = 0;

        Ethernet eth = pkt.parsed();

        // Ethernet MACs, Ethertype and VLAN
        MacAddress srcMac = eth.getSourceMAC();
        MacAddress dstMac = eth.getDestinationMAC();
        Short ethType = eth.getEtherType();
        Short vlan = eth.getVlanID();

        if (ethType == Ethernet.TYPE_IPV4) {
            //Send IPv4 data record
            IPv4 ipv4Packet = (IPv4) eth.getPayload();
            byte ipProtocol = ipv4Packet.getProtocol();

            //qos
            byte dscp = ipv4Packet.getDscp();
            byte ecn = ipv4Packet.getEcn();
            byte tos = (byte) ((byte) (dscp << 2) | ecn);

            //address
            IpAddress srcIp = Ip4Address.valueOf(ipv4Packet.getSourceAddress());
            IpAddress dstIp = Ip4Address.valueOf(ipv4Packet.getDestinationAddress());

            int srcPort = 0;
            int dstPort = 0;
            if (ipProtocol == IPv4.PROTOCOL_TCP) {
                TCP tcpPacket = (TCP) ipv4Packet.getPayload();
                srcPort = tcpPacket.getSourcePort();
                dstPort = tcpPacket.getDestinationPort();
            } else if (ipProtocol == IPv4.PROTOCOL_UDP) {
                UDP udpPacket = (UDP) ipv4Packet.getPayload();
                srcPort = udpPacket.getSourcePort();
                dstPort = udpPacket.getDestinationPort();
            } else if (ipProtocol == IPv4.PROTOCOL_ICMP) {
                ICMP icmpPacket = (ICMP) ipv4Packet.getPayload();
                Short icmpType = (short) icmpPacket.getIcmpType();
                Short icmpCode = (short) icmpPacket.getIcmpCode();
                srcPort = icmpType;
                dstPort = icmpCode;
            }
            DataRecordRfwdIpv4 record = new DataRecordRfwdIpv4(
                    exporterIpv4, exporterIpv6,
                    start, end,
                    octets, packets,
                    intfIn, intfOut,
                    srcMac, dstMac,
                    ethType, vlan,
                    srcIp, dstIp,
                    ipProtocol, tos,
                    srcPort, dstPort);
        /*    
try{
           String tempStr = bytesToHex(record.getBytes());
           log.info("Creating Flow record :" +tempStr);

           } catch(Exception e){}*/
            List<DataRecord> recordList = new ArrayList<DataRecord>();
            recordList.add(record);
            IpfixSender.sendRecords(DataRecordRfwdIpv4.getTemplateRecord(),
                                    recordList, dpid, collectorIp, collectorPort);

        } else if (ethType == Ethernet.TYPE_IPV6) {
            //Send IPv6 data record
            IPv6 ipv6Packet = (IPv6) eth.getPayload();
            byte ipProtocol = ipv6Packet.getNextHeader();

            // Is this relevant with v6??
            byte tos = 0x00;
            int flowLabelIpv6 = ipv6Packet.getFlowLabel();

            Ip6Address srcIp = Ip6Address.valueOf(ipv6Packet.getSourceAddress());
            Ip6Address dstIp = Ip6Address.valueOf(ipv6Packet.getDestinationAddress());

            int srcPort = 0;
            int dstPort = 0;
            if (ipProtocol == IPv6.PROTOCOL_TCP) {
                TCP tcpPacket = (TCP) ipv6Packet.getPayload();
                srcPort = tcpPacket.getSourcePort();
                dstPort = tcpPacket.getDestinationPort();
            } else if (ipProtocol == IPv6.PROTOCOL_UDP) {
                UDP udpPacket = (UDP) ipv6Packet.getPayload();
                srcPort = udpPacket.getSourcePort();
                dstPort = udpPacket.getDestinationPort();
            } else if (ipProtocol == IPv6.PROTOCOL_ICMP6) {
                ICMP6 icmpPacket = (ICMP6) ipv6Packet.getPayload();
                Short icmpType = (short) icmpPacket.getIcmpType();
                Short icmpCode = (short) icmpPacket.getIcmpCode();
                srcPort = icmpType;
                dstPort = icmpCode;
            }
            DataRecordRfwdIpv6 record = new DataRecordRfwdIpv6(
                    exporterIpv4, exporterIpv6,
                    start, end,
                    octets, packets,
                    intfIn, intfOut,
                    srcMac, dstMac,
                    ethType, vlan,
                    srcIp, dstIp,
                    flowLabelIpv6,
                    ipProtocol, tos,
                    srcPort, dstPort);
            List<DataRecord> recordList = new ArrayList<DataRecord>();
            recordList.add(record);
            IpfixSender.sendRecords(DataRecordRfwdIpv6.getTemplateRecord(),
                                    recordList, dpid, collectorIp, collectorPort);

        } else {
            //Send MAC data record
            DataRecordRfwdMac record = new DataRecordRfwdMac(
                    exporterIpv4, exporterIpv6,
                    start, end,
                    octets, packets,
                    intfIn, intfOut,
                    srcMac, dstMac,
                    ethType, vlan);
            List<DataRecord> recordList = new ArrayList<DataRecord>();
            recordList.add(record);
            IpfixSender.sendRecords(DataRecordRfwdMac.getTemplateRecord(),
                                    recordList, dpid, collectorIp, collectorPort);
        }
    }

    /**
     * Handle ONOS Reactive forwarding application flow removal.
     * When flow is removed, generate and send IPFIX record.
     *
     * @param entry flow entry removed from ONOS
     */
    public static void createIpfixFlowRecord(DeviceService deviceService, FlowEntry entry,
                                             IpAddress collectorIp, int collectorPort) {

        //Log
        log.trace("Create Flow Record for" +
                " Reactive Forwarding, id={}, device={}, selector={}, treatment={}",
                entry.id(), entry.deviceId(), entry.selector(), entry.treatment());

        // Exporters
        IpAddress exporterIpv4 = IpAddress.valueOf(deviceService.getDevice(
                entry.deviceId()).annotations().toString().split("=")[3].split(":")[0]);

        // dpid to exportIPv6
        long dpid = Dpid.dpid(entry.deviceId().uri()).value();
        byte[] byteExporterIpv6 = new byte[16];
        System.arraycopy(longToByteArray(0), 0, byteExporterIpv6, 0, 8);
        System.arraycopy(longToByteArray(dpid), 0, byteExporterIpv6, 8, 8);
        Ip6Address exporterIpv6 = Ip6Address.valueOf(byteExporterIpv6);

        // Timestamps, octets, packets
        long start = System.currentTimeMillis() - (1000 * entry.life());
        long end = System.currentTimeMillis();
        long octets = entry.bytes();
        long packets = entry.packets();

        // Input and Output ports
        PortCriterion portCrit = (PortCriterion) entry.selector().getCriterion(Criterion.Type.IN_PORT);
        int intfIn = (portCrit == null) ? 0 : (int) portCrit.port().toLong();
        List<Instruction> instructions = entry.treatment().allInstructions();
        int intfOut = 0;
        for (Instruction instruction : instructions) {
            if (instruction.type() == Instruction.Type.OUTPUT) {
                Instructions.OutputInstruction outputInstruction = (Instructions.OutputInstruction) instruction;
                intfOut = (outputInstruction == null) ? 0 : (int) outputInstruction.port().toLong();
            }
        }

        // Ethernet MACs, Ethertype and VLAN
        EthCriterion ethCrit;
        ethCrit = (EthCriterion) entry.selector().getCriterion(Criterion.Type.ETH_SRC);
        MacAddress srcMac = (ethCrit == null) ? MacAddress.valueOf("00:00:00:00:00:00") : ethCrit.mac();
        ethCrit = (EthCriterion) entry.selector().getCriterion(Criterion.Type.ETH_DST);
        MacAddress dstMac = (ethCrit == null) ? MacAddress.valueOf("00:00:00:00:00:00") : ethCrit.mac();

        EthTypeCriterion ethTypeCrit = (EthTypeCriterion) entry.selector().getCriterion(Criterion.Type.ETH_TYPE);
        Short ethType = (ethTypeCrit == null) ? 0x0000 : ethTypeCrit.ethType().toShort();

        VlanIdCriterion vlanCrit = (VlanIdCriterion) entry.selector().getCriterion(Criterion.Type.VLAN_VID);
        Short vlan = (vlanCrit == null) ? 0x0000 : vlanCrit.vlanId().toShort();

        // IP Criterion check
        IPCriterion srcIpCrit = (IPCriterion) entry.selector().getCriterion(Criterion.Type.IPV4_SRC);
        IPCriterion dstIpCrit = (IPCriterion) entry.selector().getCriterion(Criterion.Type.IPV4_DST);
        IPCriterion srcIp6Crit = (IPCriterion) entry.selector().getCriterion(Criterion.Type.IPV6_SRC);
        IPCriterion dstIp6Crit = (IPCriterion) entry.selector().getCriterion(Criterion.Type.IPV6_DST);

        // If IP criterions are null send MAC Data Record, else send IPv4 or IPv6 Data Record
        if (srcIpCrit == null && dstIpCrit == null && srcIp6Crit == null && dstIp6Crit == null) {
            DataRecordRfwdMac record = new DataRecordRfwdMac(
                    exporterIpv4, exporterIpv6,
                    start, end,
                    octets, packets,
                    intfIn, intfOut,
                    srcMac, dstMac,
                    ethType, vlan);
            List<DataRecord> recordList = new ArrayList<DataRecord>();
            recordList.add(record);
            IpfixSender.sendRecords(DataRecordRfwdMac.getTemplateRecord(),
                    recordList, dpid, collectorIp, collectorPort);
        } else {
            // Checking IPv4 and IPv6 criterions
            IPProtocolCriterion protocolCrit = (IPProtocolCriterion) entry.selector()
                    .getCriterion(Criterion.Type.IP_PROTO);
            byte ipProtocol = (protocolCrit == null) ? (byte) 0xff : (byte) protocolCrit.protocol();

            IPDscpCriterion dscpCrit = (IPDscpCriterion) entry.selector().getCriterion(Criterion.Type.IP_DSCP);
            byte dscp = (dscpCrit == null) ? 0x00 : dscpCrit.ipDscp();
            IPEcnCriterion ecnCrit = (IPEcnCriterion) entry.selector().getCriterion(Criterion.Type.IP_ECN);
            byte ecn = (ecnCrit == null) ? 0x00 : ecnCrit.ipEcn();
            byte tos = (byte) ((byte) (dscp << 2) | ecn);

            IPv6FlowLabelCriterion flowLabelCrit =
                    (IPv6FlowLabelCriterion) entry.selector().getCriterion(Criterion.Type.IPV6_FLABEL);
            int flowLabelIpv6 = (flowLabelCrit == null) ? 0 : flowLabelCrit.flowLabel();

            int srcPort = 0;
            int dstPort = 0;
            if (ipProtocol == IPv4.PROTOCOL_TCP) {
                TcpPortCriterion tcpCrit;
                tcpCrit = (TcpPortCriterion) entry.selector().getCriterion(Criterion.Type.TCP_SRC);
                srcPort = (tcpCrit == null) ? 0 : tcpCrit.tcpPort().toInt();
                tcpCrit = (TcpPortCriterion) entry.selector().getCriterion(Criterion.Type.TCP_DST);
                dstPort = (tcpCrit == null) ? 0 : tcpCrit.tcpPort().toInt();
            } else if (ipProtocol == IPv4.PROTOCOL_UDP) {
                UdpPortCriterion udpCrit;
                udpCrit = (UdpPortCriterion) entry.selector().getCriterion(Criterion.Type.UDP_SRC);
                srcPort = (udpCrit == null) ? 0 : udpCrit.udpPort().toInt();
                udpCrit = (UdpPortCriterion) entry.selector().getCriterion(Criterion.Type.UDP_DST);
                dstPort = (udpCrit == null) ? 0 : udpCrit.udpPort().toInt();
            } else if (ipProtocol == IPv4.PROTOCOL_ICMP) {
                IcmpTypeCriterion icmpTypeCrit = (IcmpTypeCriterion) entry.selector()
                        .getCriterion(Criterion.Type.ICMPV4_TYPE);
                Short icmpType = (icmpTypeCrit == null) ? 0 : icmpTypeCrit.icmpType();
                IcmpCodeCriterion icmpCodeCrit = (IcmpCodeCriterion) entry.selector()
                        .getCriterion(Criterion.Type.ICMPV4_CODE);
                Short icmpCode = (icmpCodeCrit == null) ? 0 : icmpCodeCrit.icmpCode();
                srcPort = icmpType;
                dstPort = icmpCode;
            } else if (ipProtocol == IPv6.PROTOCOL_ICMP6) {
                Icmpv6TypeCriterion icmpv6TypeCrit =
                        (Icmpv6TypeCriterion) entry.selector().getCriterion(Criterion.Type.ICMPV6_TYPE);
                Short icmpType = (icmpv6TypeCrit == null) ? 0 : icmpv6TypeCrit.icmpv6Type();
                Icmpv6CodeCriterion icmpv6CodeCrit =
                        (Icmpv6CodeCriterion) entry.selector().getCriterion(Criterion.Type.ICMPV6_CODE);
                Short icmpCode = (icmpv6CodeCrit == null) ? 0 : icmpv6CodeCrit.icmpv6Code();
                srcPort = icmpType;
                dstPort = icmpCode;
            }
            // If IPv4 than send IPv4 Data record
            if ((srcIpCrit != null || dstIpCrit != null) && ethType == Ethernet.TYPE_IPV4) {
                IpAddress srcIp = (srcIpCrit == null) ? IpAddress.valueOf(0) : srcIpCrit.ip().address();
                IpAddress dstIp = (dstIpCrit == null) ? IpAddress.valueOf(0) : dstIpCrit.ip().address();
                DataRecordRfwdIpv4 record = new DataRecordRfwdIpv4(
                        exporterIpv4, exporterIpv6,
                        start, end,
                        octets, packets,
                        intfIn, intfOut,
                        srcMac, dstMac,
                        ethType, vlan,
                        srcIp, dstIp,
                        ipProtocol, tos,
                        srcPort, dstPort);
                


                List<DataRecord> recordList = new ArrayList<DataRecord>();
                recordList.add(record);
                IpfixSender.sendRecords(DataRecordRfwdIpv4.getTemplateRecord(),
                        recordList, dpid, collectorIp, collectorPort);
            }
            // If IPv6 than send IPv6 Data record
            if ((srcIp6Crit != null || dstIp6Crit != null) && ethType == Ethernet.TYPE_IPV6) {
                Ip6Address srcIp6 = (srcIp6Crit == null) ?
                        Ip6Address.valueOf("0:0:0:0:0:0:0:0") : srcIp6Crit.ip().address().getIp6Address();
                Ip6Address dstIp6 = (dstIp6Crit == null) ?
                        Ip6Address.valueOf("0:0:0:0:0:0:0:0") : dstIp6Crit.ip().address().getIp6Address();
                DataRecordRfwdIpv6 record = new DataRecordRfwdIpv6(
                        exporterIpv4, exporterIpv6,
                        start, end,
                        octets, packets,
                        intfIn, intfOut,
                        srcMac, dstMac,
                        ethType, vlan,
                        srcIp6, dstIp6,
                        flowLabelIpv6,
                        ipProtocol, tos,
                        srcPort, dstPort);
                List<DataRecord> recordList = new ArrayList<DataRecord>();
                recordList.add(record);
                IpfixSender.sendRecords(DataRecordRfwdIpv6.getTemplateRecord(),
                        recordList, dpid, collectorIp, collectorPort);
            }
        }
    }
}
