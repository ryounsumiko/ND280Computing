#!/usr/bin/env python2.7

"""
Script to submit a custom GRID job
"""

from commands import getstatusoutput
import optparse
import os
from os.path import exists
from os.path import join
import pexpect
import sys
from time import sleep

from ND280GRID import ND280File
from ND280DIRACAPI import ND280DIRACProcess as DIRACProcess

# usage = 'usage: %prog [options]'
parser = optparse.OptionParser()

# Mandatory
parser.add_option('-f', '--filename',
                  default='file.list',
                  help='File containing filenames to process')
parser.add_option('-v', '--version',
                  default='v12r15',
                  help='Version of nd280 software to use')
parser.add_option('-x', '--execfile',
                  default='MyProcess.py',
                  help='Program/Script that should be sent with the job')

# Optional
parser.add_option('-n', '--nodatareq', default=False,
                  help='Optional disable DataRequirements in JDL file',
                  action='store_true', )

parser.add_option('-o', '--outdir', default='',
                  help='Optional output directory. \
Can also specify using $ND280JOBS env variable. \
Defaults to $PWD/Jobs if neither are present')

parser.add_option('-r', '--resource', default='',
                  help='Optional CE resource to submit to')

parser.add_option('-u', '--delegation', default='',
                  help='Optional proxy delegation id, e.g $USER')

parser.add_option('-O', '--optargs', default='',
                  help='Optional args passed to program, comma delimited')

parser.add_option('-i', '--inputs', default='',
                  help='Optional files for input SandBox, comma delimited')

parser.add_option('--dirac', default=False,
                  help='Optional submission via DIRAC',
                  action='store_true')

parser.add_option('--useTestDB', default=False,
                  help='Prepend the DB cascade with test DB',
                  action='store_true')

parser.add_option("--test", default=False,
                  help="Test run, do not submit jobs",
                  action='store_true')

(options, args) = parser.parse_args()
##########################################################################

# Main Program

if not (exists(options.filename) and exists(options.execfile)):
    parser.print_help()
    sys.exit()
else:
    run_settings = [options.filename, options.version, options.execfile]
    print 'Running with %s' % (' '.join(run_settings))

# Abbreviate options
delegation = options.delegation
execfile = options.execfile
listname = options.filename
nd280ver = str(options.version)
optargs = options.optargs
outdir = options.outdir
resource = str(options.resource)
username = os.getenv('USER')

# Determine output directory
if not outdir:
    outdir = os.getenv('ND280JOBS')
    if not outdir:
        outdir = join(os.getenv('PWD'), 'Jobs/')
    outdir += join('/', nd280ver)
outdir += '/'

if not os.path.isdir(outdir):
    # out = getstatusoutput('mkdir ' + outdir)
    getstatusoutput('mkdir ' + outdir)

# Read input file list
filelist = [a_file.strip() for a_file in open(listname, 'r').readlines()]

# Define arguments to custom process
arglist = '-v ' + nd280ver + ' -i '
if optargs:
    arglist = '%s %s' % (arglist, ' '.join(options.optargs.split(',')))

# Use the test DB?
if options.useTestDB:
    arglist += ' --useTestDB '

# Count the number of jobs submitted
counter = 0

