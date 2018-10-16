echo ***Resetting Virtual Interfaces
ip link delete veth0 type veth peer name veth1

echo ***Adding Virtual Interfaces
ip link add veth0 type veth peer name veth1
ifconfig veth0 up
ifconfig veth1 up
ifconfig veth0 192.168.100.1
