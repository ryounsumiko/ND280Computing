#!/usr/bin/env python2.7

from DIRAC.Core.Base import Script
Script.parseCommandLine()
from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.Interfaces.API.Job import Job

exe = '/home/mhogan/software/ND280Computing/processing_scripts/P0DCalibProcess.py'
args = '-v v12r15 -i lfn:/grid/t2k.org/nd280/raw/ND280/ND280/00014000_00014999/nd280_00014000_0000.daq.mid.gz'
stdout = 'std.out'
stderr = 'std.err'
logfile = 'ND280Custom.log'
environmentDict = {
    'VO_T2K_ORG_SW_DIR': '/cvmfs/t2k.egi.eu'
}

# the executible here '' is later set, so don't confuse users later on
diracJob = Job('', stdout, stderr)
# give a descriptive name
diracJob.setName('ND280Custom')
# set the program/executable, arguments, logFile, ...
diracJob.setExecutable(exe, arguments=args, logFile=logfile)
# set the job length
diracJob.setCPUTime(3600)
# this file is needed remotely for the job
diracJob.setInputSandbox(
    [
        "../custom_parameters/P0DMOD.PARAMETERS.DAT",
        "RunCustom.py",
        "P0DCalibProcess.py",
        "../tools/ND280Computing.py",
        "../tools/ND280Configs.py",
        "../tools/ND280GRID.py",
        "../tools/ND280Job.py",
        "../tools/ND280Software.py",
        "../tools/pexpect.py",
        "../tools/StorageElement.py"
    ]
)

# make sure to export VO_T2K_ORG_SW_DIR
diracJob.setExecutionEnv(environmentDict)

# these files are created by the job regardless of the executable
diracJob.setOutputSandbox([stdout, stderr, logfile])
"""
Output data is written to / <VO> / user / <initial> / <username>
so the full path of output data in this example is
/<VO>/user/<initial>/<username>/tests

"""
diracJob.setOutputData(['LFN:*root'], outputSE='CA-TRIUMF-T2K1-disk', outputPath='tests')

print 'job being submitted...'
dirac = Dirac()
result = dirac.submit(diracJob)
print 'Submission Result: ', result
