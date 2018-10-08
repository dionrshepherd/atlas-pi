#!/usr/bin/env bash
set -e

# username password and hostname
echo "Has the user password and hostname been changed"
# TODO: yes/no prompt here

# install all libraries needed
sudo apt install python3-pip file-rc
pip3 install setuptools
pip3 install awscli==1.11.18
pip3 install boto3
pip3 install pyserial

# copy bash script to root
cp .bashrc ../

# copy the init script to /etc/init.d and add to default start-up scripts
# cp atlas-init.sh /etc/init.d/
# sudo chmod 755 /etc/init.d/atlas-init.sh
# sudo chown root:root /etc/init.d/atlas-init.sh
# sudo update-rc.d atlas-init.sh defaults

# configure the aws creds
echo "run: ./.local/bin/aws configure"

# reboot to set everything running
echo "lastly reboot"