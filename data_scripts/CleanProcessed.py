#!/usr/bin/env python
"""
Clean Processed Data from T2:
"""

import os
import sys
from time import sleep
import ND280GRID
from ND280GRID import *
import optparse
from smtplib import SMTP
from datetime import datetime


# Parser Options:
parser = optparse.OptionParser(usage ="""\
usage: %prog [options]

       Clean/Archive Data in specified directory.

       RunND280Process leaves processed data on the SE attached to the CE it was
       processed on. This script allows for the removal of data from previous
       processing cycles, ensuring that any data to be deleted is first
       archived at RAL.

       Only processed data from current processing cycle should be present on T2

Example:
       $./CleanProcessed.py --fullpath /grid/t2k.org/nd280/production004/A/rdp/ND280/00004000_00004999 --fts 1 --filetags /anal/cali/cata""")
parser.add_option("--fts",          type="int",    help="Specify 1 (default) to use FTS 0 to use lcg-cr", default=1)
parser.add_option("--fullpath",     type="string", help="Specify path to files for cleanup e.g. --path /grid/t2k.org/nd280/mdc1")
parser.add_option("--skip",         type="string", help="'/' delimited list of files to skip T2 removal of e.g. reco/anal, can specify ALL")
parser.add_option("--filetags",     type="string", help="'/' delimited list of all file tags to archive/clean e.g. reco/cali/anal")
parser.add_option("--delete",       type="string", help="'/' delimited list of all file tags to delete e.g. cnfg/unpk/.txt")
parser.add_option("--T1",           type="string", help="Specify RAL (default) or TRIUMF", default='RAL')
parser.add_option("--noTRIUMFToRAL",type="int",    help="Do not copy replicas from TRIUMF to RAL!", default=1)
parser.add_option("--noRegDark",    type="int",    help="Skip any attempts to pick up unregistered replicas", default=0)
parser.add_option("--recipient",    type="string", help="send notification email to this recipient (default=nd280-grid@mailman.t2k.org)", default='nd280-grid@mailman.t2k.org')
(options,args) = parser.parse_args()


# Addresses for email updates:
sender    = 'j.perkin@shef.ac.uk'
recipient = options.recipient

## Input Data path:
if not options.fullpath:
    parser.print_help()
    sys.exit(1)

print 'Start time:',datetime.now()

deletables = []
if options.delete:
    for tag in options.delete.split('/'):
        deletables.append(tag)


## List of 'interesting' production directories to archive
if 'rdp' in options.fullpath or 'mcp' in options.fullpath or 'fpp' in options.fullpath:

    ## Directories (colon is consequence of recursive ls) we're interested in;
    ## User specified:
    if options.filetags:
        interesting=[]
        for tag in options.filetags.split('/'):
            interesting.append(tag+':')
    else:
        ## Production files are in the following:
        interesting=['anal:',
                     'cali:',
                     'cata:',
                     'cnfg:',
                     'controlsample:',
                     'controlsample/anal:',
                     'controlsample/reco:',
                     'elmc:',
                     'g4mc:',
                     'gnmc:',
                     'logf:',
                     'nucp:',
                     'numc:',
                     'reco:',
                     'unpk:']
else:
    ## Handle non production directories:
    ## Build a list of file paths (can be a bit time consuming
    ## - could be sped up for formatted production directories)
    print 'Non production, looking for interesting directories...'
    command = 'lfc-ls -R '+options.fullpath
    lines,errors = runLCG(command,in_timeout=7200) # increase timeout to 2 hrs
    if errors or not lines:
        print '\n'.join(errors)
        raise Exception('Failed to recursively list'+options.fullpath)

    ## Determine the data directories
    interesting=[]
    print 'Determining data directories from '+str(len(lines))+' file paths'
    for i in xrange(1,len(lines)-2):
        # previous line should be blank, this line ends with a ':' and first file in directory is interesting
        if  len(lines[i-1]) == 0 and lines[i].endswith(':') \
                and (lines[i+1].startswith('oa_')    or
                     lines[i+1].startswith('dq-')    or
                     lines[i+1].startswith('nd280_') or
                     lines[i+1].endswith  ('.txt')   or
                     any([ lines[i+1].endswith(tag) for tag in options.filetags.split('/')])
                     ):
            interesting.append(lines[i].replace(options.fullpath,'').lstrip('/'))
    print 'List of interesting directories', interesting

