#!/usr/bin/env python2
"""
The DIRAC API creates a JDL (not stored locally)
file at submission. These classes help facilitate
creating job scripts
"""
from datetime import date, datetime
import time
import os
from os import getenv
from os.path import isfile, join
import ND280GRID
import ND280Computing
from ND280Computing import NONRUNND280JOBS


class ND280DIRACProcess(object):
    """
    The ND280 process that uses the DIRAC
    API to structure the JDL. Provides more
    functionality to add options
    """

    class Error(Exception):
        """an internal class for errors"""
        pass

    def __init__(self, nd280_filename, nd280ver, jobtype,
                 executable, argument, options={}):
        self.job_descript = None
        self.executable = executable
        self.argument = argument + nd280_filename
        self.options = dict()

        defaults = {
                       'CPUTime': 86400,
                       # TODO Below not suppported by DIRAC v6r19p10
                       # TODO Check Supported API functionality for newer versions
                       'Memory': 20971520,
                       'VMemory': 4194304
                   }

        # set defaults first
        for key, value in defaults.iteritems():
            self.options[key] = value
        # now set what inputs
        for key, value in options.iteritems():
            self.options[key] = value
        self.nd280_filename = nd280_filename
        # jd stands for job description
        self.jd = ND280DIRACJobDescription(nd280_filename, nd280ver, jobtype,
                                           self.executable, self.argument,
                                           self.options)


