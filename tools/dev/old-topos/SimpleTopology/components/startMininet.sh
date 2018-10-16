#if [ "$1" != "NORMAL" ] && [ "$1" != "MERVYN" ]; then
#	echo "Usage startMininet [NORMAL | MERVYN]"
#	exit 1
#fi

#echo ***Resetting Virtual Interfaces
#ip link delete veth0 type veth peer name veth1

#if [ "$1" = "MERVYN" ]; then
#	echo ***Adding Virtual Interfaces
#	ip link add veth0 type veth peer name veth1
#	ifconfig veth0 up
#	ifconfig veth1 up
#	ifconfig veth0 192.168.100.1
#fi

#echo ***Waiting to start Mininet
#echo "Has ONOS started?"
#select yn in "Yes" "No"; do
#    case $yn in
#        Yes ) break;;
#        No ) exit;;
#    esac
#done

echo ***Starting Mininet
python mininetTopo_A.py $1
sleep 10

