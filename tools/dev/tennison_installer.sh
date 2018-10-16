#INCOMPLETE. PLEASE ONLY USE AS GUIDE
sudo apt-get install python -y
sudo apt-get install python3 -y
sudo apt-get install python3-pip -y
sudo apt-get install python-pip -y
sudo add-apt-repository ppa:openjdk-r/ppa
sudo apt-get update
sudo apt-get install openjdk-8-jdk -y
sudo apt install -y gcc libpcre3-dev zlib1g-dev libpcap-dev openssl libssl-dev libnghttp2-dev libdumbnet-dev bison flex libdnet


#Download requirements first

pip3 install -r pip3.3requirements.txt
pip install -r pip2.7requirements.txt

git clone git://github.com/mininet/mininet
sudo util/install.sh -a

git clone git@d31-git.lancaster.ac.uk:tennison/topology.git
git clone git@d31-git.lancaster.ac.uk:tennison/onos.git
git clone git@d31-git.lancaster.ac.uk:tennison/coordinator.git
git clone git@d31-git.lancaster.ac.uk:tennison/onos-tennison-apps.git
git clone git@d31-git.lancaster.ac.uk:tennison/pig-relay.git


#TODO Install snort


#Source bash profile and put it into bash.rc

#Build onos apps.


#Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

sudo apt-get update

apt-cache policy docker-ce

sudo apt-get install -y docker-ce


docker network create --internal --subnet 10.1.1.0/24 no-internet

#Run mongo
docker run --network=no-internet --name some-mongo -d mongo

#install npm
curl -sL https://deb.nodesource.com/setup_4.x | sudo -E bash -
sudo apt-get install -y nodejs

#install bower
cd /home/username/coordinator/apps/gui/
bower install


#https://support.purevpn.com/how-to-disable-ipv6-linuxubuntu DISABLE IPv6!!

