#!/usr/bin/env python2.7

"""
March 2012
The custom job (run over files with RunCustom.py)
will run the calibration jobs
required to generate calibration constants for Run 3 data:
Run on raw data as that is distributed everywhere
Run (unpk and) cali through ND280Control but
with modified parameters for oaCalib and tfbApplyCalib
Run P0DRECON.exe on these output cali files
Run CreateControlSamples.exe on the reconstructed events to
select through going muons in P0D
Run RunOAAnalysis.exe on the selected sand muons
copy the psmu output rootfile to the relevant directory
copy the anal output rootfile to the relevant directory
"""

import optparse
import os
from os.path import join
import sys
import random
from time import sleep
import ND280GRID
from ND280GRID import ND280File
from ND280Job import ND280Process
import StorageElement as SE


def main(argv):

    # Parser Options
    ########################################################################
    parser = optparse.OptionParser()
    # example input is
    # 'lfn:/grid/t2k.org/nd280/raw/ND280/ND280/00005000_00005999/nd280_00005216_0000.daq.mid.gz'
    parser.add_option("-i", "--input", dest="input",
                      type="string",
                      help="Input to process, must be an lfn")
    # example version is v12r15 or v11r31
    parser.add_option("-v", "--version", dest="version",
                      type="string", help="Version of nd280 software to use")
    # example ???
    parser.add_option("--useTestDB", action='store_true', default=False,
                      help="Prepend the DB cascade with the test DB")

    (options, args) = parser.parse_args()

    nd280ver = options.version
    if not nd280ver:
        print 'Please enter a version of the ND280 Software to use'
        parser.print_help()
        return

    usr_input = options.input
    if not (type(usr_input) is str and 'lfn:' in usr_input):
        print 'Please enter an lfn: input file'
        parser.print_help()
        return

    default_SE = SE.GetDefaultSE()
    #########################################################################
    # Parser Options

    # Main Program
    ########################################################################

    # print environment variables
    eightyPounds = str()
    for index in range(0, 80):
        eightyPounds += '#'

    print 'Environment variables'
    print eightyPounds
    os.system('env')
    print eightyPounds

    # Delay processing by random time to avoid database blocking
    # rt = 200. * random.random()
    rt = 2. * random.random()
    print eightyPounds
    print 'Sleeping ' + str(rt) + ' seconds'
    print eightyPounds
    sleep(rt)

    print eightyPounds
    print 'INPUT FILE: ' + usr_input
    print eightyPounds
    input_file = ND280File(usr_input)

    # directory suffix added to each stage name
    dirsuff = '_p0dmod'

    print eightyPounds
    # Create Job object
    print 'Job object'
    # max file size
    fmem = 20*1024*1024  # 20GiB
    # max memory
    vmem = 4*1024*1024  # 4GB
    # job time limit
    tlim = 24*3600  # 24h
    dbtime = '2038-01-01'

    print 'Max file size = ' + str(fmem / (1024.0 * 1024.0)) + 'GiB'
    print 'Max memory = ' + str(vmem / (1024.0 * 1024.0)) + 'GiB'
    print 'Max walltime = ' + str(tlim / 3600.) + 'hr'
    print 'DB time = ' + dbtime
    print eightyPounds

    # define the processing
    evtype = 'spill'
    modules = "oaCalib"
    modulelist = list()
    if modules:
        modulelist = modules.split(",")
        print eightyPounds
        print 'module list'
        print modulelist
        print eightyPounds
    config = '[calibrate],par_override = P0DMOD.PARAMETERS.DAT'
    nd280_proc = ND280Process(nd280ver, input_file, "Raw", evtype,
                              modulelist, config, dbtime, fmem, vmem, tlim)
    # use the test DataBase?
    if options.useTestDB:
        nd280_proc.useTestDB = True

    # Build up the path
    # lfn:/grid/t2k.org/nd280/calib/v*r*p*/ND280/ND280/0000*000_0000*999/[filetype]
    path_prot = join('lfn:/grid/t2k.org/nd280/calib',
                     nd280ver, 'ND280/ND280', input_file.GetRunRange())
    path_prot += '/'
    path_end = str()

    # Copy across the root files, register some
    # Remove files from list if respin
    # cata, logf, cnfg always copied
    copyfiles = ['psmu', 'anal']
    dirlist = copyfiles

    # Test that we are able to copy a test file
    print eightyPounds
    print 'Testing copy'
    nd280_proc.TestCopy(path_prot, path_end, dirsuff, default_SE)
    print eightyPounds

    # Run the Job
    # print 'Running quick job'
    # nd280_proc.SetQuick()

    # calibration
    print eightyPounds
    print 'ND280Process.RunRaw()'
    nd280_proc.RunRaw()
    print eightyPounds

    # reconstruction
    print eightyPounds
    print 'ND280Process.RunP0DRecon()'
    nd280_proc.RunP0DRecon()
    print eightyPounds

    # sand muon selection
    print eightyPounds
    print 'ND280Process.RunP0DControlSample()'
    nd280_proc.RunP0DControlSample()
    print eightyPounds

    # oaAanalysis
    print eightyPounds
    print 'ND280Process.RunOAAnalysis()'
    nd280_proc.RunOAAnalysis()
    print eightyPounds

    print eightyPounds
    print 'Copy ROOT files'
    nd280_proc.CopyLogFile(path_prot, path_end, dirsuff, default_SE)
    print eightyPounds

    print eightyPounds
    print 'Copy Log files'
    nd280_proc.CopyRootFiles(path_prot, path_end, dirlist, dirsuff, default_SE)
    print eightyPounds

    print eightyPounds
    print 'Finished OK'
    print eightyPounds
    ########################################################################
    # Main Program


if __name__ == "__main__":
    main(sys.argv[1:])
