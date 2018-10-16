PIGRELAY=$1

ifconfig veth1 192.168.100.2
cd $PIGRELAY

python pigrelay.py
