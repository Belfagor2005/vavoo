#!/bin/sh
if [ ! -f /etc/resolv-backup.conf ] 
then
grep "nameserver.*" /etc/resolv.conf >> //etc/resolv-backup.conf
fi
> /etc/resolv.conf
rm -f /etc/resolv.conf
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 8.8.4.4" >> /etc/resolv.conf; 
echo ""
echo "* NETWORK RESTARTED*"
echo "* GOOGLE DNS APPEND TO NAMESERVER *"
echo "> done
> your device will restart now please wait..."; 

# sleep 3s; killall -9 enigma2
exit 0


