#!/usr/bin/env python 

import optparse
from ND280GRID import ND280JID, runLCG
import os
import sys
import commands
import time
import pexpect

#Parser options
parser = optparse.OptionParser()

#Mandatory (should be args not options!)
parser.add_option("-e","--evtype", dest="evtype", type="string",help="[mandatory] Event type, spill or cosmic")
parser.add_option("-o","--outdir", dest="outdir", type="string",help="[mandatory] Output directory path")
parser.add_option("-v","--version",dest="version",type="string",help="[mandatory] Version of nd280 software to install")
parser.add_option("-p","--prod",   dest="prod",   type="string",help="[mandatory] Production, e.g. 4A")

#Optional
parser.add_option("-j","--job",  dest="job",  default='Raw',help="Job type, Raw, Custom, MC")
parser.add_option("-r","--runno",dest="runno",default='',   help="Run number, or start of - used for listing")

(options,args) = parser.parse_args()

###############################################################################

# Main Program
version  = options.version
prod     = options.prod
job      = options.job
evtype   = options.evtype
runno    = options.runno
outdir   = options.outdir

if not version or (evtype!="spill" and evtype!="cosmic") or not outdir:
    parser.print_help()
    sys.exit(1)

basename=''
if job == 'Raw' or job == 'MC':
    basename = 'ND280' + job + '_' + evtype
elif job == 'Custom':
    basename = 'ND280' + job

set=''
if runno:
    set = runno[0]

username=os.getenv("USER")

#if prod:
#    outdir+= '/' + prod
#else:
#    outdir+= '/' + version

## Check the output directory exists, if not then exit
if not os.path.isdir(outdir):
    sys.exit('The directory ' + outdir + ' does not exist.')

lfnbase = 'lfn:/grid/t2k.org/nd280/raw/ND280/ND280/'

nameend=''
vflag=version
if prod:
    vflag = prod
if set and not runno:
    vflag += '_' + set
if runno:
    nameend=vflag + '_' + job + '_' + evtype + '_' + runno + '.list'
else:
    nameend=vflag + '_' + job + '_' + evtype + '.list'

#Write file with unclear runs
unclear_filename = 'unclear_runs_' + nameend
rmunclear = commands.getstatusoutput('rm -rf ' + unclear_filename)
unclear_out = open(unclear_filename,'w')

#Write file with failed runs
failed_filename = 'failed_runs_' + nameend
rmfailed = commands.getstatusoutput('rm -rf ' + failed_filename)
failed_out = open(failed_filename,'w')

#Write file with OK runs
OK_filename = 'ok_runs_' + nameend
rmok = commands.getstatusoutput('rm -rf ' + OK_filename)
OK_out = open(OK_filename,'w')


#Look at the job output we already have
#-----------------------------------------------------------
print 'Loop over job outputs...'

command= 'ls -d ' + outdir + '/' + username + '_*' 
lines,errors = runLCG(command,is_pexpect=False)

midnames = []
jidnames = []

jcounter = 0
for l in lines:
    l = l.replace('\n','')
    command = 'ls ' + l + '/'+job+'_*.cfg'
    lines,errors = runLCG(command,is_pexpect=False)
    ll           = lines
    if len(ll) == 0:
        continue
    lll=ll[0].replace('\n','')
    llar=lll.split('/')                
    cfgname=llar[-1]
    jname=cfgname.replace('_' + version,'')
    jname=jname.replace(job,basename+'_'+version)
    jname=jname.replace('cfg','jid')
    jidnames.append(jname)

    midname=jname.replace(basename+'_','nd280')
    midname=midname.replace(version,'')
    midname=midname.replace('jid','daq.mid.gz')
    midnames.append(midname)

    jcounter += 1
    
#Loop over jid files and get output
#----------------------------------------------------------------
print 'Loop over jid files...'

command = 'ls ' + outdir + '/'+basename + '_' + version 
if runno:
    command += '_0000' + runno + '*.jid'
else:
    command += '*.jid'
lines,errors = runLCG(command,is_pexpect=False)

print command

smidnames = []

