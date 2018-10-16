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

import java.util.List;

import org.onlab.packet.Ip6Address;
import org.onlab.packet.IpAddress;
import org.onlab.packet.MacAddress;
import org.onosproject.ipfix.packet.DataRecord;
import org.onosproject.ipfix.packet.HeaderException;
import org.onosproject.ipfix.packet.Ie;
import org.onosproject.ipfix.packet.InformationElement;
import org.onosproject.ipfix.packet.TemplateRecord;

import com.google.common.primitives.Ints;
import com.google.common.primitives.Longs;
import com.google.common.primitives.Shorts;

/**
 * IPFIX Data record for Reactive Forwarding application with L2 fields matching.
 */
public class DataRecordRfwdMac extends DataRecord {
    public static final int TEMPLATE_ID = 331;
    public static final int FIELD_COUNT = 12;
    public static final int LENGTH = 76;

    private IpAddress exporterIPv4Address;
    private IpAddress exporterIPv6Address;
    private long flowStartMilliseconds;
    private long flowEndMilliseconds;
    private long octetDeltaCount;
    private long packetDeltaCount;
    private int ingressInterface;
    private int egressInterface;
    private MacAddress sourceMacAddress;
    private MacAddress destinationMacAddress;
    private short ethernetType;
    private short vlanId;

    /**
     * IPFIX Data record for Reactive Forwarding application with L2 fields matching.
     *
     * @param exporterIpv4 IPv4 address of the IPFIX exporter
     * @param exporterIpv6 IPv6 address of the IPFIX exporter, used for DPID
     * @param start start timestamp of the flow
     * @param end end timestamp of the flow
     * @param octets number of bytes matched by the flow
     * @param packets number of packets matched by the flow
     * @param intfIn switch input interface of the flow
     * @param intfOut switch output interface of the flow
     * @param srcMac source MAC address
     * @param dstMac destination MAC address
     * @param etherType etherType field of the flow
     * @param vlan VLAN ID of the flow
     */
    public DataRecordRfwdMac(IpAddress exporterIpv4,
            Ip6Address exporterIpv6,
            long start,
            long end,
            long octets,
            long packets,
            int intfIn,
            int intfOut,
            MacAddress srcMac,
            MacAddress dstMac,
            short etherType,
            short vlan) {

        exporterIPv4Address = exporterIpv4;
        exporterIPv6Address = exporterIpv6;
        flowStartMilliseconds = start;
        flowEndMilliseconds = end;
        octetDeltaCount = octets;
        packetDeltaCount = packets;
        ingressInterface = intfIn;
        egressInterface = intfOut;
        sourceMacAddress = srcMac;
        destinationMacAddress = dstMac;
        ethernetType = etherType;
        vlanId = vlan;
    }

    @Override
    public int getLength() {
        return LENGTH;
    }

    @Override
    public byte[] getBytes() throws HeaderException {
        try {
            byte[] data = new byte[LENGTH];

            System.arraycopy(exporterIPv4Address.toOctets(), 0, data, 0, 4);
            System.arraycopy(exporterIPv6Address.toOctets(), 0, data, 4, 16);
            System.arraycopy(Longs.toByteArray(flowStartMilliseconds), 0, data, 20, 8);
            System.arraycopy(Longs.toByteArray(flowEndMilliseconds), 0, data, 28, 8);
            System.arraycopy(Longs.toByteArray(octetDeltaCount), 0, data, 36, 8);
            System.arraycopy(Longs.toByteArray(packetDeltaCount), 0, data, 44, 8);
            System.arraycopy(Ints.toByteArray(ingressInterface), 0, data, 52, 4);
            System.arraycopy(Ints.toByteArray(egressInterface), 0, data, 56, 4);
            System.arraycopy(sourceMacAddress.toBytes(), 0, data, 60, 6);
            System.arraycopy(destinationMacAddress.toBytes(), 0, data, 66, 6);
            System.arraycopy(Shorts.toByteArray(ethernetType), 0, data, 72, 2);
            System.arraycopy(Shorts.toByteArray(vlanId), 0, data, 74, 2);

            return data;
        } catch (Exception e) {
            throw new HeaderException("Error while generating the bytes: " + e.getMessage());
        }
    }

    /**
     * IPFIX Template record for Reactive Forwarding application with L2 fields matching.
     *
     * @return TemplateRecord IPFIX Template Record
     */
    public static TemplateRecord getTemplateRecord() {

        TemplateRecord tr = new TemplateRecord();
        tr.setTemplateID(TEMPLATE_ID);
        tr.setFieldCount(FIELD_COUNT);

        List<InformationElement> ieTemp = tr.getInformationElements();

        ieTemp.add(new InformationElement(Ie.exporterIPv4Address));
        ieTemp.add(new InformationElement(Ie.exporterIPv6Address));
        ieTemp.add(new InformationElement(Ie.flowStartMilliseconds));
        ieTemp.add(new InformationElement(Ie.flowEndMilliseconds));
        ieTemp.add(new InformationElement(Ie.octetDeltaCount));
        ieTemp.add(new InformationElement(Ie.packetDeltaCount));
        ieTemp.add(new InformationElement(Ie.ingressInterface));
        ieTemp.add(new InformationElement(Ie.egressInterface));
        ieTemp.add(new InformationElement(Ie.sourceMacAddress));
        ieTemp.add(new InformationElement(Ie.destinationMacAddress));
        ieTemp.add(new InformationElement(Ie.ethernetType));
        ieTemp.add(new InformationElement(Ie.vlanId));

        return tr;
    }
}
