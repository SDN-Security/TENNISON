package org.onosproject.ipfix;

import org.onlab.packet.IpAddress;

/**
 * Created by richard on 26/02/16.
 */
public interface IpfixService {
    public IpAddress getPrefixCollectorAddress();
    public int getPrefixCollectorPort();
    void addIpfix(String saddr, String sport, String daddr, String dport, String protocol);
    void addSingleIpfix(String saddr, String sport, String daddr, String dport, String protocol, String deviceId);
    void getFlowEntry(String saddr, String sport, String daddr, String dport, String protocol);
    void getFlowEntries();
}

