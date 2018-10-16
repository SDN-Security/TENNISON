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

import org.onlab.packet.IpAddress;
import org.onosproject.net.flow.FlowEntry;
import org.onosproject.net.flow.FlowRule;
import org.onosproject.net.flow.FlowRuleEvent;
import org.onosproject.net.flow.FlowRuleListener;

/**
 * Flow Rule Listener for detecting flow removal or flow statistics update by ONOS.
 */
public class FlowRuleEventListener implements FlowRuleListener {

    private IpfixManager ipfixManager;

    /**
     * Flow Event listener for Flow removed events of Reactive Forwarding application.
     *
     * @param ipfixManager ipfix manager instance
     */
    public FlowRuleEventListener(IpfixManager ipfixManager) {
        this.ipfixManager = ipfixManager;
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
                //ipfixManager.log.info("Rule Added");
                //handleEvent(rule, ipfixManager.getPrefixCollectorAddress(), ipfixManager.getPrefixCollectorPort());
                break;
            case RULE_REMOVED:
                //ipfixManager.log.info("Rule Removed");
                //handleEvent(rule, ipfixManager.getIpfixCollectorAddress(), ipfixManager.getIpfixCollectorPort());
                break;
            default:
                break;
        }
    }

    /**
     * handles the specific event.
     * @param rule The FlowRule that triggered the event.
     * @param collectorIp The IpAddress that the IPFIX record should be sent to.
     * @param collectorPort The Port that the IPFIX record should be sent to.
     */
    private void handleEvent(FlowRule rule, IpAddress collectorIp, int collectorPort) {
        FlowEntry entry = (FlowEntry) rule;
        String appName = ipfixManager.getRfwdAppName();
        // Check that the flow rule event came from the application we are interested in.
        if (entry.appId() == ipfixManager.coreService.getAppId(appName).id()) {
            try {
                IpfixEvent.createIpfixFlowRecord(ipfixManager.deviceService, entry, collectorIp, collectorPort);
            } catch (java.lang.IllegalArgumentException iae) {
                ipfixManager.log.error("Illegal Argument Exception: " + iae.getMessage());
            } catch (Exception e) {
                ipfixManager.log.error("Generic Exception: " + e.getMessage());
            }
        }
    }

}