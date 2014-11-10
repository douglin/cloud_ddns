#!/usr/bin/env python
import os   # miscellaneous operating system interfaces
import sys  # system paramteters
import yaml # YAML
import netaddr # network address and manipulation libary
try:
    import cPickle as pickle  # python object serialization
except:
    import pickle
from netaddr import all_matching_cidrs
import novaclient.v1_1.client as novaclient
from ddns_common import get_nova_creds
from ddns_common import valid_hostname
from ddns_common import reverse_dns_zone
from ddns_common import file_suffix
from ddns_common import parms

ns_send_frequency = 25   # arbitrary number of updates before issuing a nsupdate "send"

class content():

    def __init__ (self, text):
        self._text = text
        self._update_count = 0

    def append(self, add_text):
        self._text += add_text
        self._update_count += 1
        if (self._update_count % ns_send_frequency) == 0:
            self._text += "show\nsend\n"

    def write(self, filename):
        self._text += "show\nsend\n"
        try:
            f = open(filename, 'w')
            f.write(self._text)
            f.close()
        except:
            print "ERROR: can not write to file %s", filename
        
def get_reverse_net_dns(ip, ip_ranges):
    rev_cidr = all_matching_cidrs(ip, ip_ranges)
    if len(rev_cidr) > 1:
        print "ERROR: overlapping CIDRs"
        sys.exit()
    rev_net = str(rev_cidr[0])
    rev_dns = netaddr.IPAddress(ip).reverse_dns
    return rev_net, rev_dns

def main():
    # Authenticate Credentials
    try:
        creds = get_nova_creds()
    except:
        print 'Please set OpenStack credentials, e.g. type source openrc.sh, and try again'
        sys.exit()

    # Retrieve the Nova client
    nova = novaclient.Client(**creds)

    # get template/dictionary variables
    mappings = parms('ddns_config.yaml')
    domain_name = mappings.value('domain_name')
    dns_name = mappings.value('dns_shortname') + "." + domain_name

    # initialize content for forward and reverse nsupdate files
    content_A_rec = content("server " + dns_name + "\n")

    content_PTR = {} 
    for net in mappings.value('ip_ranges'):
        revzone = reverse_dns_zone(net)
        text = "server %s\n" % dns_name
        text += "zone %s\n" % revzone
        content_PTR[net] = content(text)

    # create a current list of servers and IPs that are valid for DNS updates
    curr_servers = {}
    for server in nova.servers.list(search_opts={'all_tenants': 1}):

        if server.status != 'ACTIVE':
            print "INFO: Server name %s has state %s" % (server.name, server.status)
        elif server.name in curr_servers.keys():  # keys refers to the server names
            print "WARNING: Server name %s is a duplicate" % server.name
        elif not valid_hostname(server.name):
            print "WARNING: Server name %s is not a valid hostname" % server.name
        else:
            curr_servers[server.name] = server.networks.values()

    # load the previous server list from a file
    if os.path.isfile('ddns_instance_state.pckl'):
        f = open('ddns_instance_state.pckl')
        prev_servers = pickle.load(f)
        f.close()
    else:
        prev_servers = []

    # delete servers in the previous list but not in the current list
    for server_name in prev_servers:
        if not server_name in curr_servers:

            # get saved ip_address
            ip_addresses = prev_servers[server_name]

            # create long hostname
            server_name += '.' + domain_name

            # update forward zone content
            content_A_rec.append(
                "update delete " + server_name + " A\n") 

            # update reverse zone content
            for ip in ip_addresses[0]:
                rev_net, rev_dns = get_reverse_net_dns(ip, mappings.value('ip_ranges'))
                content_PTR[rev_net].append(
                    "update delete " + rev_dns + " 600 IN PTR " + server_name + ".\n")

    # add servers in the current list that are not in the previous list
    for server_name in curr_servers:
        if not server_name in prev_servers:

            # get the ip addresses, assume there is only one network, e.g. "nebula"
            ip_addresses = curr_servers[server_name]

            # create long hostname
            server_name += "." + domain_name 

            # update forward zone content with address of the last ip address
            forward_ip = ip_addresses[0][-1]
            content_A_rec.append(
                "update add " + server_name + " 600 A " + forward_ip + "\n")
 
            # update reverse zone content
            for ip in ip_addresses[0]:
                rev_net, rev_dns = get_reverse_net_dns(ip, mappings.value('ip_ranges'))
                content_PTR[rev_net].append(
                    "update add " + rev_dns + " 600 IN PTR " + server_name + ".\n")

    # write content
    content_A_rec.write('A_records')
    for net in mappings.value('ip_ranges'):
        filename = "PTR_%s" % file_suffix(net)
        content_PTR[net].write(filename)

    # dump current server list to a file
    f = open('ddns_instance_state.pckl', 'w')
    pickle.dump(curr_servers, f)
    f.close()

if __name__ == "__main__":
    main()
