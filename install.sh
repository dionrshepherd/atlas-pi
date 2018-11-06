#!/usr/bin/env bash
set -e

# username password and hostname
echo "Has the user password, root password and hostname been changed (y/n)"
read -p '>' install

if [ "$install" = "y" ]; then
    echo "Have the packages been installed (y/n)"
    read -p '>' update

    if [ "$update" = "n" ]; then
        # install all libraries needed
        echo "update packages"
        sudo apt update
        echo "install pip3 and screen"
        sudo apt -y install python3-pip screen
        echo "install needed python packages"
        pip3 install setuptools
        pip3 install awscli==1.11.18
        pip3 install boto3
        pip3 install pyserial

        # copy bash script to root
        cp .bashrc ../

    fi
    # copy python script to sbin
    echo "copy clear script"
    cp /home/linaro/atlas-pi/clear.py /usr/local/sbin/
    echo "copy produce script"
    cp /home/linaro/atlas-pi/pi_produce.py /usr/local/sbin/

    # copy the init script to /etc/init.d and add to default start-up scripts
    echo "copy init file"
    cp /home/linaro/atlas-pi/atlas-init.sh /etc/init.d/
    echo "chmod file"
    sudo chmod 755 /etc/init.d/atlas-init.sh
    #echo "chown file"
    #sudo chown root:root /etc/init.d/atlas-init.sh
    echo "add to defaults"
    sudo update-rc.d atlas-init.sh defaults

    # configure the aws creds
    echo "run: aws configure"

    # reboot to set everything running
    echo "lastly reboot"
else
    exit
fi
