#!/usr/bin/env python2.7

import optparse
import ND280GRID
from ND280GRID import ND280JDL
import os
import sys
import time
import pexpect
import commands

#Parser options
parser = optparse.OptionParser()

#Mandatory (should be positional arguments or at least have default values!)
parser.add_option("-e","--evtype",  dest="evtype",  type="string",help="[Mandatory] Event type: spill or cosmic")
parser.add_option("-f","--filename",dest="filename",type="string",help="[Mandatory] File containing filenames to process")
parser.add_option("-j","--job",     dest="job",     type="string",help="[Mandatory] Job type, Raw, MC, FlatTree, MiniTree")
parser.add_option("-v","--version", dest="version", type="string",help="[Mandatory] Version of nd280 software to use")

#Optional
parser.add_option("-b","--dbtime",    dest="dbtime",    type="string",help="Freeze time for the database, e.g. 2011-07-07")
parser.add_option("-c","--config",    dest="config",    type="string",help="Additions to the runND280 config file, e.g. '[calibration],a=0,b=0,[reconstruction],c=0'")
parser.add_option("-d","--dirs",      dest="dirs",      type="string",help="Suffix appended to directory names, e.g. _new")
parser.add_option("-m","--modules",   dest="modules",   type="string",help="Specified modules to run, e.g -m oaUnpack,oaCalib")
parser.add_option("-n","--nsub",      dest="nsub",      type="string",help="Unique number for parallell submission")
parser.add_option("-o","--outdir",    dest="outdir",    type="string",help="Output directory. Can also specify using $ND280JOBS env variable. Defaults to $PWD/Jobs if neither are present")
parser.add_option("-p","--prod",      dest="prod",      type="string",help="Production, e.g. 4A")
parser.add_option("-q","--queuelim",  dest="queuelim",  type="string",help="Queue memory limit")
parser.add_option("-r","--resource",  dest="resource",  type="string",help="Optional - CE to submit to")
parser.add_option("-s","--prescale",  dest="prescale",  type="string",help="Submit every n:th file")
parser.add_option("-t","--type",      dest="type",      type="string",help="Production type, rdp, rdpverify, mcp or mcpverify")
parser.add_option("-u","--delegation",dest="delegation",type="string",help="Proxy delegation id, e.g $USER")
parser.add_option("-x","--extrafile", dest="extrafile", type="string",help="Any extra file that should be sent with the job")

parser.add_option("-g","--generator", dest="generator", type="string",help="Neutrino generator type, neut or genie")
parser.add_option("-a","--geometry",  dest="geometry",  type="string",help="Geometry configuration for nd280, e.g. 2010-11-water")
parser.add_option("-y","--vertex",    dest="vertex",    type="string",help="Vertex region in nd280, magnet or basket")
parser.add_option("-w","--beam",      dest="beam",      type="string",help="Beam type simulation (bunches etc.), beama or beamb")

parser.add_option("--regexp",          help="Use JDL RegExp, e.g. !(RegExp(\"in2p3.fr\", other.GlueCEInfoHostName))")
parser.add_option("--test",            help="Test run, do not submit jobs", action='store_true', default=False)

parser.add_option("--neutVersion",     help="Version of NEUT to be used", default='')
parser.add_option("--POT",             help="No. of POT to generate",     default='')
parser.add_option("--highlandVersion", help="Version of nd280Highland2",  default='')

(options,args) = parser.parse_args()

###############################################################################

# Main Program

filename  = options.filename
nd280ver  = options.version
prod      = options.prod
dtype     = options.type
jobtype   = options.job
evtype    = options.evtype
config    = options.config
extrafile = options.extrafile
modules   = options.modules
dirs      = options.dirs
resource  = options.resource
delegation= options.delegation
nsub      = options.nsub
queuelim  = options.queuelim
dbtime    = options.dbtime
generator = options.generator
geometry  = options.geometry
vertex    = options.vertex
beam      = options.beam
outdir    = options.outdir
regexp    = options.regexp

if not filename or not nd280ver or (prod and not dtype) or not jobtype or (jobtype != 'FlatTree' and not evtype) or (jobtype != 'MiniTree' and not evtype):
    parser.print_help()
    sys.exit(1)


