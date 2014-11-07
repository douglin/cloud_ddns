#!/usr/bin/env python
import os   # miscellaneous operating system interfaces
import sys  # system paramteters
import yaml # YAML
import netaddr
from netaddr import all_matching_cidrs
import novaclient.v1_1.client as novaclient
from ddns_common import get_nova_creds
from ddns_common import valid_hostname
from ddns_common import reverse_dns_zone
from ddns_common import file_suffix
from ddns_common import parms

ns_send_frequency = 25   # arbitrary number of updates before issuing a nsupdate "send"

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
    update_count = {}
    content_A_Records = "server %s\n" % dns_name
    update_count['A_Records'] = 0

    content_PTR = {} 
    for net in mappings.value('ip_ranges'):
        revzone = reverse_dns_zone(net)
        text = "server %s\n" % dns_name
        text += "zone %s\n" % revzone
        content_PTR[net] = text
        update_count[net] = 0

    server_list = [] # used to check for duplidate server names
    # update nspdate files for each existing server
    for server in nova.servers.list(search_opts={'all_tenants': 1}):

        if server.status != 'ACTIVE':
            print "INFO: Server name %s has state %s" % (server.name, server.status)
        elif server.name in server_list:
            print "WARNING: Server name %s is a duplicate" % server.name
        elif not valid_hostname(server.name):
            print "WARNING: Server name %s is not a valid hostname" % server.name
        else:
            server_list.append(server.name)
            server_name = server.name + "." + domain_name 

            # get the ip addresses, assume there is only one network, e.g. "nebula"
            ip_addresses = server.networks.values()
     
            # update forward zone content
            forward_ip = ip_addresses[0][-1]
            content_A_Records += "update delete %s A\n" % server_name  
            content_A_Records += "update add %s 600 A %s\n" % (server_name, forward_ip)
            if (update_count['A_Records'] % ns_send_frequency) == 0:
                content_A_Records += "show\nsend\n"
            update_count['A_Records'] += 1
 
            # update reverse zone content
            for ip in ip_addresses[0]:

                # find matching CIDR
                rev_cidr = all_matching_cidrs(ip, mappings.value('ip_ranges'))
                if len(rev_cidr) > 1:
                    print "ERROR: overlapping CIDRs"
                    sys.exit()
		rev_net = str(rev_cidr[0])
                rev_dns = netaddr.IPAddress(ip).reverse_dns

                content_PTR[rev_net] += "update add %s 600 IN PTR %s.\n" % (rev_dns, server_name)
                if (update_count[net] % ns_send_frequency) == 0:
                    content_PTR[rev_net] += "show\nsend\n"
                update_count[net] += 1

    # finish content
    content_A_Records += "show\nsend\n"
    for net in mappings.value('ip_ranges'):
        content_PTR[net] += "show\nsend\n"
   
    # write "A_records"
    f = open('A_records', 'w')
    f.write(content_A_Records)
    f.close()

    # write PTR records
    for net in mappings.value('ip_ranges'):
        filename = "PTR_%s" % file_suffix(net)
        f = open(filename, 'w')
        f.write(content_PTR[net])
        f.close()

if __name__ == "__main__":
    main()
