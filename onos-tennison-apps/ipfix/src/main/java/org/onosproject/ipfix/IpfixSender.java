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

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.util.Date;
import java.util.List;

import org.onlab.packet.IpAddress;
import org.onosproject.ipfix.packet.DataRecord;
import org.onosproject.ipfix.packet.HeaderException;
import org.onosproject.ipfix.packet.MessageHeader;
import org.onosproject.ipfix.packet.SetHeader;
import org.onosproject.ipfix.packet.TemplateRecord;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Sends IPFIX records.
 */
public final class IpfixSender {

    private static int seqNumber = 0;
    private static final int IPFIX_VERSION = 10;
    private static final int TEMPLATE_SETID = 2;

    protected static final Logger log = LoggerFactory.getLogger(IpfixSender.class);




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
     * Creates instance of the IPFIX Sender.
     *
     */
    private IpfixSender() {
    }

    /**
     * Send IPFIX Template and coresponding list of data records.
     *
     * @param tr Template Record to send
     * @param recordsList List of corresponding IPFIX records to send
     * @param oid observation domain ID
     * @param collector IPFIX collector IP address
     * @param port IPFIX collector UDP port
     */
    public static void sendRecords(TemplateRecord tr, List<DataRecord> recordsList,
                             long oid, IpAddress collector, int port) {

        MessageHeader mh = new MessageHeader();
        mh.setVersionNumber(IPFIX_VERSION);
        mh.setObservationDomainID(oid);
        seqNumber++;
        mh.setSequenceNumber(seqNumber);
        mh.setExportTime(new Date());

        // Set header for the template
        SetHeader shTemplate = new SetHeader();
        shTemplate.setSetID(TEMPLATE_SETID);

        // Add template record
        List<TemplateRecord> trTemp = shTemplate.getTemplateRecords();
        trTemp.add(tr);
        shTemplate.setTemplateRecords(trTemp);

        // Set header for the Data Records
        SetHeader shData = new SetHeader();
        shData.setSetID(tr.getTemplateID());

        // Add Data records from the recordsList
        List<DataRecord> drTemp = shData.getDataRecords();
        for (DataRecord tempRecord : recordsList) {
            drTemp.add(tempRecord);

          /* try{
           String tempStr = bytesToHex(tempRecord.getBytes());
           log.info("Send records : "+tempStr);
           } catch(Exception e){}*/


        }
        shData.setDataRecords(drTemp);

        // Make Set Headers from Template and Data
        List<SetHeader> shTemp = mh.getSetHeaders();
        shTemp.add(shTemplate);
        shTemp.add(shData);
        mh.setSetHeaders(shTemp);


        // socket handling and IPFIX UDP packet sending
        InetAddress collectorAddress = null;
        try {
            collectorAddress = InetAddress.getByAddress(collector.toOctets());
        } catch (UnknownHostException e) {
            log.warn("IPFIX Collector IP address format problem: " + e.getMessage());
            return;
        }
        DatagramSocket dSocket = null;
        DatagramPacket dPacket = null;
        try {
            log.info("Sending IPFIX to coordinator");
            dSocket = new DatagramSocket();
        } catch (SocketException e) {
            log.warn("IPFIX datagram socket problem: " + e.getMessage());
            return;
        }
        try {
            dPacket = new DatagramPacket(mh.getBytes(), mh.getBytes().length, collectorAddress, port);
        } catch (HeaderException e) {
            log.warn("IPFIX datagram packet problem: " + e.getMessage());
            dSocket.close();
            return;
        }
        try {
            dSocket.send(dPacket);
        } catch (IOException e) {
            log.warn("IPFIX packet send IO exception: " + e.getMessage());
            dSocket.close();
            return;
        }
        dSocket.close();
    }

}
