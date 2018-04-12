#!/usr/bin/env python2.7
import sys

try:
    from DIRAC.Core.Base import Script
    Script.parseCommandLine()
    from DIRAC.Interfaces.API.Dirac import Dirac
    from DIRAC.Interfaces.API.Job import Job
except Exception as exception:
    print str(exception)
    print 'Unable to import DIRAC'
    sys.exit(1)


def main(argv):
    diracJob = Job()
    diracJob.setCPUTime(500)
    diracJob.setExecutable('echo', arguments='Hello world!')
    # diracJob.setExecutable('ls', arguments='-l')
    # diracJob.setExecutable('echo', arguments='hello again')
    diracJob.setName('HelloWord')

    dirac = Dirac()
    result = dirac.submit(diracJob)
    print 'Submission Result: ', result


if __name__ is '__main__':
    main(sys.argv[1:])
