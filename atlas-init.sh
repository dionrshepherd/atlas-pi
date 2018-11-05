#! /bin/sh
# /etc/init.d/atlas-init.sh
### BEGIN INIT INFO
# Provides:          pitracker
# Required-Start:    $all
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Track pi.
# Description:       This service is used to track a pi.
### END INIT INFO

# Some things that run always
touch /var/lock/atlas-init.sh

# Carry out specific functions when asked to by the system
case "$1" in
    start)
        # bind sensor to usb
        echo '1-1' | sudo tee /sys/bus/usb/drivers/usb/bind

        # run the produce script
        /usr/bin/python3 /usr/local/sbin/pi_produce.py &
        ;;
    stop)
        # kill any running python scripts
        pkill -9 -f pi_produce.py

        # unbind sensor from usb
        echo '1-1' | sudo tee /sys/bus/usb/drivers/usb/unbind
        ;;
    *)
        echo "Usage: /etc/init.d/atlas-init.sh {start|stop}"
        exit 1
        ;;
esac

exit 0