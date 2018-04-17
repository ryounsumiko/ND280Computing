#!/usr/bin/env python2

from subprocess import Popen, PIPE

# t2k.org VO name
VO = 't2k.org'

# The ND280 detectors
ND280DETECTORS = ['ECAL', 'FGD', 'ND280', 'P0D', 'SMRD', 'TPC']

# The non runND280 job types
NONRUNND280JOBS = ['HADD', 'FlatTree', 'MiniTree']


class status_flags(object):
    """a namespace for status flags"""
    kProxyValid = 0
    kProxyInvalid = 1


class status_wait_times(object):
    """a namespace for common wait times"""
    kSecond = 1
    kMinute = 60 * kSecond
    kHour = 60 * kMinute
    kDay = 24 * kHour
    kProxyExpirationThreshold = 2 * kMinute
    kProxyNextCheck = 6 * kMinute
    kProcessWait = 1 * kMinute
    kTimeout = 5 * kMinute
    kJobSubmit = 2 * kMinute


class LCG(object):
    """lcg commands with timeouts set at start"""

    def __init__(self, timeout=10*status_wait_times.kMinute):
        self.commands = dict()
        self.timeout = None

        # new commands go here
        self.commands['bringonline'] = 'lcg-bringonline '
        
        self.SetTimeouts(timeout)

    def SetTimeouts(self, new_timeout):
        """initialize commands with common timeouts"""
        self.timeout = new_timeout
        for key, value in self.commands.iteritems():
            value += '--connect-timeout %d ' % (self.timeout)
            value += '--sendreceive-timeout %d ' % (self.timeout)
            value += '--bdii-timeout %d ' % (self.timeout)
            value += '--srm-timeout %d ' % (self.timeout)
            self.commands[key] = value

        # new commands go here
        self.bringonline = self.commands['bringonline']
            



def GetListPopenCommand(command):
    """submits a command with the stdin, out, and err available for printing
    return the list of lines"""

    try:
        popen = Popen([command], shell=True,
                      stdin=PIPE, stdout=PIPE, stderr=PIPE)
        lines = popen.stdout.readlines()
        errors = popen.stderr.readlines()
        # Something bad happened...
        if errors:
            print '\n'.join(errors)
            raise Exception

        return lines, errors

    # Something else bad happened...
    except Exception as exception:
        print str(exception)
    return [], errors
