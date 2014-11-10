#!/bin/sh
source ./openrc.sh -e
python ddns.py
nsupdate -y {key_name}:{secret_key} -v A_records
nsupdate -y {key_name}:{secret_key} -v PTR_fixed
nsupdate -y {key_name}:{secret_key} -v PTR_float
rm A_records PTR_f*
