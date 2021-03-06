#!/usr/bin/env python

"""
A script to synchronise two directories, directory A is an LFC directory and
directory B is an SRM directory. SRM-SRM synchronisation is not supported.

-f flag states whether the user wants to use FTS rather than standard lcg-utils
which is the default

Example
     ./SyncDirs.py
     -a lfn:/grid/t2k.org/nd280/raw/ND280/ND280/00006000_00006999/
     -b srm://t2ksrm.nd280.org//nd280data/raw/ND280/ND280/00006000_00006999/
     -f 1

This synchronises the lfc directory with that on the TRIUMF SE and uses FTS to
transfer the files.

"""

from ND280GRID import ND280Dir
import ND280GRID
import optparse
import os
import sys
import time
import traceback

# Parser Options

parser = optparse.OptionParser()
## Common with genie_setup
parser.add_option("-a","--dirA",   dest="dirA",   type="string",help="Directory A (LFN)")
parser.add_option("-b","--dirB",   dest="dirB",   type="string",help="Directory B (SRM)")
parser.add_option("-f","--fts",    dest="fts",    type="int",   help="Use FTS flag 1=yes 0=no", default=1)
parser.add_option("-p","--pattern",dest="pattern",type="string",help="Only sync files matching <pattern>")
parser.add_option("-i","--ftsInt", dest="ftsInt", type="int",   help="Optional integer to pass to FTS for uniquifying transfer-file names")
(options,args) = parser.parse_args()

###############################################################################

# The start time.
start = time.time()


# Use FTS?
fts=options.fts

# Specify file patter e.g. '.root' to copy
pattern=options.pattern
if pattern:
    print 'Synchronising '+pattern+' files'
else:
    pattern=''

# Add optional integer to FTS transfer-file name (to prevent overwriting)
ftsInt=options.ftsInt
if not ftsInt:
    ftsInt=os.getpid()

try:
    # Create ND280Dir object
    dirA=ND280Dir(options.dirA,ls_timeout=600)

    # Sync this ND280Dir with dir
    dirA.NewSync(options.dirB,fts,pattern,ftsInt)
except:
    traceback.print_exc()

# The time taken
duration = time.time() - start

print 'It took '+str(duration)+' seconds to synchronise directories.\n'
