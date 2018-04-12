#!/usr/bin/env python2.7

from DIRAC.Core.Base import Script
from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.Interfaces.API.Job import Job
Script.parseCommandLine()

executable = '/usr/bin/env bash'
stdout = 'std.out'
stderr = 'std.err'
logfile = 'job.log'

diracJob = Job('', stdout, stderr)
# diracJob.setCPUTime(500)
diracJob.setName('OutputSandboxTest')
diracJob.setExecutable(executable, arguments='test.sh', logFile=logfile)
diracJob.setOutputSandbox(['env.out', stdout, stderr])

print 'job being submitted...'
dirac = Dirac()
result = dirac.submit(diracJob)
print 'Submission Result: ', result
