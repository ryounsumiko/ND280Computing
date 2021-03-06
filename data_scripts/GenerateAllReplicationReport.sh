#!/bin/bash

cd /home/ppd/stewartt/T2K/GRID/nd280Computing/data_scripts
source cronGRID.sh

std_out=$ND280TRANSFERS/replication.ALL.$(date +%H).out
std_err=$ND280TRANSFERS/replication.ALL.$(date +%H).err

nohup ./GenerateReplicationReport.py -s ALL \
-l lfn:/grid/t2k.org/nd280/raw/ND280/ND280/ \
</dev/null >$std_out 2>$std_err &
