package org.onosproject.snort;

import org.onosproject.core.ApplicationId;
import org.onosproject.core.GroupId;
import org.onosproject.net.Link;
import org.onosproject.net.Host;
import org.onosproject.net.Port;
import org.onosproject.net.PortNumber;
import org.onosproject.net.ConnectPoint;
import org.onosproject.net.Device;
import org.onosproject.net.DeviceId;
import org.onosproject.net.device.DeviceService;
import org.onosproject.net.device.DeviceListener;
import org.onosproject.net.device.DeviceEvent;
import org.onosproject.net.flow.TrafficTreatment;
import org.onosproject.net.flow.DefaultTrafficTreatment;
import org.onosproject.net.link.LinkService;
import org.onosproject.net.group.GroupService;
import org.onosproject.net.group.GroupBuckets;
import org.onosproject.net.group.GroupBucket;
import org.onosproject.net.group.DefaultGroupBucket;
import org.onosproject.net.group.GroupKey;
import org.onosproject.net.group.DefaultGroupKey;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.ArrayDeque;



public class SnortTunnel implements DeviceListener {

    private SnortManager manager;
    private ApplicationId appId;
    private DeviceService deviceService;
    private LinkService linkService;
    private GroupService groupService;
    private final Logger log = LoggerFactory.getLogger(SnortTunnel.class);
   
    private HashMap<String /*DeviceID*/, Port> snortPorts = new HashMap<>();
    private HashMap<DeviceId, Integer> snortHops = new HashMap<>();

    public SnortTunnel(ApplicationId a, DeviceService d, LinkService l, GroupService g) {
        appId = a;
        deviceService = d;
        linkService = l;
        groupService = g;
        deviceService.addListener(this);
    }

    @Override
    public void event(DeviceEvent deviceEvent) {
        if (deviceEvent.type() == DeviceEvent.Type.DEVICE_REMOVED) {
            Device device = (Device) deviceEvent.subject();
            removeSnort(device.id().toString());
        } else if (deviceEvent.type() == DeviceEvent.Type.PORT_REMOVED) {
            Device device = (Device) deviceEvent.subject();
            snortPorts.remove(device.id().toString(), deviceEvent.port());
        }
        if (deviceEvent.type() == DeviceEvent.Type.DEVICE_ADDED || deviceEvent.type() == DeviceEvent.Type.DEVICE_REMOVED || deviceEvent.type() == DeviceEvent.Type.PORT_REMOVED) {
            log.info("Updating Snort Tunnels");
            for (Device device: deviceService.getDevices()) {
                snortHops.put(device.id(), -1); //-1 for no Snort available.
            }
            for (String deviceString: snortPorts.keySet()) {
                setupSnortTunnel(DeviceId.deviceId(deviceString), snortPorts.get(deviceString));
            }
        }
    }
    
    public boolean addSnort(String deviceId, Port port) {
        snortPorts.put(deviceId, port);
        setupSnortTunnel(DeviceId.deviceId(deviceId), port);
        return true;
    }

    public boolean removeSnort(String deviceId) {
        snortPorts.remove(deviceId);
        return true;
    }

    public boolean clearSnort() {
        snortPorts.clear();
        return true;
    }

    private void setupSnortTunnel(DeviceId snortDeviceId, Port snortPort) {

        //Setup seenDevices and snortHops
        HashMap<DeviceId, Boolean> seenDevices = new HashMap<>();
        for (Device device: deviceService.getDevices()) {
            DeviceId deviceId = device.id();
            seenDevices.put(deviceId, false);
            if (!snortHops.containsKey(deviceId)) {
                snortHops.put(deviceId, -1); //-1 for no Snort available.
            }
        }

        snortHops.put(snortDeviceId, 0); //Snort is on this device.

        //Setup VLAN redirect to Snort on nearest device
        TrafficTreatment bucketTreatment = DefaultTrafficTreatment.builder().popVlan().setOutput(snortPort.number()).build();
        GroupBucket bucket = DefaultGroupBucket.createIndirectGroupBucket(bucketTreatment);
        ArrayList<GroupBucket> bucketList = new ArrayList<>();
        bucketList.add(bucket);
        GroupBuckets buckets = new GroupBuckets(bucketList);
        GroupKey groupKey = new DefaultGroupKey("SNORT".getBytes());
        groupService.setBucketsForGroup(snortDeviceId, groupKey, buckets, groupKey, appId);

        ArrayDeque<DeviceId> deviceLinksToLookAt = new ArrayDeque<>();
        deviceLinksToLookAt.add(snortDeviceId);
        //for each in queue -> only containing /\device so far.
        //while devices left in queue
        while(!deviceLinksToLookAt.isEmpty()) {
            DeviceId currentDeviceId = deviceLinksToLookAt.remove();
            for (Link link: linkService.getDeviceLinks(currentDeviceId)) {
                DeviceId destId = link.dst().deviceId();
                PortNumber destPort = link.dst().port();
                if (!destId.equals(currentDeviceId) && !seenDevices.get(destId)) { //If the device has not been seen
                    int newHops = snortHops.get(currentDeviceId) + 1;
                    int currentHops = snortHops.get(destId);
                    if (currentHops == -1 || currentHops > newHops) {
                        snortHops.put(destId, newHops);
                        //change group 500 bucket to point to snort
                        bucketTreatment = DefaultTrafficTreatment.builder().setOutput(destPort).build();
                        bucket = DefaultGroupBucket.createIndirectGroupBucket(bucketTreatment);
                        bucketList.clear();
                        bucketList.add(bucket);
                        buckets = new GroupBuckets(bucketList);
                        groupService.setBucketsForGroup(destId, groupKey, buckets, groupKey, appId);
                        deviceLinksToLookAt.add(destId); //add to device to queue
                    }
                    seenDevices.put(destId, true);
                }
            }
        }
    }

}
