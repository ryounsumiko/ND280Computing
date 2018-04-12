#!/usr/bin/env python2.7

from DIRAC.Core.Base import Script
Script.parseCommandLine()
from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.Interfaces.API.Job import Job

diracJob = Job()
diracJob.setCPUTime(500)
diracJob.setExecutable('echo', arguments='Hello world!')
# diracJob.setExecutable('ls', arguments='-l')
# diracJob.setExecutable('echo', arguments='hello again')
diracJob.setName('HelloWord')

dirac = Dirac()
result = dirac.submit(diracJob)
print 'Submission Result: ', result
