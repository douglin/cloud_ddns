cloud_ddns
==========

Setup a custom dynamic DNS for instances in an OpenStack cloud

==========

USER GUIDE

Part 1. Build a Dynamic DNS Instance

1. Pre-Requisites for the DNS Instance
    1.	Deploy an Centos/RHEL 6.5 instance for the DNS. It should be sufficient to choose a smaller flavor like “n1.small”.
    2.	Add a Floating IP
    3.	Setup security group rules for the DNS instance. The following ports should be open: TCP 22 (SSH), TCP 53 and UDP 53 (for DNS). 
    4.	If the iptables service is on, it may be easiest to turn it off or to open the ports required for the DNS 
    5.	Ensure that the OpenStack CLI clients are installed 
    6.	Ensure that BIND is installed

2. Install BIND
Install the bind and bind-utils packages if they have not already been installed. Note that bind sets up the DNS server and bind-utils has the nsupdate tools.

  [centos@ddns ~]$ sudo yum update -y
  [centos@ddns ~]$ sudo yum install -y bind bind-utils

3. Get the Cloud Admin’s OpenStack API Credentials, e.g. openrc.sh
Using the Admin’s credentials will allow the “DDNS “ scripts to see instances across projects. If openrc.sh prompts for a password, remove the prompt and add the password in the file. Including the password will be required for the scripts to run automatically. Below is an example of how to test the openrc.sh file using the OpenStack CLI.

  [centos@ddns ~]$ source openrc.sh 
  [centos@ddns ~]$ nova list

4. Generate DNSSEC Key
Create a DNSSEC Key which will be used to restrict DNS updates (to a script called ddns.sh). This key file and “key name” will be parameters used in the step 4 – “setup ddns_config.yaml”.  Note that DNS Security Extensions (DNSSEC) is a specification which aims at maintaining the data integrity of DNS responses. DNSSEC signs all the DNS resource records (A, MX, CNAME etc.) of a zone using PKI (Public Key Infrastructure).

  [centos@ddns ~]$ dnssec-keygen -r /dev/urandom -a HMAC-MD5 -b 512 -n HOST <key name>

5. Unzip the DDNS scripts
For example,
  [centos@ddns ~]$ unzip /tmp/ddns.zip

6. Setup ddns_config.yaml
  “ddns_config.yaml” has all of the configuration parameters that will be used to configure BIND and the “DDNS” scripts. Edit this file and input customized information. Then save the file.  It is important to make sure there are no errors, like no over lapping IP ranges in this file. Here is a sample listing of the file. 

domain_name: cloud.myuniverse.org
dns_shortname: bigbang
dns_fixed_ip: 10.130.52.121
dns_floating_ip: 10.130.56.248
forwarders:
  - 10.130.0.1
key_name: cloud.myuniverse.com
key_file: Kcloud.myuniverse.com.+157+41426.private
ip_ranges:
  - 10.130.52.0/24
  - 10.130.56.0/24

6. Run setup_ddns.sh to complete the DNS setup
setup_ddns.sh creates configuration files for the DNS updates as well as configuration files for BIND. It then moves the BIND files to the appropriate directories and restart the DNS (“named”) service.  Feel free to view the script to see what it does. Run this script using “sudo”. 

  [centos@ddns ~]$ sudo ./setup_ddns.sh

7. Run ddns.sh to complete the setup of the Dynamic DNS
Now the main executable script, ddns.sh, has been created. It will use the OpenStack APIs to query instances and then update the DNS appropriately. 

  [centos@zdns ~]$ ./ddns.sh

8. Add ddnn.sh to cron to update the DNS automatically
The following example will update cron to call ddns.sh every minute.

  [centos@ddns ~]$ crontab –e  

Once in the file, add  “* * * * * <path-to-script>”. For example:

  * * * * * /home/centos/ddns.sh

To monitor if the cron is working monitor /var/log/messages with:
  “tail –f /var/log/messages”

8. Test the DNS server
Use ping and dig or nslookup to test the name server. 


Part 2. Connecting Instances to the DNS
An instance needs to be configured to resolve using the new DNS. The easiest way to do this is to configure the image(s). In the image, change /etc/resolv.conf and /etc/sysconfig/network-scripts/ifcfg-eth0 as described below. These changes can also be done for an individual instance. 

1. Edit /etc/resolv.conf
  First, change resolv.conf as follows. The “nameserver_ip” can be either the fixed or floating IP of the DNS instance.
  search <domain_name>
  nameserver <nameserver_ip>

For example:
  search cloud.mycompany.com
  nameserver 10.130.52.121

2. Add PEERDNS=”no” to /etc/sysconfig/network-scripts/ifcfg-eth0
Add a line, PERRDNS=”no”, to ifcfg-eth0.  For example, type:

  echo "PEERDNS=no" >> /etc/sysconfig/network-scripts/ifcfg-eth0


