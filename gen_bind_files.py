#!/usr/bin/env python
import os   # miscellaneous operating system interfaces
import sys  # system paramteters
import yaml # YAML
import netaddr
from ddns_common import parms
from ddns_common import file_suffix
from ddns_common import reverse_dns_zone
from ddns_common import get_ddns_key

class content():

    def __init__(self, filename):
        try:
            f = open(filename, 'r')
            self.text = f.read()
        except:
            print "ERROR: reading %s" % filename
        f.close()

    def replace_fields(self, mappings):
        self.text = self.text.format(**mappings.dict)

    def append(self, add_text):
        self.text += add_text

    def write(self, filename):
        try:
            f = open(filename, 'w')
            f.write(self.text)
        except:
            print "ERROR: writing to %s" % filename
        f.close()

def revzone_filename(net):
    return "reverse.cloudzone.%s" % file_suffix(net)

def main():

    # initialize mappings for the replacement fields in the templates
    mappings = parms('ddns_config.yaml')
    mappings.add('key_name', 'cloud.ddns')
    mappings.add('secret_key', get_ddns_key())

    # initialize content
    named = content('templates/template.named.conf')
    forward_zone = content('templates/template.forward.cloudzone')
    reverse_zone = {}
    for net in mappings.value('ip_ranges'):
        reverse_zone[net] = content('templates/template.reverse.cloudzone')
    resolvconf = content('templates/template.resolv.conf')

    # create content for {forward_ips} mapping in named.conf
    text = ""
    for ip in mappings.value('forwarders'):
        text += "%s; " % ip
    mappings.add('forward_ips', text)
        
    # create content for {reverse_zones} mapping in named.conf
    rz_fields = ""
    zone_template = content('templates/template.named.zone')
    rz_dict = {}
    rz_dict['key_name'] = mappings.value('key_name')
    for net in mappings.value('ip_ranges'):
	text = zone_template.text
        rz_dict['revzone'] = reverse_dns_zone(net)
        rz_dict['revzone_file'] = revzone_filename(net)
        rz_fields += "%s\n" % text.format(**rz_dict)
    mappings.add('reverse_zones', rz_fields)

    # swap replacement fields with mapped content and add reverse lookup for the DNS instance IPs
    named.replace_fields(mappings)
    forward_zone.replace_fields(mappings)
    for net in mappings.value('ip_ranges'):
        reverse_zone[net].replace_fields(mappings)

        # add reverse lookup for the DNS instance
        for ip in [mappings.value('dns_fixed_ip'), mappings.value('dns_floating_ip')]:
            if netaddr.IPAddress(ip) in netaddr.IPNetwork(net):
                text = "%s  IN  A  %s" % (mappings.value('dns_shortname'), ip)
                reverse_zone[net].append(text)
        
    resolvconf.replace_fields(mappings)

    # write content
    named.write('gen4bind/named.conf')
    forward_zone.write('gen4bind/forward.cloudzone')
    for net in mappings.value('ip_ranges'):
        filename = "gen4bind/%s" % revzone_filename(net)
        reverse_zone[net].write(filename)
    resolvconf.write('gen4bind/resolv.conf')

if __name__ == "__main__":
    main()
