package org.onosproject.driver.handshaker;

import org.onosproject.openflow.controller.driver.SwitchDriverSubHandshakeAlreadyStarted;
import org.onosproject.openflow.controller.driver.SwitchDriverSubHandshakeCompleted;
import org.onosproject.openflow.controller.driver.SwitchDriverSubHandshakeNotStarted;
import org.projectfloodlight.openflow.protocol.OFFactories;
import org.projectfloodlight.openflow.protocol.OFFactory;
import org.projectfloodlight.openflow.protocol.OFMessage;
import org.projectfloodlight.openflow.protocol.OFStatsReplyFlags;
import org.projectfloodlight.openflow.protocol.OFTableFeatureProp;
import org.projectfloodlight.openflow.protocol.OFTableFeatures;
import org.projectfloodlight.openflow.protocol.OFTableFeaturesStatsReply;
import org.projectfloodlight.openflow.protocol.OFTableFeaturesStatsRequest;
import org.projectfloodlight.openflow.protocol.OFType;
import org.projectfloodlight.openflow.protocol.OFVersion;
import org.projectfloodlight.openflow.protocol.actionid.OFActionId;
import org.projectfloodlight.openflow.protocol.instructionid.OFInstructionId;
import org.projectfloodlight.openflow.protocol.ver13.OFActionIdsVer13;
import org.projectfloodlight.openflow.protocol.ver13.OFInstructionIdsVer13;
import org.projectfloodlight.openflow.types.TableId;
import org.projectfloodlight.openflow.types.U32;
import org.projectfloodlight.openflow.types.U64;
import org.projectfloodlight.openflow.types.U8;
import org.slf4j.Logger;

import java.util.LinkedList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

import static org.slf4j.LoggerFactory.getLogger;

public class HPSwitchHandshaker extends DefaultSwitchHandshaker {

    private final Logger log = getLogger(getClass());

    private AtomicBoolean handshakeComplete = new AtomicBoolean(false);

    private int emptyXid;
    private int reqXid;
    private int checkXid;

    private List<OFTableFeatures> entries;

    public void startDriverHandshake() {
        if (startDriverHandshakeCalled) {
            throw new SwitchDriverSubHandshakeAlreadyStarted();
        }
        startDriverHandshakeCalled = true;

        setCustomPipeline();

        emptyXid = getNextTransactionId();
        OFTableFeaturesStatsRequest empty = factory().buildTableFeaturesStatsRequest()
                .setXid(emptyXid).build();
        log.info("Sending empty request: " + empty.toString());
        sendHandshakeMessage(empty);


        reqXid = getNextTransactionId();
        OFTableFeaturesStatsRequest request = factory().buildTableFeaturesStatsRequest()
                .setEntries(entries).setXid(reqXid).build();
        log.info("Sending actual request: " + request.toString());
        sendHandshakeMessage(request);


        checkXid = getNextTransactionId();
        OFTableFeaturesStatsRequest check = factory().buildTableFeaturesStatsRequest()
                .setXid(checkXid).build();
        log.info("Sending checking request: " + check.toString());
        sendHandshakeMessage(check);

    }

    @Override
    public boolean isDriverHandshakeComplete() {
        if (!startDriverHandshakeCalled) {
            throw new SwitchDriverSubHandshakeAlreadyStarted();
        }
        return handshakeComplete.get();
    }

    @Override
    public void processDriverHandshakeMessage(OFMessage m) {
        if (!startDriverHandshakeCalled) {
            throw new SwitchDriverSubHandshakeNotStarted();
        }
        if (handshakeComplete.get()) {
            throw new SwitchDriverSubHandshakeCompleted(m);
        }
        if (m.getType() == OFType.STATS_REPLY) {
            if (m.getXid() == emptyXid) {
                log.info("Received reply for empty request!");
            } else if (m.getXid() == reqXid) {
                log.info("Received reply for actual request!");
                log.info("Request reply: " + m.toString());
            } else if (m.getXid() == checkXid) {
                log.info("Received reply for checking request!");
                log.info("Check reply: " + m.toString());
                OFTableFeaturesStatsReply msg = (OFTableFeaturesStatsReply) m;
                if (!msg.getFlags().contains(OFStatsReplyFlags.REPLY_MORE)) {
                    handshakeComplete.set(true);
                }
            }
        } else if (m.getType() == OFType.ERROR) {
            log.error(m.toString());
            if (m.getXid() == reqXid || m.getXid() == checkXid) {
                handshakeComplete.set(true);
            }
        }
    }

