package org.onosproject.snort;

import java.util.HashMap;

/**
 * Created by richard on 26/02/16.
 */
public interface SnortService {
    boolean addSnortInstance(String newSnortIp);
    boolean removeSnortInstance(String ip);
    boolean clearSnortInstances();
    HashMap<String, HashMap<String, Integer>> getSnortInstances();
    boolean addMirrorRule(String src, String dst, String sport, String dport, String protocol,
                          int timeout);
    boolean deleteMirrorRule(String src, String dst, String sport, String dport, String protocol,
                             int timeout);
    boolean addRedirectRule(String src, String dst, String sport, String dport, String protocol,
                            int timeout);
    boolean deleteRedirectRule(String src, String dst, String sport, String dport, String protocol,
                               int timeout);
    boolean addBlockRule(String src, String dst, String sport, String dport, String protocol,
                         int timeout);
    boolean deleteBlockRule(String src, String dst, String sport, String dport, String protocol,
                            int timeout);
}