# Loop over the list of files to process
for a_file in filelist:

    # Create file instance
    infile = None
    try:
        print a_file
        infile = ND280File(a_file)
    except Exception as excpt:
        print str(excpt)
        print 'File not on LFN, skipping'
        continue

    print 'Done making infile', a_file

    runnum = str(infile.GetRunNumber())
    subrunnum = str(infile.GetSubRunNumber())
    jdlbasename = '_'.join(['ND280Custom', nd280ver, runnum, subrunnum])

    if options.dirac:
        dirac_proc = DIRACProcess(a_file, nd280ver, 'Custom',
                                  execfile, arglist)
        dirac_script = '%s.py' % dirac_proc.jd.scriptname
        if os.path.isfile(dirac_script):
            os.system('rm -f %s' % dirac_script)
        dirac_proc.jd.CreateDIRACAPIFile()
        if os.path.isfile(dirac_script):
            command = '/usr/bin/env python2 %s' % (dirac_script)
            print command
            if not options.test:
                os.system(command)
            counter += 1
            # Give the wms some time
            # sleep(ND280Computing.status_wait_times.kJobSubmit)
    else:

        jdlname = '%s.jdl' % jdlbasename
        jidname = '%s.jid' % jdlbasename
        # Open JDL file for writing
        jdlfile = open(jdlname, "w")

        # Write the custom JDL (should use ND280JDL here -
        # but it is presently only capable of handling
        # one extra file for the input sanbox)
        jdlfile.write('Executable = "%s";\n' % (execfile))
        jdlfile.write('Arguments = "%s %s";\n' % (arglist, a_file))
        jdlfile.write('InputSandbox = {"../tools/*.py",\
"%s","../custom_parameters/*.DAT"' % (execfile))
        if options.inputs:
            for option_i in options.inputs.split('/'):
                jdlfile.write(',"%s"' % (option_i))
        jdlfile.write('};\n')
        stdout = 'ND280Custom.out'
        stderr = 'ND280Custom.err'
        jdlfile.write('StdOutput = "%s";\n' % stdout)
        jdlfile.write('StdError = "%s";\n' % stderr)
        jdlfile.write('OutputSandbox = {"%s", "%s"};\n' % (stdout, stderr))
        if not options.nodatareq:
            jdlfile.write('DataRequirements = {\n')
            jdlfile.write('[\n')
            jdlfile.write('DataCatalogType = "DLI";\n')
            jdlfile.write('DataCatalog = "'+os.getenv('LFC_HOST')+':8085/";\n')
            jdlfile.write('InputData = {"%s"};\n' % (a_file))
            jdlfile.write(']\n')
            jdlfile.write('};\n')
            jdlfile.write('DataAccessProtocol = "gsiftp";\n')
        jdlfile.write('VirtualOrganisation = "t2k.org";\n')
        jdlfile.write('Requirements = Member("VO-t2k.org-ND280-\
%s",other.GlueHostApplicationSoftwareRunTimeEnvironment) ' % (nd280ver))
        jdlfile.write(' && other.GlueCEPolicyMaxCPUTime > 600 \
&& other.GlueHostMainMemoryRAMSize >= 512; \n')

        if os.getenv('MYPROXY_SERVER'):
            my_proxy = os.getenv('MYPROXY_SERVER')
            jdlfile.write('MyProxyServer = "%s";' % my_proxy)
        else:
            print 'Warning MyProxyServer attribute undefined!'

        jdlfile.close()

        # First delete any old jid and jdl file
        if os.path.isfile(jidname):
            print 'jid file exists, removing'
            fjid = open(jidname, 'r')
            flines = fjid.readlines()
            joblink = flines[1]
            jar = joblink.split('/')
            jobout = jar[-1]
            jout = outdir + username + '_' + jobout
            if os.path.isfile(jout):
                print 'output file exists, removing'
                outdel = getstatusoutput('rm -rf ' + jout)
                if outdel[0] != 0:
                    print 'Error: rm -rf ' + jout + ' failed'
            outdel = getstatusoutput('rm -rf ' + jidname)
            if outdel[0] != 0:
                print 'Error: rm -rf ' + jidname + ' failed'

        command = 'glite-wms-job-submit'
        if delegation:
            command += ' -d ' + delegation
        else:
            command += ' -a'
        command += ' -c autowms.conf -o ' + jidname
        if not resource:
            command += ' ' + jdlname
        else:
            command += ' -r ' + resource + ' ' + jdlname
        print command

        ii = 0
        trials = 0
        while ii < 1 and trials < 10:

            if os.path.isfile(jidname):
                print 'jid written, do not submit again'
                break

            if options.test:
                print 'TEST RUN'
                break

            child = pexpect.spawn(command, timeout=30)
            ii = child.expect([pexpect.TIMEOUT, pexpect.EOF])

            if ii == 0:
                print 'Retrying ...'
                trials += 1
            else:
                print child.before

            # Give the wms some time
            sleep(200)

        counter += 1

print '--------------------------------'
print 'Submitted ' + str(counter) + ' jobs'
