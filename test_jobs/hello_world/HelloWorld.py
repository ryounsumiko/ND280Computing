#!/usr/bin/env python2.7

# DO NOT CHANGE THE ORDER OF THESE!
from DIRAC.Core.Base import Script
Script.parseCommandLine()
from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.Interfaces.API.Job import Job

jobName = 'HelloWorld'

# create the DIRAC API Job object
diracJob = Job()
# set the job length, but not needed in this example
diracJob.setCPUTime(500)
diracJob.setName(jobName)
diracJob.setExecutable('echo', arguments='\"Hello world!\"')
# multiple executables can be set
# diracJob.setExecutable('ls', arguments='-l')
# diracJob.setExecutable('echo', arguments='\"hello again\"')

print 'submitting job', 'HelloWorld'
dirac = Dirac()
result = dirac.submit(diracJob)
print 'Submission Result: ', result

# try to create job id file
try:
    jid = 'JobID'
    if jid in result.keys():
        jid_file = open('%s.jid' % (jobName), 'w')
        jid_file.write('%s\n' % (str(result[jid]).strip()))
        jid_file.close()
    else:
        print 'Unable to creaate jid file for this job', jobName
except Exception as exception:
    print str(exception)
    print 'Unable to creaate jid file for this job', jobName

