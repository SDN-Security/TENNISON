ONOS_SERVICE=/tmp
MERVYN_CONTROL=~/MervynONOS/mervyn
MERVYN_APPS=~/MervynONOS/onos-mervyn-apps
PIGRELAY=~/MervynONOS/pigrelay

SETUP=false
CLEAN=false

#ONOS is run locally to make it easier to use and debugable (port 5005).

if [ $(id -u) == 0 ]
  then echo "Please run this in non-sudo bash"
  exit
fi

MYDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $MYDIR/components

echo "Pick an option:"
select opt in "Setup" "Start All" "Start ONOS + Install Apps" "Reinstall Apps Only" "Start Mininet + Pigrelay" "Start Mervyn" "Cleanup" "Exit"; do
    case $opt in
        "Setup" ) SETUP=true; break;;
        "Start All" ) break;;
        "Start ONOS + Install Apps" ) gnome-terminal -e "bash startOnos.sh '$ONOS_SERVICE' '$MERVYN_APPS'"; exit;;
        "Reinstall Apps Only" ) gnome-terminal -e "bash startOnos.sh '$ONOS_SERVICE' '$MERVYN_APPS' true"; exit;;
        "Start Mininet + Pigrelay" ) sudo gnome-terminal -e "bash startMininet.sh '$PIGRELAY'"; exit;;
        "Start Mervyn" ) sudo bash startMervyn.sh "$MERVYN_CONTROL"; exit;;
        "Cleanup" ) CLEAN=true; break;;
        "Exit" ) exit;;
    esac
done

if [ "$CLEAN" == true ]
    then
    echo ***Stopping Mervyn
    sudo pkill -f -x "python3 mervyn.py"
    echo ***Stopping MongoDB
    sudo pkill -f -x "sudo mongod --quiet"
    sudo service mongodb stop
    echo ***Stopping Pigrelay
    sudo pkill -f -x "python pigrelay.py"
    echo ***Stopping Snort
    sudo pkill -x "snort -i"
    echo ***Stopping Mininet
    sudo pkill -f -x "bash startMininet.sh $PIGRELAY"
    echo ***Stopping ONOS
    sudo pkill -f -x "sudo -E bash -c bash onos-service debug"
    echo ***Removing ONOS package
    cd $ONOS_SERVICE
    sudo rm -rf onos
    echo ***Cleaning ONOS + Mininet
    sudo mn -c
    echo ***Resetting configs
    mv -vf $MERVYN_CONTROL/examples/oldconfig.yaml $MERVYN_CONTROL/examples/config.yaml
    mv -vf $MERVYN_CONTROL/examples/oldthresholds.yaml $MERVYN_CONTROL/examples/thresholds.yaml
    mv -vf $PIGRELAY/examples/oldconfig.yaml $PIGRELAY/examples/config.yaml
    cd $ONOS_ROOT/tools/test/bin
    bash onos-cell $ONOS_CELL
    exit
fi

if [ "$SETUP" == true ] 
    then
    #Only running one ONOS controller so we can run on loopback
    export OCI=127.0.0.1
    export OC1=127.0.0.1
    export OCN=127.0.0.1
    export ONOS_APPS=drivers,openflow,fwd,proxyarp,mobility
    export ONOS_NIC=10.0.0.*
    echo ***Making ONOS package
    bash $ONOS_ROOT/tools/build/onos-package
    echo ***Unpacking to $ONOS_SERVICE/onos
    cd $ONOS_SERVICE
    sudo rm -rf onos
    sudo tar -zxvf onos-*.*.*.$(id -un).tar.gz
    sudo mv onos-1.*.*.$(id -un) onos
    sudo chmod -R 777 $ONOS_SERVICE/onos
    echo ***Renaming old configs
    mv -vn $MERVYN_CONTROL/examples/config.yaml $MERVYN_CONTROL/examples/oldconfig.yaml
    mv -vn $MERVYN_CONTROL/examples/thresholds.yaml $MERVYN_CONTROL/examples/oldthresholds.yaml
    mv -vn $PIGRELAY/examples/config.yaml $PIGRELAY/examples/oldconfig.yaml
    echo ***Adding our configs
    cp -vn $MYDIR/config/mervyn/config.yaml $MERVYN_CONTROL/examples/config.yaml
    cp -vn $MYDIR/config/mervyn/thresholds.yaml $MERVYN_CONTROL/examples/thresholds.yaml
    cp -vn $MYDIR/config/pigrelay/config.yaml $PIGRELAY/examples/config.yaml
    #These are to stop ONOS from constantly generating warnings when debugging
    echo ***Fixing Karaf config bug
    cp -fv $MYDIR/config/org.apache.karaf.management.cfg $ONOS_SERVICE/onos/apache-karaf-*/etc
    echo ***Fixing README bug
    cd $ONOS_SERVICE/onos/apache-karaf-*/deploy
    sudo rm -fv README
    echo ***Fixing ONOS config bug
    CDEF_FILE=/tmp/$ONOS_USER@$OC1.cluster.json
    cd $ONOS_ROOT/tools/test/bin
    onos-gen-partitions $CDEF_FILE
    cp -fr $ONOS_ROOT/tools/package/config $ONOS_SERVICE/onos
    cp -fv $CDEF_FILE $ONOS_SERVICE/onos/config/cluster.json
    echo "Would you like to Start All or Exit?"
    select opt in "Start All" "Exit"; do
        case $opt in
        "Start All" ) break;;
        "Exit" ) exit;;
        esac
    done
fi

echo ***Cleaning ONOS + Mininet
sudo mn -c
echo ***Starting ONOS
cd $MYDIR/components
gnome-terminal -e "bash startOnos.sh '$ONOS_SERVICE' '$MERVYN_APPS'" 
echo ***Starting Mininet
sudo gnome-terminal -e "bash startMininet.sh '$PIGRELAY'"
sudo bash startMervyn.sh "$MERVYN_CONTROL"
