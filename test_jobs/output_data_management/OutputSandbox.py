#!/usr/bin/env python2.7

from DIRAC.Core.Base import Script
Script.parseCommandLine()
from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.Interfaces.API.Job import Job

executable = '/usr/bin/env bash'
stdout = 'std.out'
stderr = 'std.err'
logfile = 'job.log'

# the executible here '' is later set, so don't confuse users later on
diracJob = Job('', stdout, stderr)
# give a descriptive name
diracJob.setName('OutputSandboxTest')
# set the program/executable, arguments, logFile, ...
diracJob.setExecutable(executable, arguments='test.sh', logFile=logfile)
# set the job length, not needed in this example
# diracJob.setCPUTime(500)
# this file is needed remotely for the job
diracJob.setInputSandbox(['test.sh'])
# these files are created by the job regardless of the executable
diracJob.setOutputSandbox([stdout, stderr, logfile, 'env.out'])
"""
Output data is written to / <VO> / user / <initial> / <username>
so the full path of output data in this example is
/<VO>/user/<initial>/<username>/tests

"""
# this file will come in the output sandbox
diracJob.setOutputData(['env.out'])

print 'job being submitted...'
dirac = Dirac()
result = dirac.submit(diracJob)
print 'Submission Result: ', result
