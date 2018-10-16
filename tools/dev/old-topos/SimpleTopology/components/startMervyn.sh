MERVYN_CONTROL=$1

if [ $(id -u) -ne 0 ]
  then echo "Please run this in sudo bash"
  exit
fi

echo ***Starting MongoDB
service mongodb stop
gnome-terminal -e "sudo mongod --quiet"
echo ***Waiting to start the Mervyn controller
echo "Has Mininet + Pigrelay started and are the ONOS-Mervyn Apps installed?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) break;;
        No ) exit;;
    esac
done
echo ***Starting Mervyn from $MERVYN_CONTROL
cd $MERVYN_CONTROL
python3 mervyn.py