    private void setCustomPipeline() {
        OFFactory factory = OFFactories.getFactory(OFVersion.OF_13);
        LinkedList<OFTableFeatures> tempEntries = new LinkedList<>();
        LinkedList<OFTableFeatureProp> properties = new LinkedList<>();
        LinkedList<OFInstructionId> instructIds = new LinkedList<>();
        instructIds.add(OFInstructionIdsVer13.INSTANCE.gotoTable()); //5.9 Instructions
        instructIds.add(OFInstructionIdsVer13.INSTANCE.applyActions());
        instructIds.add(OFInstructionIdsVer13.INSTANCE.clearActions());
        instructIds.add(OFInstructionIdsVer13.INSTANCE.writeActions());
        instructIds.add(OFInstructionIdsVer13.INSTANCE.writeMetadata());
        instructIds.add(OFInstructionIdsVer13.INSTANCE.meter());
        properties.add(factory.buildTableFeaturePropInstructions().setInstructionIds(instructIds).build());
        LinkedList<U8> tableIds = new LinkedList<>();
        tableIds.add(U8.of((short) 1)); //Tables that can be reached using goto table
        tableIds.add(U8.of((short) 2));
        tableIds.add(U8.of((short) 3));
        tableIds.add(U8.of((short) 4));
        properties.add(factory.buildTableFeaturePropNextTables().setNextTableIds(tableIds).build());
        LinkedList<OFActionId> actionIds = new LinkedList<>();
        actionIds.add(OFActionIdsVer13.INSTANCE.output()); //5.12 Actions
        actionIds.add(OFActionIdsVer13.INSTANCE.group());
        actionIds.add(OFActionIdsVer13.INSTANCE.setField());
        actionIds.add(OFActionIdsVer13.INSTANCE.setQueue());
        actionIds.add(OFActionIdsVer13.INSTANCE.pushVlan());
        actionIds.add(OFActionIdsVer13.INSTANCE.popVlan());
        actionIds.add(OFActionIdsVer13.INSTANCE.pushMpls());
        actionIds.add(OFActionIdsVer13.INSTANCE.popMpls());
        actionIds.add(OFActionIdsVer13.INSTANCE.setMplsTtl());
        actionIds.add(OFActionIdsVer13.INSTANCE.decMplsTtl());
        actionIds.add(OFActionIdsVer13.INSTANCE.setNwTtl());
        actionIds.add(OFActionIdsVer13.INSTANCE.decNwTtl());
        properties.add(factory.buildTableFeaturePropWriteActions().setActionIds(actionIds).build());
        properties.add(factory.buildTableFeaturePropApplyActions().setActionIds(actionIds).build());
        LinkedList<U32> oxmIds = new LinkedList<>();
        oxmIds.add(U32.of(factory.oxms().buildEthSrc().getTypeLen()));
        oxmIds.add(U32.of(factory.oxms().buildEthDst().getTypeLen()));
        oxmIds.add(U32.of(factory.oxms().buildEthType().getTypeLen()));
        oxmIds.add(U32.of(factory.oxms().buildIpv4Src().getTypeLen())); //oxm_ofb_match_fields
        oxmIds.add(U32.of(factory.oxms().buildIpv4Dst().getTypeLen()));
        oxmIds.add(U32.of(factory.oxms().buildIpProto().getTypeLen()));
        oxmIds.add(U32.of(factory.oxms().buildTcpSrc().getTypeLen()));
        oxmIds.add(U32.of(factory.oxms().buildTcpDst().getTypeLen()));
        oxmIds.add(U32.of(factory.oxms().buildUdpSrc().getTypeLen()));
        oxmIds.add(U32.of(factory.oxms().buildUdpDst().getTypeLen()));
        properties.add(factory.buildTableFeaturePropMatch().setOxmIds(oxmIds).build()); //OFTFPT_MATCH
        properties.add(factory.buildTableFeaturePropWildcards().setOxmIds(oxmIds).build()); //OFTFPT_WILDCARDS
        properties.add(factory.buildTableFeaturePropWriteSetfield().setOxmIds(oxmIds).build());
        properties.add(factory.buildTableFeaturePropApplySetfield().setOxmIds(oxmIds).build());
        tempEntries.add(factory.buildTableFeatures().setTableId(TableId.of(0)).setName("classifer")
                                .setMetadataMatch(U64.NO_MASK).setMetadataWrite(U64.NO_MASK)
                                .setMaxEntries(10000).setProperties(properties)
                                .build());

        LinkedList<OFTableFeatureProp> properties1 = new LinkedList<>();
        properties1.add(factory.buildTableFeaturePropInstructions().setInstructionIds(instructIds).build());
        LinkedList<U8> tableIds1 = new LinkedList<>();
        tableIds1.add(U8.of((short) 2));
        tableIds1.add(U8.of((short) 3));
        tableIds1.add(U8.of((short) 4));
        properties1.add(factory.buildTableFeaturePropNextTables().setNextTableIds(tableIds1).build());
        properties1.add(factory.buildTableFeaturePropWriteActions().setActionIds(actionIds).build());
        properties1.add(factory.buildTableFeaturePropWriteSetfield().setOxmIds(oxmIds).build());
        properties1.add(factory.buildTableFeaturePropApplyActions().setActionIds(actionIds).build());
        properties1.add(factory.buildTableFeaturePropMatch().setOxmIds(oxmIds).build()); //OFTFPT_MATCH
        properties1.add(factory.buildTableFeaturePropWildcards().setOxmIds(oxmIds).build()); //OFTFPT_WILDCARDS
        properties1.add(factory.buildTableFeaturePropWriteSetfield().setOxmIds(oxmIds).build());
        properties1.add(factory.buildTableFeaturePropApplySetfield().setOxmIds(oxmIds).build());
        tempEntries.add(factory.buildTableFeatures().setTableId(TableId.of(1)).setName("table1")
                                .setMetadataMatch(U64.NO_MASK).setMetadataWrite(U64.NO_MASK)
                                .setMaxEntries(10000)
                                .setProperties(properties1).build());

        LinkedList<OFTableFeatureProp> properties2 = new LinkedList<>();
        properties2.add(factory.buildTableFeaturePropInstructions().setInstructionIds(instructIds).build());
        LinkedList<U8> tableIds2 = new LinkedList<>();
        tableIds2.add(U8.of((short) 3));
        tableIds2.add(U8.of((short) 4));
        properties2.add(factory.buildTableFeaturePropNextTables().setNextTableIds(tableIds2).build());
        properties2.add(factory.buildTableFeaturePropWriteActions().setActionIds(actionIds).build());
        properties2.add(factory.buildTableFeaturePropWriteSetfield().setOxmIds(oxmIds).build());
        properties2.add(factory.buildTableFeaturePropApplyActions().setActionIds(actionIds).build());
        properties2.add(factory.buildTableFeaturePropMatch().setOxmIds(oxmIds).build()); //OFTFPT_MATCH
        properties2.add(factory.buildTableFeaturePropWildcards().setOxmIds(oxmIds).build()); //OFTFPT_WILDCARDS
        properties2.add(factory.buildTableFeaturePropWriteSetfield().setOxmIds(oxmIds).build());
        properties2.add(factory.buildTableFeaturePropApplySetfield().setOxmIds(oxmIds).build());
        tempEntries.add(factory.buildTableFeatures().setTableId(TableId.of(2)).setName("table2")
                                .setMetadataMatch(U64.NO_MASK).setMetadataWrite(U64.NO_MASK)
                                .setMaxEntries(10000)
                                .setProperties(properties2).build());

        LinkedList<OFTableFeatureProp> properties3 = new LinkedList<>();
        properties3.add(factory.buildTableFeaturePropInstructions().setInstructionIds(instructIds).build());
        LinkedList<U8> tableIds3 = new LinkedList<>();
        tableIds3.add(U8.of((short) 4));
        properties3.add(factory.buildTableFeaturePropNextTables().setNextTableIds(tableIds3).build());
        properties3.add(factory.buildTableFeaturePropWriteActions().setActionIds(actionIds).build());
        properties3.add(factory.buildTableFeaturePropWriteSetfield().setOxmIds(oxmIds).build());
        properties3.add(factory.buildTableFeaturePropApplyActions().setActionIds(actionIds).build());
        properties3.add(factory.buildTableFeaturePropMatch().setOxmIds(oxmIds).build()); //OFTFPT_MATCH
        properties3.add(factory.buildTableFeaturePropWildcards().setOxmIds(oxmIds).build()); //OFTFPT_WILDCARDS
        properties3.add(factory.buildTableFeaturePropWriteSetfield().setOxmIds(oxmIds).build());
        properties3.add(factory.buildTableFeaturePropApplySetfield().setOxmIds(oxmIds).build());
        tempEntries.add(factory.buildTableFeatures().setTableId(TableId.of(3)).setName("table3")
                                .setMetadataMatch(U64.NO_MASK).setMetadataWrite(U64.NO_MASK)
                                .setMaxEntries(10000)
                                .setProperties(properties3).build());

        this.entries = tempEntries;
    }

}
