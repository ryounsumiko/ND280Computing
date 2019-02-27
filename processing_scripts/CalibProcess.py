#!/usr/bin/env python2.7

# June 2011
# The custom job (run over files with RunCustom.py will run the calibration jobs required to generate calibration
# constants for 2010b data:
# Run on raw data as that is distributed everywhere
# Run unpk and cali through ND280Control but with modified parameters for oaCalib and tfbApplyCalib
# Run SimpleTrackFitter.exe on these output cali files
# Run collectMuonData.exe on the SimpleTrackFitter output
# copy the cali output to the relevant directory
# copy the stft output rootfile to the relevant directory
# copy the cmud output rootfile to the relevant directory

import optparse
import os
import sys
import ND280Job
import ND280GRID
import random
import time
from ND280GRID import ND280File
from ND280Job  import ND280Process


# Parser Options

parser = optparse.OptionParser()

parser.add_option("-i","--input",  type="string",                      help="Input to process, must be an lfn")
parser.add_option("-v","--version",type="string",                      help="Version of nd280 software to use")
parser.add_option("--useTestDB",   action='store_true', default=False, help="Prepend the DB cascade with the test DB")

(options,args) = parser.parse_args()

###############################################################################

# Main Program
nd280ver = options.version
if not nd280ver:
    sys.exit('Please enter a version of the ND280 Software to use')

## example input is 'lfn:/t2k.org/nd280/raw/ND280/ND280/00005000_00005999/nd280_00005216_0000.daq.mid.gz'
input = options.input
if not input and not 'lfn:' in input:
    sys.exit('Please enter an lfn: input file')

dirsuff = '_ecalmod'

os.system('env')


# Delay processing by random time
# to avoid database blocking
rt = 200*random.random()
print 'Sleeping ' + str(rt) + ' seconds'
time.sleep(rt)

print 'INPUT FILE: ' + input
input_file = ND280File(input)

## Create Job object
print 'Job object'
fmem   = 20*1024*1024  # max 20GB file size
vmem   = 4 *1024*1024  # max 4GB memory
tlim   = 24*3600       # max 24h running
dbtime = 2097-15-20    # check this!

modules    = "oaCalib"
modulelist = []
if modules:
    modulelist = modules.split(',')
    print modulelist
evtype = 'cosmic'
config = '[calibrate],par_override=ECALMOD.PARAMETERS.DAT'
j = ND280Process(nd280ver, input_file, "Raw", evtype, modulelist, config, dbtime, fmem, vmem, tlim)

## use the test DataBase?
if options.useTestDB:
    j.useTestDB=True

## Build up the path lfn:/t2k.org/nd280/calib/v*r*p*/ND280/ND280/0000*000_0000*999/[filetype]
path_prot = 'lfn:/t2k.org/nd280/calib/' + nd280ver + '/ND280/ND280/' + input_file.GetRunRange() + '/'
path_end  = ''

## Copy across the root files, register some
#  Remove files from list if respin
#  cata, logf, cnfg always copied
dirlist = []
copyfiles = ['cali','stft','cmud']
# copyfiles = ['stft','cmud']
dirlist   = copyfiles


##Test that we are able to copy a test file
print 'Testing copy'
j.TestCopy(path_prot, path_end, dirsuff, ND280GRID.GetDefaultSE())

## Run the Job
#print 'Running quick job'
#j.SetQuick()

j.RunRaw()

## Now run the simple track fitter on this
j.RunSimpleTrackFitter()

## Now run collectMuonData on this
j.RunCollectMuonData()

print 'Copy files'
j.CopyRootFiles(path_prot, path_end, dirlist, dirsuff, ND280GRID.GetDefaultSE())
j.CopyLogFile  (path_prot, path_end, dirsuff, ND280GRID.GetDefaultSE())

print 'Finished OK'


