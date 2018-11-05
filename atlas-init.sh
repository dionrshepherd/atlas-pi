#! /usr/bin/env bash
#  /etc/init.d/atlas-init

# Some things that run always
touch /var/lock/atlas-init.sh

# Carry out specific functions when asked to by the system
case "$1" in
    start)
        # bind sensor to usb
        echo '1-1.4' | sudo tee /sys/bus/usb/drivers/usb/bind

        # run the produce script
        # python3 /home/linaro/atlas-pi/pi_produce.py
        ;;
    stop)
        # kill any running python scripts
        pkill -9 -f pi_produce.py

        # unbind sensor from usb
         echo '1-1.4' | sudo tee /sys/bus/usb/drivers/usb/unbind
        ;;
    *)
        echo "Usage: /etc/init.d/atlas-init.sh {start|stop}"
        exit 1
        ;;
esac

exit 0