## Controlsamples may or may not have subdirectories, be greedy...
if 'controlsample:' in interesting:
    if 'controlsample/anal:' not in interesting : interesting.append('controlsample/anal:')
    if 'controlsample/reco:' not in interesting : interesting.append('controlsample/reco:')

## Skip any files? (overrides deletables):
skip_list=[]
if options.skip:
    for skip in options.skip.split('/'):
        print "Skipping "+skip+" removal"
        if skip!='ALL':
            skip_list.append('/'+skip)


## Failsafe for noRegDark - only allow if deleting and not copying...
if options.noRegDark:
    if options.delete != options.filetags:
        print '--noRegDark not permitted unless this is a deletion only process, i.e. list of deletables matches list of filetags!'
        print '--delete:  ',options.delete
        print '--filetags:',options.filetags
        sys.exit(1)


## Resource
resources = 'RAL','TRIUMF'
if options.T1 not in resources:
    print 'Invalid T1 resource'
    parser.print_help()
    sys.exit(1)
elif options.T1 == 'RAL':
    T1 = 'srm-t2k.gridpp.rl.ac.uk'
elif options.T1 == 'TRIUMF':
    T1 = 't2ksrm.nd280.org'


## Descend into directory:
os.system('clear')
command = "lfc-ls -R "+options.fullpath
print '\nCleaning '+options.fullpath+' data from T2\n'
print 'Descending into subdirectories (may take some time)\n'
## allow 2 hours
lines,errors = runLCG(command,in_timeout=7200)
if errors or not lines:
    print '\n'.join(errors)
    sys.exit('Unable to clear:'+options.fullpath)
filelist = lines


## Run until all T2 replicas are cleared:
is_cleared = False


## Keep track of repeats:
n_repeats = 0


## A dictionary of bools, one for each interesting directory (key)
## True (value) if cleared:
cleared_dict = {}


## Keep track of how many files we're waiting to transfer
n_files_copied = 0


## Keep track of FTS channels we're using
channel_list = []


## Email initiation of archiving process:
message = 'Archiving/Cleanup of '+options.fullpath+' '+'/'.join(interesting)+' to '+options.T1+' is underway.\n'
subject = 'From: '+recipient+'\nTo: '+recipient+'\nSubject:'

if options.filetags and options.skip and options.filetags == options.skip:
    subject +=' Parallelised '
    message  = 'Parallelised '+message

subject+='Archiving/Cleanup Notice\n\n'

if options.skip:
    message += 'Skipping T2 removal of '+repr(options.skip)+'\n'
if message:
    try:
        server = SMTP('localhost')
        server.sendmail(sender,[recipient],str(subject+message))
        server.quit()
    except:
        print 'Exception!: Notification email failed'
message = ''


