#! /usr/bin/env bash
#  /etc/init.d/atlas-init

# Some things that run always
touch /var/lock/atlas-init.sh

# Carry out specific functions when asked to by the system
case "$1" in
  start)
    echo "Start reading distances"
    python3 /home/linaro/atlas-pi/pi_produce.py
    ;;
  stop)
    echo "Stop all running python scripts"
    pkill -9 -f pi_produce.py
    # fuser -k /dev/ttyUSB9
    ;;
  *)
    echo "Usage: /etc/init.d/atlas-init.sh {start|stop}"
    exit 1
    ;;
esac

exit 0