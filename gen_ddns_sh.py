#!/usr/bin/env python
import os   # miscellaneous operating system interfaces
import sys  # system paramteters
from ddns_common import parms
from ddns_common import file_suffix
from ddns_common import get_ddns_key

# initialize template/dictionary variables
mappings = parms('ddns_config.yaml')
key_name = 'cloud.ddns'
key_value = get_ddns_key()

text = "#!/bin/sh\n"
text +=  "source ./openrc.sh\n"
text += "python ddns.py\n"
text += "nsupdate -y %s:%s -v %s\n" % (key_name, key_value, 'A_records')
for net in mappings.value('ip_ranges'):
    filename = "PTR_%s" % file_suffix(net)
    text += "nsupdate -y %s:%s -v %s\n" % (key_name, key_value, filename)
text += "rm A_records PTR_*"

f = open('ddns.sh', 'w')
f.write(text)
f.close()
