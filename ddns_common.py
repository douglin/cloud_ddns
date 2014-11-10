#!/usr/bin/env python
import os   # miscellaneous operating system interfaces
import sys  # system paramteters
import re   # regular expression
import yaml
import netaddr
from netaddr import all_matching_cidrs

def get_nova_creds():
    d = {}
    d['username'] = os.environ['OS_USERNAME']
    d['api_key'] = os.environ['OS_PASSWORD']
    d['auth_url'] = os.environ['OS_AUTH_URL']
    d['project_id'] = os.environ['OS_TENANT_NAME']
    return d

class parms():

    def __init__(self, filename):
        try:
            f = open(filename, 'r')
        except:
            print "ERROR: opening %s" % filename
            sys.exit()
        try:
            self.dict = yaml.load(f)
        except:
            print "ERROR: loading parms from %s" % filename
            sys.exit()
	f.close()

    def add(self, key, value):
	self.dict[key] = value

    def value(self, key):
	return self.dict[key]

def valid_hostname(hostname):
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1] # strip exactly one dot from the right, if present
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))

def reverse_ip_address(ip_addr):
    quads = ip_addr.split('.',4)
    quads.reverse()
    reverse_ip_addr = ".".join(quads)

    return reverse_ip_addr

def reverse_dns_zone(ipv4_net):
    net = netaddr.IPNetwork(ipv4_net)
    rev_zone = netaddr.IPAddress(net.ip).reverse_dns

    if net.prefixlen % 8:
        print "ERROR: Zones need to be on octet boundaries, e.g. Class A, B or C"
        sys.exit()
    else:
        octets_to_remove = 4 - (net.prefixlen / 8)
        rev_zone_split = rev_zone.split('.', octets_to_remove)
        rev_zone = rev_zone_split[-1]
        rev_zone = rev_zone[:-1]  # strip trailing '.'
        return rev_zone

def file_suffix(net):
    return net.split('/',2)[0]

def get_ddns_key():
    try:
        f = open('Kcloud.ddns.filename', 'r')
    except:
        print ("Missing key file, run setup_ddns.sh")
        sys.exit()

    key_file = str(f.read())[:-1] + ".private"  # "[:-1] removes training end-of-line                        
    f.close()
    key_parms =parms(key_file)
    return key_parms.value('Key')