dcounter = 0
allcounter = 0
unclear = 0
for l in lines:
    allcounter += 1

    l = l.replace('\n','')

    #Skip if we already downloaded
    lar=l.split('/')                
    jidname=lar[-1]
    midname=jidname.replace(basename+'_','nd280')
    midname=midname.replace(version,'')
    midname=midname.replace('jid','daq.mid.gz')
    smidnames.append(midname)

    set = midname[10]
    dataset = '0000' + set + '000_0000' + set + '999'
    
    gotit=0
    for item in jidnames:
        if jidname == item:
            gotit = 1
    if gotit == 1:
        continue
    
    #Get job output
    fjid = open(l,"r")
    flines = fjid.readlines()
    joblink = flines[1]
    print joblink

    #command = 'glite-wms-job-output --dir ' + outdir + ' ' + joblink
    command = 'dirac-wms-job-get-output -f ' + self.jidfilename + ' --Dir ' + outdir

    ii=0
    timeouts = 0
    while ii == 0:
        child = pexpect.spawn(command,timeout=20)
        #ii=child.expect([pexpect.TIMEOUT,'Error','ABORTED',pexpect.EOF])
        ii = child.expect([pexpect.TIMEOUT, 'Error', pexpect.EOF])
        # soph - dirac returns Error in the case you feed it rubbish
        # soph - and it returns Error if the job was killed
        #
        #if ii == 3:
        if ii == 2:
            dcounter += 1
            print child.before
            time.sleep(1)
        #elif ii == 1 or ii == 2:
        elif ii == 1:
            jj=child.expect([pexpect.EOF,'.* : '])
            # soph - TODO - dont know what situation causes you to write 'n' ?
            # soph - so hard to work out what the dirac equivalent is... no files to test on
            if jj == 1:
                child.sendline('n')
            print 'Error' + child.before
            unclear_out.write(lfnbase + dataset + '/' + midname + '\n')
            unclear += 1
        else:
            print 'Timeout!'
            timeouts += 1
            if timeouts == 10:
                ii = 1
                unclear_out.write(lfnbase + dataset + '/' + midname + '\n')
                unclear += 1


#Look at all the job output
#-------------------------------------------------------
print 'Loop over all job output files...'

#command = 'ls -d ' + outdir + '/' + username + '_*'
# soph - dirac doesnt put your username in the output folder name
command = 'ls -d ' + outdir + '/' + username + '_*'

lines,errors = runLCG(command,is_pexpect=False)


print command

#Look at the job outputs
fcounter = 0
ok       = 0
failed   = 0
for l in lines:
    this_ok = 0
    l = l.replace('\n','')
    ll = l + '/ND280'+job+'.out'

    command = 'ls ' + l + '/'+job+'_*.cfg' 
    lines,errors = runLCG(command,is_pexpect=False)
    fn           = lines
    if len(fn) == 0:
        print 'No cfg file'
        continue
    
    fnl=fn[0].replace('\n','')
    fnar=fnl.split('/')                
    cfgname=fnar[-1]
    jname=cfgname.replace('_' + version,'')
    jname=jname.replace(job,basename+'_'+version)
    jname=jname.replace('cfg','jid')
    midname=jname.replace(basename+'_','nd280')
    midname=midname.replace(version,'')
    midname=midname.replace('jid','daq.mid.gz')
    fmidname=lfnbase + dataset + '/' + midname

    if os.path.isfile(ll):
        fout = open(ll,"r")
        flines = fout.readlines()
        
        for fline in flines:
            if 'Finished OK' in fline:
                this_ok = 1
                                
        if this_ok == 1:
            OK_out.write(fmidname + '\n')
            ok += 1
        else:
            failed_out.write(fmidname + '\n')
            failed += 1
    else:
        unclear_out.write(fmidname + '\n')
        unclear += 1
        
    fcounter += 1


#-------------------------------------------------------------
print 'Downloaded ' + str(dcounter)               + ' jobs'
print str(fcounter) + ' jobs finished out of '    + str(allcounter)
print str(ok)       + ' OK runs written to '      + OK_filename
print str(failed)   + ' failed runs written to '  + failed_filename
print str(unclear)  + ' unclear runs written to ' + unclear_filename
print 'Checksum '   + str(unclear + failed + ok)  + ' ' + str(allcounter)

