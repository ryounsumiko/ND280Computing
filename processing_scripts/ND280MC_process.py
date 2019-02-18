#!/usr/bin/env python 

import optparse
import os
import sys
import ND280Job
import ND280GRID
from ND280GRID import ND280File
from ND280Job import ND280Process
import random
import time

# Parser Options

parser = optparse.OptionParser()

# Mandatory
parser.add_option("-e","--evtype",    default='', help="Event type, spill (spl) or cosmic (cos)trigger"                     )
parser.add_option("-i","--input",     default='', help="Input to process, must be an lfn"                                   )
parser.add_option("-p","--prod",      default='', help="Production, e.g. 4A"                                                )
parser.add_option("-t","--type",      default='', help="Production type, mcp or mcpverify"                                  )
parser.add_option("-v","--version",   default='', help="Version of nd280 software to use"                                   )
# Optional
parser.add_option("-b","--dbtime",    default='', help="Freeze time for the database, e.g. 2011-07-07"                      )
parser.add_option("-c","--config",    default='', help="Additions to the runND280 config file, e.g. '[calibration],a=0,b=0'")
parser.add_option("-d","--dirs",      default='', help="Suffix appended to directory names, e.g. _new"                      )
parser.add_option("-m","--modules",   default='', help="Specified modules to run"                                           )
parser.add_option("-g","--generator", default='', help="Neutrino generator type, neut or genie"                             )
parser.add_option("-a","--geometry",  default='', help="Geometry configuration for nd280, e.g. 2010-11-water"               )
parser.add_option("-y","--vertex",    default='', help="Vertex region in nd280, magnet or basket"                           )
parser.add_option("-w","--beam",      default='', help="Beam type simulation (bunches etc.), beama or beamb"                )

parser.add_option("--neutVersion",    default='',     help="Version of NEUT to be used"               )
parser.add_option("--POT",            default='1E18', help="No. of POT to generate"                   )
parser.add_option("--highlandVersion",default='',     help="Version of nd280Highland2 to process with")
parser.add_option("--test",           default=False,  help="Test run, do not submit jobs", action='store_true')

(options,args) = parser.parse_args()

###############################################################################

# Main Program 

nd280ver=options.version
if not nd280ver:
    sys.exit('Please enter a version of the ND280 Software to use')

prod = options.prod
respin=''
prodnr=''
if prod:
    respin=prod[-1]
    prodnr='production'
    nr=prod[:-1]
    if len(nr) == 1:
        prodnr += '00'
    if len(nr) == 2:
        prodnr += '0'
    prodnr += nr

dtype = options.type
if prod and not dtype:
    sys.exit('Please enter the type with -t')

verify = ''
if dtype:
    if len(dtype) > 3:
        verify = dtype[3:]
        dtype = dtype[:3]

if verify and not nd280ver:
    sys.exit('Please specify software version with -v')

## example input is 'lfn:/grid/t2k.org/nd280/raw/ND280/ND280/00005000_00005999/nd280_00005216_0000.daq.mid.gz'
input = options.input
if not input:
    sys.exit('Please enter an input file')
if not input.startswith('lfn:') and not input.startswith('/cvmfs'):
    sys.exit('Input file path must start with lfn: or /cvmfs')
    
print('soph - ND280MC_process.py  1)  input = ' + input)

modules = options.modules
modulelist = []
if modules:
    modulelist = modules.split(',')

evtype = options.evtype
if not evtype:
    sys.exit('Please enter the event type you wish to process using the -e or --evtype flag')

dirsuff   = options.dirs
config    = options.config
dbtime    = options.dbtime
generator = options.generator
geometry  = options.geometry
vertex    = options.vertex
beam      = options.beam

# Delay processing by random time
# to avoid database blocking
if not options.test:
    rt = 200*random.random()
    print 'Sleeping ' + str(rt) + ' seconds'
    time.sleep(rt)

print 'INPUT FILE: ' + input
input_file=ND280File(input)

print('soph - ND280MC_process.py  2)  input = ' + input)

    
## Create Job object
print 'Job object'
fmem=20*1024*1024 #max 20GB file size
vmem=4*1024*1024  #max 4GB memory
tlim=24*3600      #max 24h


## What flavour of MC process is this what stage of the processing chain does the input correspond to?
if 'fluka' in input:
    jobtype = 'nusetup'
    stage   = 'fluka'
else:
    jobtype = 'MC'
    stage   = input_file.GetStage()

print('soph - ND280MC_process.py  3)  stage = ' + stage)    

    
j=ND280Process(nd280ver, input_file, jobtype, evtype, modulelist, config, dbtime, fmem, vmem,tlim)



## Run the Job
runCreateMiniTree = False
print 'Running job'
if 'fluka' in input and options.neutVersion :
    j.SetNEUTVersion(options.neutVersion)
    j.RunNEUTSetup  (generator,geometry,vertex,beam,options.POT)
else:
    j.RunMC() 
    # was there a highland version specified and is oaAnalysis part of the job? If so create a mini tree...
    if options.highlandVersion and ('oaAnalysis' in j.config_options['module_list'] or stage == 'anal'):
        print 'Incorporating RunCreateMiniTree.exe into job'
        runCreateMiniTree = True
        j.SetHighlandVersion(options.highlandVersion)
        j.RunCreateMiniTree()

## Build up the path srm://srm-t2k.gridpp.rl.ac.uk/castor/ads.rl.ac.uk/prod/t2k.org/nd280/v7r19p1/logf/ND280/ND280/00003000_00003999/
path_prot='lfn:/grid/t2k.org/nd280/'
path_end=''
if prod:
    path_prot+= prodnr + '/' + respin + '/' + dtype + '/'
    if verify:
        path_prot+=verify + '/' + nd280ver + '/' + generator + '/' + geometry + '/' + vertex  + '/' + beam + '/'
    else:
        path_prot+=generator + '/' + geometry + '/' + vertex  + '/' + beam + '/'
    path_end='/'
else:
    path_prot+= nd280ver + '/'
    path_end= 'ND280/ND280/' + input_file.GetRunRange() + '/'


# Copy across the root files, register some
# Remove files from list if respin
# cata, logf, cnfg always copied
dirlist=[]
if modulelist:
    for module in modulelist:
        if module == 'nd280MC':
            dirlist.append('g4mc')
        if module == 'elecSim':
            dirlist.append('elmc')
        if module == 'oaCalibMC':
            dirlist.append('cali')
        if module == 'oaRecon':
            dirlist.append('reco')
        if module == 'oaAnalysis':
            dirlist.append('anal')
else:
    if not 'fluka' in input:
        ## Is this is a respin?

        if stage not in ['numc', 'nucp', 'gnmc', 'gncp']:
            print 'This is a re-spin of stage ' + stage
            if   stage=='elmc':
                dirlist = ['cali', 'reco', 'anal']
            elif stage=='cali':
                dirlist = ['reco', 'anal']
            elif stage=='reco':
                dirlist = ['anal']
        else:
            dirlist = ['g4mc', 'elmc', 'cali', 'reco', 'anal']
    else:
        ## This is a neutSetup job
        dirlist = ['numc']

if runCreateMiniTree:
    dirlist.append('mini'+options.highlandVersion)

print 'Copy files'

# log file check returns 0 if successful
if not j.LogFileCheck():
    if not options.test:
        j.CopyAll(path_prot, path_end, dirlist, dirsuff, ND280GRID.GetDefaultSE())
    else:
        print 'TEST RUN, do not register output'
else:
    sys.exit('Failed LogFileCheck()')

# if you got to here, the job ran to completion
print 'Finished OK'