class ND280DIRACJobDescription(object):
    """
    A class to write a DIRAC python script that gives the
    JDL equivalent information
    """

    class Error(Exception):
        """an internal class for errors"""
        pass

    def __init__(self, nd280_filename, nd280ver, jobtype,
                 executable, argument, options={}):
        self.scriptname = str()
        self.nd280_file = ND280GRID.ND280File(nd280_filename)
        self.nd280ver = nd280ver
        self.jobtype = jobtype
        self.executable = executable
        self.argument = argument
        self.options = options
        self.cfgfile = None
        self.bannedSites = list()
        self.inputSandbox = list()
        self.outputSandbox = list()
        self.SetupDIRACAPIInfo()

    def AddBannedSite(self, bannedSite):
        """Add a banned site to the banned site list"""
        if len(bannedSite) > 0:
            self.bannedSites.append(bannedSite)

    def SetupDIRACAPIInfo(self):
        """Create a Raw data or MC processing jdl file.
           The one and only argument is the event type to
           process: spill OR cosmic trigger
        """

        self.scriptname = 'ND280' + self.jobtype
        # Don't add trigger to JDL for non runND280 jobs
        if self.jobtype not in NONRUNND280JOBS:
            if 'trigger' in self.options.keys():
                self.scriptname += '_' + str(self.options['trigger'])
        run_num = self.nd280_file.GetRunNumber()
        run_subnum = self.nd280_file.GetSubRunNumber()
        file_descriptors = [self.nd280ver, str(run_num), str(run_subnum)]
        self.scriptname += '_' + '_'.join(file_descriptors)

        # create the input and output sandboxes
        py_files = [self.executable]
        nd280_comp = getenv('ND280COMPUTINGROOT')
        for fn in os.listdir('%s/tools' % nd280_comp):
            full_name = join('%s/tools' % nd280_comp, fn)
            if isfile(full_name) and '.py' in fn:
                if '.pyo' in fn or '.pyc' in fn:
                    continue
                py_files.append(full_name)
        self.inputSandbox = py_files
        if self.cfgfile:
            self.inputSandbox.append(self.cfgfile)
        self.outputSandbox = ['std.out', 'std.err', '%s.log' % self.scriptname]
        return 0

    def CreateDIRACAPIFile(self, dir=''):
        """let DIRAC API handle creating the JDL info"""
        scriptfile = None
        try:
            if dir:
                self.scriptname = os.path.join(dir, self.scriptname)
            scriptfile = open('%s.py' % (self.scriptname), "w")

            # environment
            scriptfile.write('#!/usr/bin/env python2\n')

            # imports
            scriptfile.write('from DIRAC.Core.Base import Script\n')
            scriptfile.write('Script.parseCommandLine()\n')
            scriptfile.write('from DIRAC.Interfaces.API.Dirac import Dirac\n')
            scriptfile.write('from DIRAC.Interfaces.API.Job import Job\n')
            scriptfile.write('import ND280DIRACAPI\n')
            scriptfile.write('\n')
            scriptfile.write('diracJob = Job(\"\",\"std.out\",\"std.err\")\n')

            # job name
            scriptfile.write('diracJob.setName(\"%s\")\n' % self.scriptname)
            # job exe, args, and logFile
            scriptfile.write('diracJob.setExecutable(\"%s\", arguments=\"%s\", \
logFile=\"%s.log\")\n' % (self.executable, self.argument, self.scriptname))

            # job input Sandbox
            # it seems that * does not work with DIRAC v6r19p10
            scriptfile.write('inputSandbox = [\"%s\"' % self.inputSandbox[0])
            for i_file in range(1, len(self.inputSandbox)):
                scriptfile.write(', \"%s\"' % self.inputSandbox[i_file])
            scriptfile.write(']\n')
            scriptfile.write('diracJob.setInputSandbox(inputSandbox)\n')

            # job output Sandbox
            scriptfile.write('outputSandbox = [\"%s\"' % self.outputSandbox[0])
            for i_file in range(1, len(self.outputSandbox)):
                scriptfile.write(', \"%s\"' % self.outputSandbox[i_file])
            scriptfile.write(']\n')
            scriptfile.write('diracJob.setOutputSandbox(outputSandbox)\n')
            # job environmental variables
            scriptfile.write('diracJob.setExecutionEnv({\
\"VO_T2K_ORG_SW_DIR\": \"%s\"})\n' % (getenv('VO_T2K_ORG_SW_DIR')))
            if 'CPUTime' in self.options.keys():
                tlim = self.options['CPUTime']
                scriptfile.write('diracJob.setCPUTime(%d)\n' % tlim)
            scriptfile.write('\n')

            # # banned sites
            # scriptfile.write('diracJob.setBannedSites([\"%s\"' % self.bannedSites[0])
            # for i_banned_site in range(1, len(self.bannedSites)):
            #     scriptfile.write(',\"%s\"' % self.bannedSites[i_banned_site])
            # scriptfile.write('])\n')

            # submit the job
            scriptfile.write('print \"submitting job %s\"\n' % (self.scriptname))
            scriptfile.write('dirac = Dirac()\n')
            scriptfile.write('result = dirac.submitJob(diracJob)\n')
            scriptfile.write('print \"Submission Result: \", result\n')
            scriptfile.write('\n')

            # write a job ID (JID) file for DIRAC to read, user to know JID
            scriptfile.write('try:\n')
            scriptfile.write('    jid = ND280DIRACAPI.GetJobIDFromSubmit(result)\n')
            scriptfile.write('    if jid is not \"-1\":\n')
            scriptfile.write('        jid_file = open(\"%s.jid\", \"w\")\n' % (self.scriptname))
            scriptfile.write('        jid_file.write(\'%s\\n\' % jid)\n')
            scriptfile.write('        jid_file.close()\n')
            scriptfile.write('    else:\n')
            scriptfile.write('        print \"Unable to creaate jid file for this job:\", jobName\n')
            scriptfile.write('except Exception as exception:\n')
            scriptfile.write('    print str(exception)\n')
            scriptfile.write('    print \"Unable to creaate jid file for this job:\", jobName')
            scriptfile.close()
        except self.Error as error:
                print str(error)
                print 'Unable to create job file'
        try:
            if scriptfile:
                scriptfile.close()
        except self.Error as error:
            print str(error)
            print 'Unable to close job file'


class DIRACBase(object):
    """dirac commands with a 10minute timeout"""


    class Error(Exception):
        """an internal class for errors"""
        pass


    def __init__(self, timeout=ND280Computing.StatusWait.kTimeout):
        self.timeout = timeout
        self.command = str()
        self.args = dict()
        self.inputs = list()

    def EnableDebug(self, enable=True):
        """Enable or disable debug"""
        if enable:
            self.args['-ddd'] = ''
        elif '-ddd' in self.args:
            del self.args['-ddd']

    def RemoveLFNString(self, inString):
        """Remove any instance of "LFN:" and "lfn:" from the input string """
        if type(inString) is str:
            return inString.replace('LFN:', '').replace('lfn:', '')

    def Run(self, PrintCommand=False):
        """almost equivalent to __str__, but with errors and multiple calls"""
        if PrintCommand:
            print self.command

        # Limit the execution time
        # - note this only clocks CPU time so zombie
        # processes will last forever..
        SelfCommand = self.__str__()
        # command = 'ulimit -t ' + str(self.timeout) + '\n'
        command = SelfCommand

        # try the command a few times because failures happen on the GRID
        print datetime.now()
        for ii in range(3):
            print 'Try %d of \"%s\" with %d timeout' % (ii, SelfCommand, self.timeout)
            lines, errors = ND280Computing.GetListPopenCommand(command)
            if errors:
                print 'ERROR!'
                print '\n'.join(errors)
                time.sleep(self.timeout)
                continue
            else:
                break
        # Removal of newlines, carriage returns
        lines = [l.strip() for l in lines]
        errors = [e.strip() for e in errors]
        return lines, errors

    def __str__(self):
        RetStr = str(self.command)
        for key, value in self.args.iteritems():
            if '--' in key:
                if '=' in key:
                    RetStr = RetStr + ' {}{}'.format(key, value)
                else:
                    RetStr = RetStr + ' {}={}'.format(key, value)
            elif '-' in key:
                RetStr = RetStr + ' {} {}'.format(key, value)
            else:
                RetStr = RetStr + ' -{} {}'.format(key, value)
        if type(self.inputs) is list:
            for input in self.inputs:
                RetStr = RetStr + ' {}'.format(input)
        elif type(self.inputs) is str:
            RetStr = RetStr + input
        return RetStr


