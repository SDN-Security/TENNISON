ONOS_SERVICE=$1
MERVYN_APPS=$2
ONLY_APPS=$3

BUILD_APPS=true

if [ $(id -u) == 0 ]
  then echo "Please run this in non-sudo bash"
  exit
fi

if [ "$ONLY_APPS" != true ]
    then
    echo ***Starting ONOS
    cd $ONOS_SERVICE/onos/bin
    gnome-terminal -e "sudo -E bash -c 'bash onos-service debug'"
fi

echo ***Waiting to Build/Install Apps
echo "Has ONOS started?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) break;;
        No ) exit;;
    esac
done

if [ "$BUILD_APPS" == true ]
    then
    echo ***Building ONOS-Mervyn Apps at $MERVYN_APPS
    cd $MERVYN_APPS
    mvn clean install
    sleep 5
fi

echo ***Installing ONOS-Mervyn Apps
cd $ONOS_ROOT/tools/dev/bin

bash onos-app $OC1 deactivate org.onosproject.flowmonitor 
bash onos-app $OC1 deactivate org.onosproject.ipfix 
bash onos-app $OC1 deactivate org.onosproject.snort 
bash onos-app $OC1 deactivate org.onosproject.mervynapi  

bash onos-app $OC1 reinstall $MERVYN_APPS/ipfix/target/onos-app-ipfix-*-SNAPSHOT.oar 
bash onos-app $OC1 activate org.onosproject.ipfix
sleep 2

bash onos-app $OC1 reinstall $MERVYN_APPS/snort/target/onos-app-snort-*-SNAPSHOT.oar 
bash onos-app $OC1 activate org.onosproject.snort 
sleep 2

bash onos-app $OC1 reinstall $MERVYN_APPS/flowmonitor/target/onos-app-flowmonitor-*-SNAPSHOT.oar 
bash onos-app $OC1 activate org.onosproject.flowmonitor
sleep 2

bash onos-app $OC1 reinstall $MERVYN_APPS/mervynapi/target/onos-app-mervynapi-*-SNAPSHOT.oar
bash onos-app $OC1 activate org.onosproject.mervynapi
sleep 2