try:
    ## Repeat until all T2 data cleared (wait for file transfers/registration):
    while is_cleared == False:

        print '\nIteration:'+str(n_repeats)
        print 'Archving interesting files:',repr(interesting)

        ## Keep track of failures
        failures = []

        ## Loop over files and look for the ones we're interested in...
        for listfile in filelist:
            for interest in interesting:
                if interest in listfile:

                    ## Check proxy is still valid
                    IsValidProxy()

                    ## The path of the interesting processed data
                    proc_path = 'lfn:'+rmNL(listfile.replace(':','/'))
                    proc_path = proc_path.rstrip('/')
                    print 'proc_path: '+proc_path

                    ## Add this interesting directory to dictionary
                    ## (first pass only)
                    if n_repeats == 0 and 'lfn:' in proc_path:
                        print 'Adding '+proc_path+' to dictionary'
                        cleared_dict[proc_path]=False
                    print 'Dumping dictionary:',cleared_dict

                    ## Construct log file name for RegDarkData subprocesses
                    reg_log = transfer_dir= os.getenv("ND280TRANSFERS")+'/clean_'+proc_path.replace('lfn:/grid/t2k.org/nd280/','').replace('/','_')+'.'+options.T1+'.reg.log'

                    ## First register any T1 dark data in this directory
                    if not options.noRegDark:
                        command = 'nice ./RegDarkData.py -l '+proc_path+' '+T1+' >'+reg_log+' 2>/dev/null'
                        print 'Trying '+command
                        print datetime.now()
                        os.system(command)
                        print datetime.now()

                    ## Create an ND280Dir object for folder containing processed
                    ## data:
                    print 'Creating ND280Dir object for '+proc_path
                    proc_dir = ND280Dir(proc_path,skipFailures=True,ls_timeout=3600)

                    ## ignore empty directories!
                    lines,errors = runLCG('lfc-ls '+proc_path.replace('lfn:',''))
                    if lines and not proc_dir.ND280Files:

                        ## abort if ND280Dir instance is empty
                        raise Exception('Could not find files in '+proc_path+'!')

                    ## Reset last file flag:
                    is_last_file = False

                    ## If no replicas in this directory, it is cleared
                    print 'Examining files in '+proc_dir.dir
                    if not len(proc_dir.ND280Files):
                        cleared_dict[proc_path]=True
                    print cleared_dict

                    ## Keep track of unwanted replicas and FTS transfers
                    unwanted_replicas = []

                    ## Loop over the files:
                    for proc_file in proc_dir.ND280Files:
                        print 'Checking '+proc_file.alias

                        ## check proxy
                        IsValidProxy()


                        ## Is deletion of this file to be skipped?
                        if options.skip=='ALL': is_to_skip = True
                        else:
                            is_to_skip = False
                            for skip in skip_list:
                                if skip in proc_file.alias:
                                    is_to_skip = True
                                    print 'Skipping deletion of '+proc_file.alias

                        ## Is it a deletable?
                        is_deletable = False
                        if not is_to_skip:
                            for deletable in deletables:
                                if deletable in proc_file.alias:
                                    is_deletable = True
                                    print 'Deletable '+proc_file.alias

                        ## Really don't ever want to copy non-production, i.e.
                        ## /grid/t2k.org/nd280/v* from TRIUMF to RAL, essential to
                        ## pick these up from T2
                        is_to_copy = True
                        if 't2k.org/nd280/v' in proc_file.alias or 't2k.org/nd280//v' in proc_file.alias:
                            ## Ignore replicas at TRIUMF and .txt files
                            for proc_srm in proc_file.reps:
                                if 't2ksrm.nd280.org' in proc_srm or T1 in proc_srm or '.txt' in proc_file.alias:
                                    is_to_copy = False
                        if not is_to_copy:
                            print 'Will not copy '+proc_file.alias

                        ## Is this the last file? (use to force runFTSMulti() to submit transfer)
                        if proc_file.filename == proc_dir.last_file_name:
                            is_last_file = True
                            print proc_file.filename+' is last file'

                        ## Ignore deletion of files from triumf/westgrid processing unless filetags matches delete:
                        if 'triumf' in proc_file.filename or 'westgrid' in proc_file.filename:
                            if options.filetags != options.delete:
                                print 'Ignoring deletion of '+proc_file.filename
                                is_to_skip   = True
                                is_deletable = False
                                if not is_last_file: is_to_copy = False
                            else:
                                if is_deletable:
                                    print 'Deleting TRIUMF copy of '+proc_file.filename

                        ## Blank stdout, stderr buffers
                        lines  = []
                        errors = []

                        ## Is file at T1?
                        if ((not proc_file.OnSRM(T1) and is_to_copy) or (is_last_file and options.fts and n_files_copied)) and not is_deletable:

                            ## If not copy it there:
                            source_surl   = proc_file.GetRepSURL()
                            print 'Source SURL = '+source_surl

                            ## as long as it isn't an unwanted TRIUMF-RAL replication
                            if 't2ksrm.nd280.org' in source_surl and options.noTRIUMFToRAL:
                                print 'Will not copy '+proc_file.filename+' from TRIUMF to RAL'
                            else:
                                print 'Copying '+proc_file.filename+' to '+T1

                                if options.noRegDark:
                                    print 'Alert!: Overriding noRegDark==1'
                                    options.noRegDark = 0

                                    # should never reach CopySRM if options.filetags == options.delete
                                    # if we did, something went wrong
                                    if options.delete == options.filetags:
                                        message = 'Error!: should not invoke CopySRM if filetags == delete'
                                        print message
                                        raise Exception(message)
                                try:
                                    ## Append PID to fts transfer file name here
                                    proc_file.CopySRM(T1,options.fts,is_last_file,os.getpid())
                                except:
                                    print proc_file.alias,'.CopySRM() failed'
                                    failures.append(proc_file.filename)

                                ## Record FTS channel usage
                                source_se     = GetSEFromSRM(source_surl)
                                print 'Source SE = '+source_se
                                if source_se in se_channels and T1 in se_channels:
                                    # fts_channel = se_channels[source_se]+'-'+se_channels[T1]
                                    fts_channel = [source_se,T1]
                                    if not fts_channel in channel_list:
                                        print 'Appending '+repr(fts_channel)+' to FTS channel list for monitoring'
                                        channel_list.append(fts_channel)

                                ## Count copies, (don't count forced [runFTS] copies)
                                if not is_last_file:
                                    n_files_copied += 1
                                    print str(n_files_copied)+' files copied so far'

                                ## If this was a forced copy and the file is deletable,
                                ## delete all instances now
                                if is_deletable:
                                    print 'Deleting '+proc_file.alias
                                    command = 'lcg-del -v --vo t2k.org -a '+proc_file.alias
                                    lines,errors = runLCG(command)

                        ## File is at T1
                        elif proc_file.OnSRM(T1) or is_deletable:

                            ## Skip T2 deletion?
                            if is_to_skip:
                                print 'Skipping T2 deletion of '+proc_file.alias
                                continue


                            ## Is it deletable?
                            if is_deletable:
                                print 'Deleting all replicas of '+proc_file.alias
                                command = 'lcg-del -v --vo t2k.org -a '+proc_file.alias
                                lines,errors = runLCG(command)
                            else:
                                print proc_file.filename+' is at '+T1
                                print 'Deleting any T2 replicas of '+proc_file.alias+'...'
                                ## Delete T2 replicas only
                                for proc_srm in proc_file.reps:

                                    ## Ignore replicas at TRIUMF and RAL
                                    if 't2ksrm.nd280.org' in proc_srm or 'srm-t2k.gridpp.rl.ac.uk' in proc_srm:
                                        continue
                                    else:
                                        ## Delete
                                        print 'Deleting '+proc_srm
                                        command = 'lcg-del -v --vo t2k.org '+proc_srm
                                        lines,errors = runLCG(command)


                        ## File failed to copy
                        else:
                            if is_to_copy:
                                print 'Failed to copy file: '+proc_file.filename
                            print 'Hmmm, did not want to copy '+proc_file.filename


                        ## Handle lcg-del errors
                        if errors:
                            print 'lcg-del Error!'
                            print repr(errors)
                            ## Unregister files with invalid path
                            if 'SRM_INVALID_PATH' in errors[-1]:
                                print 'Unregistering file with SRM_INVALID_PATH'
                                for proc_srm in proc_file.reps:
                                    try:
                                        command = 'lcg-uf --vo t2k.org -f '+proc_file.guid+' '+proc_srm
                                        runLCG(command)
                                    except:
                                        print 'Exception!'
                                        if not proc_srm in unwanted_replicas:
                                            print 'Adding '+proc_srm+' to unwanted_replicas'
                                            unwanted_replicas.append(proc_srm)

                            ## Re-register and then delete files with
                            ## 'no such file or directory'
                            elif 'No such file' in errors[-1] or 'SRM_AUTHORIZATION_FAILURE' in errors[-1]:
                                print 'Re-registering and then deleting file'
                                for proc_srm in proc_file.reps:
                                    try:
                                        command = 'lcg-rf --vo t2k.org -g '+proc_file.guid+' '+proc_srm
                                        runLCG(command)
                                        se = proc_srm.replace('srm://','').split('/')[0]
                                        command = 'lcg-del --vo t2k.org --se '+se+' '+proc_file.guid
                                        runLCG(command)
                                    except:
                                        print 'Exception!'
                                        if not proc_srm in unwanted_replicas:
                                            print 'Adding '+proc_srm+' to unwanted_replicas'
                                            unwanted_replicas.append(proc_srm)
                            ## If file persists, add to list of unwanted replicas
                            else:
                                print 'File persists.'
                                for proc_srm in proc_file.reps:
                                    if not proc_srm in unwanted_replicas:
                                        print 'Adding '+proc_srm+' to unwanted_replicas'
                                        unwanted_replicas.append(proc_srm)


                    ## If there are no transfers and all T2 replicas are deleted
                    ## then data is cleared from this directory, update
                    ## dictionary:
                    print 'Checking if '+proc_path+' is clear...'
                    if not n_files_copied:
                        if not len(unwanted_replicas):
                            print proc_path + ' Cleared!'
                            cleared_dict[proc_path]=True
                        else:
                            message = 'List of unwanted replicas:' + repr(unwanted_replicas)
                            if failures:
                                message += 'List of failures:' +repr(failures)
                            print 'Exception: '+message
                            raise Exception(message)
                    else: print 'Nope.'


        ## If all T2 data from all interesting directories is deleted
        ## T2 data is cleared
        print 'Checking if all T2 replicas are deleted...'
        if not False in cleared_dict.values():
            print 'Dumping directory dictionary:'
            print cleared_dict
            is_cleared = True
        else: print 'Nope.'


        ## Wait for FTS transfers
        if not is_cleared:
            print 'Waiting for FTS...'
            while(1):
                n_active = 0

                # FTS3 ---
                for source,dest in channel_list:
                    transfers,statuses = GetActiveTransferList(source,dest)

                    for t in transfers:
                        active,failed,finished = GetTransferStatus(t,source,dest)

                        # make sure the transfer query succeeded
                        if type(active) is int:
                            n_active += active
                        # otherwise add large number to ensure loop persists
                        else:
                            n_active += 100

                if n_active < 20:
                    break
                sleep(60)

        ## Increment counter
        n_repeats += 1

        ## Any failures?
        if failures:
            message = 'List of failures:\n'
            message += '\n'.join(failures)
            print message

        ## Abort ?
        if n_repeats > 9:
            ## Was T2 replica deletion enabled?
            if len(skip_list) or options.skip=='ALL':
                message = 'T2 '+options.fullpath+' data archving iterated '+str(n_repeats)+' times\n'
                print message
                break
            ## If not, T2 replicas should have cleared
            else:
                message = 'Data not cleared/archived in 10 iterations, ABORTING!'
                print 'Exception: '+message
                raise Exception(message)

        ## Reset counter
        n_files_copied = 0
