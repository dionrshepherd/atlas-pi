#! /usr/bin/env bash
#  /etc/init.d/atlas-init

# Some things that run always
touch /var/lock/atlas-init.sh

# Carry out specific functions when asked to by the system
case "$1" in
    start)
        # bind sensor to usb
        echo '1-1' | sudo tee /sys/bus/usb/drivers/usb/bind

        # run the produce script
        /usr/bin/python3 /home/linaro/atlas-pi/pi_produce.py

        touch /home/linaro/start.txt
        ;;
    stop)
        # kill any running python scripts
        pkill -9 -f pi_produce.py

        # unbind sensor from usb
        echo '1-1' | sudo tee /sys/bus/usb/drivers/usb/unbind

        touch /home/linaro/stop.txt
        ;;
    *)
        echo "Usage: /etc/init.d/atlas-init.sh {start|stop}"
        exit 1
        ;;
esac

exit 0