#!/usr/bin/env bash
set -e

# username password and hostname
echo "Has the user password, root password and hostname been changed"
# TODO: yes/no prompt here

# install all libraries needed
sudo apt update
sudo apt -y install python3-pip
pip3 install setuptools
pip3 install awscli==1.11.18
pip3 install boto3
pip3 install pyserial

# copy bash script to root
cp .bashrc ../

# copy the init script to /etc/init.d and add to default start-up scripts
#echo "copy init file"
#cp atlas-init.sh /etc/init.d/
#echo "chmod file"
#sudo chmod 755 /etc/init.d/atlas-init.sh
#echo "chown flie"
#sudo chown root:root /etc/init.d/atlas-init.sh
#echo "add to defaults"
#sudo update-rc.d atlas-init.sh defaults

# configure the aws creds
echo "run: ./.local/bin/aws configure"

# reboot to set everything running
echo "lastly reboot"