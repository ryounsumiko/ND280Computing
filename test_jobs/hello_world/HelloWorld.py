#!/usr/bin/env python2.7

# DO NOT CHANGE THE ORDER OF THESE!
from DIRAC.Core.Base import Script
Script.parseCommandLine()
from DIRAC.Interfaces.API.Dirac import Dirac
from DIRAC.Interfaces.API.Job import Job

jobName = 'HelloWorld'
executable = '/bin/echo'
stdout = 'std.out'
stderr = 'std.err'
logfile = 'HelloWorldjob.log'

# The executable here '' is later set, so don't confuse users later on
diracJob = Job('', stdout, stderr)

diracJob.setName(jobName)

# Set the program/executable, arguments, logFile, ...
diracJob.setExecutable('echo', arguments='\"Hello world!\"')

# multiple executables can be set/appended
# diracJob.setExecutable('ls', arguments='-l')
# diracJob.setExecutable(executable, arguments='\"hello again\"')

# Set the job length, but not needed in this example
diracJob.setCPUTime(500)

print 'submitting job', jobName
dirac = Dirac()
result = dirac.submitJob(diracJob)
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

