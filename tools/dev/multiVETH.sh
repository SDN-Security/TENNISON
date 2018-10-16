int1="veth${1}"
int2="veth${2}"
int1addr="192.168.${3}.1"

echo ***Resetting Virtual Interfaces
ip link delete $int1 type veth peer name $int2

echo ***Adding Virtual Interfaces
ip link add $int1 type veth peer name $int2
ifconfig $int1 up
ifconfig $int2 up
ifconfig $int1 $int1addr
