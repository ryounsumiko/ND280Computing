#!/usr/bin/env python2
"""since the DIRAC API creates a JDL file at submission,
these classes help facilitate creating job scripts
"""

from os import getenv
from StorageElement import units
import ND280GRID
import ND280Job


class ND280DIRACProcess(ND280Job.ND280Process):
    """The ND280 process that instead uses the DIRAC
       API to describe the process
    """

    class Error(Exception):
        """an internal class for errors"""
        pass

    def __init__(self, nd280ver, input, jobtype, evtype='', modules='',
                 config='', dbtime='', fmem=20971520, vmem=4194304,
                 tlim=86400):
        super(ND280DIRACProcess, self).__init__(nd280ver, input, jobtype,
                                                evtype, modules, config,
                                                dbtime, fmem, vmem, tlim)
        if type(input) is str:
            self.input = ND280DIRACJobDescription(input)
        else:
            self.input = None

        # memory usage converter
        self.units = units(1)  # 1 = 1 kB

        # overly protective check
        if type(self.input) is ND280DIRACJobDescription:
            if type(tlim) is int:
                self.input.options['CPUTime'] = tlim
            # TODO Not suppported by DIRAC v6r19p10
            # TODO Check Supported API functionality for newer versions
            if type(fmem) is int:
                self.input.options['Memory'] = fmem * self.units.kGB
            # TODO Not suppported by DIRAC v6r19p10
            # TODO Check Supported API functionality for newer versions
            if type(vmem) is int:
                self.input.options['VMemory'] = vmem * self.units.kGB


class ND280DIRACJobDescription(ND280GRID.ND280JDL):
    """a class to write a DIRAC python script that gives the
    JDL equivalent information"""

    class Error(Exception):
        """an internal class for errors"""
        pass

    def __init__(self, nd280ver, input, jobtype, evtype='', options={}):
        # inherited constructor
        super(ND280DIRACJobDescription, self).__init__(nd280ver, input,
                                                       jobtype, evtype, options)
        self.scriptname = self.jdlname

    def CreateDIRACAPIFile(self, dir=''):
        """let DIRAC API handle creating the JDL info"""
        scriptfile = None
        try:
            if dir:
                self.scriptname = dir + '/' + self.scriptname
            scriptfile = open('%s.py' % (self.scriptname), "w")

            # environment
            scriptfile.write('#!/usr/bin/env python2\n')

            # imports
            scriptfile.write('from DIRAC.Core.Base import Script\n')
            scriptfile.write('Script.parseCommandLine()\n')
            scriptfile.write('from DIRAC.Interfaces.API.Dirac import Dirac\n')
            scriptfile.write('from DIRAC.Interfaces.API.Job import Job\n')
            scriptfile.write('import ND280DIRACAPI\n')

            scriptfile.write('diracJob = Job(\"\",\"std.out\",\"std.err\")\n')
            # job name
            scriptfile.write('diracJob.setName(\"%s\")\n' % self.scriptname)
            # job exe, args, and logFile
            scriptfile.write('diracJob.setExecutable(\"%s\", arguments=\"%s\", \
logFile=\"%s.log\"\n' % (self.executable, self.argument, self.scriptname))

            # job input Sandbox
            # it seems that * does not work with DIRAC v6r19p10
            scriptfile.write('inputSandbox = [\"../tools/ND280Computing.py\", \
\"../tools/ND280Configs.py\", \"../tools/ND280GRID.py\", \
\"../tools/ND280Job.py\", \"../tools/ND280Software.py\", \
\"../tools/pexpect.py\", \"../tools/StorageElement.py\", \
\"../tools/ND280DIRACAPI.py\", \"%s\"' % (self.executable))
            if self.cfgfile:
                scriptfile.write(' \"%s\"', self.cfgfile)
            scriptfile.write(']\n')

            # job output Sandbox
            scriptfile.write('diracJob.setOutputSandbox([\"std.out\", \
\"std.err\", \"%s.log\"])\n' % (self.scriptname))
            # job environmental variables
            scriptfile.write('diracJob.setExecutionEnv({\
\"VO_T2K_ORG_SW_DIR\": \"%s\"})\n' % (getenv('VO_T2K_ORG_SW_DIR')))
            if 'CPUTime' in self.options.keys():
                tlim = self.options['CPUTime']
                scriptfile.write('diracJob.setCPUTime(%d)\n' % tlim)

            # submit the job
            scriptfile.write('print \"submitting job %s\"\n' % (self.scriptname))
            scriptfile.write('dirac = Dirac()')
            scriptfile.write('result = dirac.submit(diracJob)')
            scriptfile.write('print \"Submission Result: \", result')

            # write a job ID (JID) file for DIRAC to read, user to know JID
            scriptfile.write('try:')
            scriptfile.write('    jid = ND280DIRACAPI.GetJobIDFromSubmit(result)')
            scriptfile.write('    if jid is not \"-1\":\n')
            scriptfile.write('        jid_file = open(\"%s.jid\", \"w\")' % (self.scriptname))
            scriptfile.write('        jid_file.write(jid)\n')
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


def GetJobIDFromSubmit(submitResult):
    """when the DIRAC.submit() method is called, use this
    method to extract the JodID from the dictionary
    example {...stuff..., 'Value': 8765031, 'JobID': 8765031}
    """
    jid_identifiers = ['JobID', 'Value']
    if type(submitResult) is dict:
        for identifier in jid_identifiers:
            if identifier in submitResult.keys():
                return str(submitResult[identifier]).strip()
    return '-1'
