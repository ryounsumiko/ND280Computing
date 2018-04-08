#!/usr/bin/env python2.7

import optparse
import os
from os.path import join
import sys
import random
import time
import ND280GRID
from ND280GRID import ND280File
from ND280Job import ND280Process

# Parser Options

parser = optparse.OptionParser()

# Manadatory options
parser.add_option("-e", "--evtype", dest="evtype", type="string",
                  help="Event type, spill or cosmic trigger")
parser.add_option("-i", "--input", dest="input", type="string",
                  help="Input to process, must be an lfn")
parser.add_option("-p", "--prod", dest="prod", type="string",
                  help="Production, e.g. 4A")
parser.add_option("-t", "--type", dest="type", type="string",
                  help="Production type, rdp or rdpverify")
parser.add_option("-v", "--version", dest="version", type="string",
                  help="Version of nd280 software to use")
# Optional
parser.add_option("-b", "--dbtime", dest="dbtime", type="string",
                  help="Freeze time for the database, e.g. 2011-07-07")
parser.add_option("-c", "--config", dest="config", type="string",
                  help="Additions to the \
runND280 config file, e.g. '[calibration],a=0,b=0,[reconstruction],c=0'")
parser.add_option("-d", "--dirs", dest="dirs", type="string",
                  help="Suffix appended to directory names, e.g. _new")
parser.add_option("-m", "--modules", dest="modules", type="string",
                  help="Specified modules to run")

parser.add_option("--highlandVersion", default='',
                  help="Version of nd280Highland2 to process with")
parser.add_option("--test", default=False,
                  help="Test run, do not submit jobs", action='store_true')

(options, args) = parser.parse_args()

###############################################################################

# Main Program
nd280ver = options.version
if not nd280ver:
    sys.exit('Please enter a version of the ND280 Software to use')

prod = options.prod
respin = str()
prodnr = str()
if prod:
    respin = prod[-1]
    prodnr = 'production'
    nr = prod[:-1]
    if len(nr) == 1:
        prodnr += '00'
    if len(nr) == 2:
        prodnr += '0'
    prodnr += nr

dtype = options.type
if prod and not dtype:
    sys.exit('Please enter the type with -t')

verify = str()
if dtype:
    if len(dtype) > 3:
        verify = dtype[3:]
        dtype = dtype[:3]

if verify and not nd280ver:
    sys.exit('Please specify software version with -v')
"""
example input file is
'lfn:/grid/t2k.org/nd280/raw/ND280/ND280/00005000_00005999/nd280_00005216_0000.daq.mid.gz'
"""
input = options.input
if not input and 'lfn:' not in input:
    sys.exit('Please enter an lfn: input file')

modules = options.modules
modulelist = list()
if modules:
    modulelist = modules.split(',')

dirsuff = options.dirs
config = options.config
dbtime = options.dbtime

evtype = options.evtype
if not evtype:
    sys.exit('Please enter the event type you wish \
to process using the -e or --evtype flag')

os.system('env')

# Delay processing by random time
# to avoid database blocking
if not options.test:
    rt = 200*random.random()
    print 'Sleeping ' + str(rt) + ' seconds'
    time.sleep(rt)

print 'INPUT FILE: ' + input
input_file = ND280File(input)
stage = input_file.GetStage()

# Create Job object
print 'Job object'
fmem = 20*1024*1024  # max 20GB file size
vmem = 4*1024*1024   # max 4GB memory
tlim = 24*3600       # max 24h running
nd280_process = ND280Process(nd280ver, input_file, "Raw", evtype, modulelist,
                             config, dbtime, fmem, vmem, tlim)

print 'Max file size = ' + str(fmem / (1024.0 * 1024.0)) + 'GiB'
print 'Max memory = ' + str(vmem / (1024.0 * 1024.0)) + 'GiB'
print 'Max walltime = ' + str(tlim / 3600.) + 'hr'

"""
Build up the path
srm://srm-t2k.gridpp.rl.ac.uk/castor/ads.rl.ac.uk/prod/t2k.org/nd280/v7r19p1/logf/ND280/ND280/00003000_00003999/
"""
path_prot = 'lfn:/grid/t2k.org/nd280/'
path_end = str()
if prod:
    path_prot += join(prodnr, respin, dtype) + '/'
    if verify:
        path_prot += join(verify, nd280ver) + '/'
    else:
        path_prot += join('ND280', input_file.GetRunRange()) + '/'
    path_end = '/'
else:
    path_prot += nd280ver + '/'
    path_end = join('ND280/ND280', input_file.GetRunRange()) + '/'

# Copy across the root files, register some
# Remove files from list if respin
# cata, logf, cnfg always copied
dirlist = list()
if modulelist:
    for module in modulelist:
        if module == 'oaUnpack':
            dirlist.append('unpk')
        if module == 'oaCalib':
            dirlist.append('cali')
        if module == 'oaRecon':
            dirlist.append('reco')
        if module == 'oaAnalysis':
            dirlist.append('anal')
else:
    print 'This is a re-spin of stage ' + stage
    if stage == 'elmc':
        dirlist = ['cali', 'reco', 'anal']
    elif stage == 'cali':
        dirlist = ['reco', 'anal']
    elif stage == 'reco':
        dirlist = ['anal']

# Create a new proxy
# if pword:
#     print 'Renew proxy'
#     password_file='PASSWORD_FILE'
#     f=open(password_file,'w')
#     f.write(pword)
#     f.close()
#     command = 'export MYPROXY_SERVER=\
# lcgrbp01.gridpp.rl.ac.uk\nvoms-proxy-destroy\n'
#     command += 'myproxy-get-delegation -d --stdin_pass \
# --voms t2k.org:/t2k.org/Role=production < '+password_file+'\n'
#     command += 'voms-proxy-init -debug \
# -voms t2k.org:/t2k.org/Role=production -valid 168:0 -noregen'
#     os.system(command)
#     if rtc:
#         sys.exit('Proxy creation failed!')

# Test that we are able to copy a test file
print 'Testing copy'
nd280_process.TestCopy(path_prot, path_end, dirsuff,
                       ND280GRID.GetDefaultSE())

# Run the Job
print 'Running job'
nd280_process.RunRaw()

# was there a highland version specified
# and is oaAnalysis part of the job? If so create a mini tree...
if options.highlandVersion:
    module_test = 'oaAnalysis' in nd280_process.config_options['module_list']
    if module_test or stage is 'anal':
        print 'Incorporating RunCreateMiniTree.exe into job'
        runCreateMiniTree = True
        nd280_process.SetHighlandVersion(options.highlandVersion)
        nd280_process.RunCreateMiniTree()

print 'Copy files'

# log file check returns 0 if successful
if not nd280_process.LogFileCheck():
    if not options.test:
        nd280_process.CopyAll(path_prot, path_end, dirlist, dirsuff,
                              ND280GRID.GetDefaultSE())
    else:
        print 'TEST RUN, do not register output'
else:
    sys.exit('Failed LogFileCheck()')


print 'Finished OK'