prescale=1
if options.prescale:
    prescale = int(options.prescale)


if not outdir:
    outdir=os.getenv("ND280JOBS")
    if not outdir:
        outdir=os.getenv("PWD") + '/Jobs/'

    if prod:
        outdir+= '/' + prod+dtype
    else:
        outdir+= '/' + nd280ver


listfile=open(filename,'r')
filelist=listfile.readlines()
listfile.close()


username=os.getenv("USER")

## Check the output directory exsits, if not then create it.
if not os.path.isdir(outdir):
    print 'Making directory '+outdir
    os.makedirs(outdir)

tempconf='tempwms'
if nsub:
    tempconf += str(nsub)
tempconf += '.conf'


submit_command='time -p dirac-wms-job-submit '

#if delegation:
#    submit_command+='-d '+delegation
#else:
#    submit_command+='-a'
# TODO - soph - not sure about delegating long term proxies with dirac.. come back to this

#submit_command+=' -c '+tempconf+' -o '
#submit_command+=' -c autowms.conf -o '

counter   = 0
submitted = 0
miss      = 0
failures  = []

for f in filelist:
    counter += 1
    if counter%prescale > 0 and miss == 0:
        continue
    miss=0

    f=str(f.replace('\n',''))
    print f

    #Check proxy
    if not ND280GRID.IsValidProxy():
        print 'Proxy expired'
        break

    #Check validity of input file
    try:
        if not ND280GRID.ND280File(f):
            print 'Not a valid file, skipping'
            miss=1
            continue
    except:
        failures.append(f)

    #The default list of config options passed to ND280JDL
    optionsDict = {'regexp':regexp,'trigger':evtype,'prod':prod,'type':dtype,'modules':modules,'config':config,'dirs':dirs,'cfgfile':extrafile,'queuelim':queuelim,'dbtime':dbtime,'generator':generator,'geometry':geometry,'vertex':vertex,'beam':beam}

    #Is a version of NEUT to be used?
    if options.neutVersion:
        optionsDict ['neutVersion'] = options.neutVersion

        #How many POT?
        optionsDict ['POT'] = options.POT

    #Is a version of highland to be used?
    if options.highlandVersion:
        optionsDict['highlandVersion'] = options.highlandVersion

    #Create the JDL
    j = ND280JDL(nd280ver,f,jobtype,evtype,optionsDict)

    jdlname=j.CreateJDLFile(outdir)
    jidname=jdlname.replace('.jdl','.jid')

    #First delete any old jid and jdl file
    if os.path.isfile(jidname):
        print 'jid file exists, removing'
        fjid = open(jidname,"r")
        flines = fjid.readlines()
        if len(flines) > 1:
            joblink = flines[1]
            jar=joblink.split('/')
            jobout=jar[-1]
            jout=outdir + username + '_' + jobout
            if os.path.isfile(jout):
                print 'output file exists, removing'
                outdel = commands.getstatusoutput('rm -rf ' + jout)
                if outdel[0] != 0:
                    print 'Error: rm -rf ' + jout + ' failed'
        outdel = commands.getstatusoutput('rm -rf ' + jidname)
        if outdel[0] != 0:
            print 'Error: rm -rf ' + jidname + ' failed'

    command = submit_command + ' -f ' +jidname + ' ' + jdlname

    print command

    ii=0
    while ii < 1:

        if os.path.isfile(jidname):
            print 'jid written, do not submit again'
            break

        if options.test:
            print 'TEST RUN'
            break

        child=pexpect.spawn(command,timeout=300)
        ii=child.expect([pexpect.TIMEOUT,pexpect.EOF])

        if ii == 0:
            print 'Retrying ...'
        else:
            print child.before

        #Give the wms some time
        time.sleep(2)

    submitted += 1

    # sleep for a couple of hours to ease I/O burden...
    waitAfter = 2000
    if submitted == waitAfter:
        print 'Submitted %d jobs, taking a nap' % waitAfter
        time.sleep(7200)


print '--------------------------------'
print 'Submitted ' + str(submitted) + ' jobs'

if failures:
    print 'Dumping list of failures'
    print failures