except:
    ## Exception thrown
    message = 'Archving/Cleanup of '+options.fullpath+' failed with exception : '+traceback.format_exc()
else:
    ## Finished, handle possible outcomes
    if is_cleared:
        message = 'Success!: All T2 '+options.fullpath+' data cleared/archived in '+str(n_repeats)+' iterations... registering files'
    else:
        if not len(skip_list):
            if len(cleared_dict):
                message = 'T2 '+options.fullpath+' data did not clean/archive:\n'+repr(cleared_dict)
            else:
                message = 'T2 '+options.fullpath+' data cleanup/archiving: script had nothing to do.'


## Email outcome
if message:
    message = 'Archiving/Cleanup @ '+options.T1+'\n'+message
    if failures:
        message += 'List of failures:\n'
        message += '\n'.join(failures)
    print message
    footer  = '\n Log will appear in http://www.hep.shef.ac.uk/people/perkin/t2k_logs/cleanup/ within 24hrs.\n'
    try:
        server = SMTP('localhost')
        server.sendmail(sender,[recipient],str(subject+message+footer))
        server.quit()
    except:
        print 'Exception!: Notification email failed'


print 'Finish time:',datetime.now()

if options.noRegDark:
    sys.exit(0)

## Register any recently copied T1 data:
print 'Registering recently copied data'
for listfile in filelist:
    for interest in interesting:
        if interest in listfile:
            proc_path = 'lfn:'+rmNL(listfile.replace(':','/'))
            command = './RegDarkData.py -l '+proc_path+' '+T1+' >/dev/null 2>&1 &'
            print 'Retrying '+command
            os.system(command)

## End of program
sys.exit(0)
