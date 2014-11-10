#!/bin/sh -e
#
# Auto-generated BIND files will temporarily be put here
if [ ! -d "gen4bind" ]; then
  mkdir gen4bind
fi	
#
# Generate a secure key that will be used by the DNS
if [ ! -f Kcloud.ddns.filename ]; then
  dnssec-keygen -r /dev/urandom -a HMAC-MD5 -b 512 -n HOST cloud.ddns > Kcloud.ddns.filename
fi
#
# create bind server zone files and resolv.conf
python gen_bind_files.py
#
# create ddns.sh
python gen_ddns_sh.py
chmod +x ddns.sh
#
# copy generated files to the right directories
cp /etc/named.conf /etc/named.conf.ori
mv gen4bind/named.conf /etc/named.conf
mv gen4bind/forward.cloudzone /var/named
mv gen4bind/reverse.cloudzone.* /var/named
cp /etc/resolv.conf /etc/resolv.conf.ori
mv gen4bind/resolv.conf /etc/resolv.conf
#
# change permissions on /var/named
chmod -R 775 /var/named
#
# restart DNS
service named restart
#
# edit ifcfg-eth0 to prevent resolv.conf from being overwritten
echo "PEERDNS=no" >> /etc/sysconfig/network-scripts/ifcfg-eth0
