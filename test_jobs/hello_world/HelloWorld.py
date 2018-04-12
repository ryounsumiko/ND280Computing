#!/usr/bin/env python2.7

# DO NOT CHANGE THE ORDER OF THESE!
from DIRAC.Core.Base import Script
Script.parseCommandLine()
from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.Interfaces.API.Job import Job

# create the DIRAC API Job object
diracJob = Job()
# set the job length, but not needed in this example
diracJob.setCPUTime(500)
diracJob.setExecutable('echo', arguments='\"Hello world!\"')
# multiple executables can be set
diracJob.setExecutable('ls', arguments='-l')
diracJob.setExecutable('echo', arguments='\"hello again\"')
diracJob.setName('HelloWorld')

print 'submitting job', 'HelloWorld'
dirac = Dirac()
result = dirac.submit(diracJob)
print 'Submission Result: ', result