class DMSFindLFN(DIRACBase):
    """
    Find a file in its file catalogue, default is all files in directory
    """

    def __init__(self, path, LFN='*'):
        super(DMSFindLFN, self).__init__()
        self.command = 'dirac-dms-find-lfns'
        path = self.RemoveLFNString(path)
        LFN = self.RemoveLFNString(LFN)
        if type(path) is str and len(path) == 0 and LFN != '*':
            path = LFN
            LFN.split('/')[len(LFN.split('/'))-1]
            path = path.replace(LFN, '').rstrip('/')
        self.inputs.append('Name={}'.format(LFN))
        self.args['--Path='] = path


class DMSRemoveLFN(DIRACBase):
    """
    Remove the given file from the File Catalog and from the storage
    """

    def __init__(self, LFN):
        super(DMSRemoveLFN, self).__init__()
        self.command = 'dirac-dms-remove-files'
        LFN = self.RemoveLFNString(LFN)
        if type(LFN) is str:
            self.inputs.append(LFN)
        if type(LFN) is list:
            for FileName in LFN:
                self.inputs.append(FileName)


class DMSAddFile(DIRACBase):
    """
    Add file to DFC. Note that use of default args is to
    allow calling easier to read
    """

    def __init__(self, LFN='', FileName='', SE=''):
        super(DMSAddFile, self).__init__()
        self.command = 'dirac-dms-add-file'
        LFN = self.RemoveLFNString(LFN)
        self.inputs.append(LFN)
        self.inputs.append(FileName)
        self.inputs.append(SE)


class DMSListReplicas(DIRACBase):
    """
    List replicas for a LFN
    """

    def __init__(self, LFN):
        super(DMSAddFile, self).__init__()
        self.command = 'dirac-dms-lfn-replicas'
        LFN = self.RemoveLFNString(LFN)
        self.inputs.append(LFN)


class DMSFileSize(DIRACBase):
    """
    Find the total size of a file or set of files
    """

    def __init__(self, LFN, size='MB'):
        super(DMSFileSize, self).__init__()
        self.command = 'dirac-dms-data-size'
        LFN = self.RemoveLFNString(LFN)
        self.AcceptableUnits = ['MB', 'GB', 'TB', 'PB']
        if size not in self.AcceptableUnits:
            raise self.Error('Input units to DMSFileSize \"%s\" is not acceptable\n\
Please use the following %s' % (size, str(self.AcceptableUnits)))
        self.args['--Unit='] = size
        if type(LFN) is str:
            self.inputs.append(LFN)
        if type(LFN) is list:
            for FileName in LFN:
                if 'LFN:' in FileName or 'lfn:' in FileName:
                    FileName.replace('lfn:', '').replace('LFN:', '')
                self.inputs.append(FileName)


class ProxyInfo(DIRACBase):
    """
    Proxy info status
    """

    def __init__(self):
        super(ProxyInfo, self).__init__()
        self.command = 'dirac-proxy-info'


class SEStatus(DIRACBase):
    """
    SE status
    """

    def __init__(self):
        super(SEStatus, self).__init__()
        self.command = 'dirac-dms-show-se-status'


def GetJobIDFromSubmit(submitResult):
    """When the DIRAC.submitJob() method is called, use this
       method to extract the JodID STRING from the dictionary
       example {...stuff..., 'Value': 8765031, 'JobID': 8765031}
    """
    jid_identifiers = ['JobID', 'Value']
    if type(submitResult) is dict:
        for identifier in jid_identifiers:
            if identifier in submitResult.keys():
                return str(submitResult[identifier]).strip()
    return '-1'
