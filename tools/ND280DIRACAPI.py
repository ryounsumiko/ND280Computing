#!/usr/bin/env python2.7

from os import getenv
import StorageElement as SE
import ND280GRID


class DIRACJOB(ND280GRID.ND280JDL):
    """a class to write a DIRAC python script that gives the
    JDL equivalent information"""

    class Error(Exception):
        """an internal class for errors"""
        pass

    def __init__(self, nd280ver, input, jobtype, evtype='', options={}):
        # inherited constructor
        super(DIRACJOB, self).__init__(self, nd280ver, input,
                                       jobtype, evtype, options)
        self.scriptname = self.jdlname

    def CreateAPIFile(self, dir=''):
        """let DIRAC API handle creating the JDL info"""
        try:
            if dir:
                self.scriptname = dir + '/' + self.scriptname
            jdlfile = open('blank.txt', 'w')
            scriptfile = open(self.scriptname, "w")

            scriptfile.write('#!/usr/bin/env python2.7\n')
            scriptfile.write('from DIRAC.Core.Base import Script\n')
            scriptfile.write('Script.parseCommandLine()\n')
            scriptfile.write('from DIRAC.Interfaces.API.Dirac import Dirac\n')
            scriptfile.write('from DIRAC.Interfaces.API.Job import Job\n')
            scriptfile.write('\n')
            scriptfile.write('diracJob = Job()\n')
            scriptfile.write('diracJob.setName(\"%s\")\n' % self.scriptname)
            scriptfile.write('diracJob.setExecutable(\"%s\", \
arguments=\"%s\"\n' % (self.executable, self.argument))

            # TODO test if input.LFN() has LFN in it!
            scriptfile.write('diracJob.setInputData(\"%s\")\n' %
                             self.input.LFN())
            # TODO Determine if * is really accepted in sandboxes
            # TODO Determine custom parameters path
            scriptfile.write('diracJob.setInputSandbox([\"../tools/*py\",\
\"../custom_parameters/*.DAT\"])\n')
            # TODO Determine if output names and output paths are set
            scriptfile.write('diracJob.setOutputData([\"%s\"], \"%s\", \"%s\")\
\n' % ('*root', SE.GetDefaultSE(), '/test/path'))
            scriptfile.write('diracJob.setOutputSandbox([\"%s\"])\
\n' % ('*root'))

            comp_path = getenv('ND280COMPUTINGROOT')
            if not comp_path:
                raise self.Error('Could not get\
the ND280COMPUTINGROOT environment variable, have you executed the setup.sh?')

            input_SB_string = 'InputSandbox = \
{\"' + comp_path + '/tools/*.py\", \"' + self.executable + '\"'
            if self.cfgfile:
                input_SB_string += ', \"' + self.cfgfile + '\"'
            for j, i in enumerate(self.inputsandbox):
                input_SB_string += ', \"' + i + '\"'
            input_SB_string += '};\n'
            jdlfile.write(input_SB_string)

            jdlfile.write('StdOutput = "' + self.stdoutput + '";\n')
            jdlfile.write('StdError = "' + self.stderror + '";\n')

            output_SB_string = 'OutputSandbox = {"' + \
                self.stdoutput + '", "' + self.stderror + '"'
            for o in self.outputsandbox:
                output_SB_string += ', "' + o + '"'
            output_SB_string += '};\n'
            jdlfile.write(output_SB_string)

            # Data Requirements for LFC InputData
            jdlfile.write('DataRequirements = {\n[\nDataCatalogType = "DLI";\
\nDataCatalog = "'+getenv('LFC_HOST')+':8085/";\n')
            if self.input.alias and 'cvmfs' not in self.input.path:
                # Should use lcg-lr to determine where data is located.
                jdlfile.write('InputData = {"' + self.input.alias +
                              '"};\n]\n};\n')
            # generic LFC Data Requirements
            else:
                # The location of the replicas determine the resource matching
                jdlfile.write('InputData = \
{"lfn:/grid/t2k.org/nd280/cvmfsAccessList"};\n]\n};\n')
            jdlfile.write('DataAccessProtocol = {"gsiftp"};\n')

            # VO requirements (ND280 software version etc)
            jdlfile.write('VirtualOrganisation = \"t2k.org\";\n')

            # under CVMFS s/w tags no longer work
            # jdlfile.write('Requirements=Member(\"VO-t2k.org-ND280-' +
            #               self.nd280ver + '\",\
# other.GlueHostApplicationSoftwareRunTimeEnvironment)')

            # Resource requirements (CPU time, RAM etc)
            # jdlfile.write(' && other.GlueCEPolicyMaxCPUTime > 600')

            jdlfile.write('Requirements = other.GlueCEPolicyMaxCPUTime > 600')
            jdlfile.write(' && ')
            jdlfile.write('other.GlueHostMainMemoryRAMSize >= ' +
                          self.queuelim)

            # Add regexp to requirements? (to exclude sites etc)
            if self.options['regexp']:
                jdlfile.write(' && '+self.regexp)
            jdlfile.write(';\n')

            # MyProxy server requirements
            if getenv('MYPROXY_SERVER'):
                jdlfile.write('MyProxyServer = \"' +
                              getenv('MYPROXY_SERVER')+'\";\n')
            else:
                print 'Warning MyProxyServer attribute undefined!'

            # Finished writing the JDL
            jdlfile.close()
            return self.jdlname
        except Exception as exception:
            print str(exception)
            print "Could not write create the " + self.jdlname + " jdl file"
        return ""
