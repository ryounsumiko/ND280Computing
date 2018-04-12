#!/usr/bin/env python2.7

from DIRAC.Core.Base import Script
Script.parseCommandLine()
from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.Interfaces.API.Job import Job

executable = '/usr/bin/env bash'
stdout = 'std.out'
stderr = 'std.err'
logfile = 'job.log'

diracJob = Job('', stdout, stderr)
# diracJob.setCPUTime(500)
diracJob.setName('OutputSandboxTest')
diracJob.setInputSandbox(['test.sh'])
diracJob.setExecutable(executable, arguments='test.sh', logFile=logfile)
diracJob.setOutputSandbox([stdout, stderr, logfile])
diracJob.setOutputData(['env.out'], outputSE='CA-TRIUMF-T2K1-disk', outputPath='LFN:/grid/t2k.org/nd280/contrib/hogan')

print 'job being submitted...'
dirac = Dirac()
result = dirac.submit(diracJob)
print 'Submission Result: ', result
