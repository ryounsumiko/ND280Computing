#!/usr/bin/env python2

"""
A bunch of handy commands for use with the ND280 software
on the grid or locally. The object allows one to list
information of packages, disable packages and install software.
"""
import sys
import os
import glob
from datetime import datetime
from time import time
# import smtplib
# from email.MIMEText import MIMEText
# import optparse
# import shutil
# import stat
# import re
# import tempfile

import ND280GRID
# from ND280GRID     import ND280Dir
from ND280GRID import ND280File
# from ND280GRID     import rmNL
from ND280GRID import runLCG
from ND280Configs import ND280Config
from ND280Software import ND280Software


class ND280Job(object):
    """ Base class for all types of ND280 Job: Raw data, beam MC etc etc"""

    def __init__(self, nd280ver):
        self.input           = ''
        self.highlandVersion = ''
        self.neutVersion     = ''
        self.useTestDB       = False
        self.nd280ver        = nd280ver
        self.t2ksoftdir      = ND280GRID.GetT2KSoftDir()
        self.base            = os.getcwd()
        self.software        = ND280Software(nd280ver)
        if os.getenv("SITE_NAME"):
            self.sitename = os.getenv("SITE_NAME")
            self.sitename = self.sitename.replace('UKI-','')
            self.sitename = self.sitename.lower()
        else:
            self.sitename = ''

        # Unless every instance of voms -> dirac has been checked,
        # set dirac to be true here and change it manually if need
        # to use false otherwise
        # self.dirac = True

        ## Copy vector file to working directory for respins
        self.localVector = ''

        ## Common config files
        self.config_options={'cmtpath':'environment','cmtroot':'environment','nd280ver':nd280ver}

        ## Blank dictionary of custom_list options, to be filled later...
        self.custom_list_dict = {}


    ########################################################################################################################
    def RunCommand(self,in_command):

        sys.stdout.flush()
        print datetime.now()
        print 'RunCommand():\n'+in_command

        """ Source the required setups before executing local commands """
        instDir = self.t2ksoftdir + '/nd280' + self.nd280ver + '/'
        command='umask 002\n'

        ## use standard path to CMT setup script on CVMFS
        if os.path.exists(os.getenv('VO_T2K_ORG_SW_DIR')+'/CMT'):
            cmtSetupScr=os.getenv('VO_T2K_ORG_SW_DIR')+'/CMT/v1r20p20081118/mgr/setup.sh'
        else:
            cmtSetupScr=instDir + 'CMT/setup.sh'

        if os.path.isfile(cmtSetupScr):
            command += 'source ' + cmtSetupScr + '\n'
        else:
            raise self.Error('Could not find the CMT setup script ' + cmtSetupScr)

        ## source the 'global' nd280 setup script
        ## not required for highland or if using cmtpathPrepend option
        gblSetupScr=instDir + 'setup.sh'
        if self.highlandVersion:
            print 'Skipping %s for highland' % (gblSetupScr)

        ## cmtpathPrepend?
        if 'custom_list' in self.config_options and 'cmtpathPrepend' in self.custom_list_dict:
            print 'Prepending CMTPATH with %s' % self.custom_list_dict['cmtpathPrepend']

            if not os.path.exists(self.custom_list_dict['cmtpathPrepend']):
                raise  self.Error('%s does not exist' % self.custom_list_dict['cmtpathPrepend'])

            command += 'export CMTPATH=%s:$CMTPATH\n' % self.custom_list_dict['cmtpathPrepend']

            ## also need to source setup script in associated module in order to fix PATH and LD_LIBRARY_PATH...
            ## look for setup script in the prepended folder first
            if os.path.isfile(self.custom_list_dict['cmtpathPrepend']+'/setup.sh'):
                prepend_cmt_folder = self.custom_list_dict['cmtpathPrepend']
            ## otherwise find the module associated with the prepended folder
            else:
                prepend_cmt_folder = glob.glob(self.custom_list_dict['cmtpathPrepend']+'/*/*/cmt')[0]
            print 'Need to source setup script in %s' % (prepend_cmt_folder)
            command += 'source %s/setup.sh\n' % (prepend_cmt_folder)

        ## the default setup script
        else:
            if os.path.isfile(gblSetupScr):
                command += 'source ' + gblSetupScr + '\n'
            else:
                raise self.Error('Could not find the setup script ' + gblSetupScr)

        ## sometimes the software installs in the wrong location because
        ## the underlying linux kernel query returns the wrong system type,
        ## make sure CMT knows where to look for the software
        for sysType in 'Linux-x86_64', 'amd64_linux26', 'ND280GRIDBinaries':
            if os.path.exists(instDir + 'nd280/' + self.nd280ver + '/' + sysType):
                print 'Setting CMTCONFIG to '+sysType
                command+='export CMTCONFIG='+sysType+'\n'

        ## Add ENV_TSQL_URL setting here
        if self.useTestDB:
            sql_cascade  = 'export ENV_TSQL_URL=\"mysql://trcaldb.t2k.org/testnd280calib;mysql://dpnc.unige.ch/nd280calib\;mysql://trbsddb.nd280.org/t2kbsd"\n'
            sql_cascade += 'export ENV_TSQL_USER=\"t2kcaldb_reader;t2kcaldb_reader;t2kbsd_reader\"\n'
            sql_cascade += 'export ENV_TSQL_PSWD=\"rdt2kcaldb;rdt2kcaldb\"\n'
        else:
            sql_cascade  = 'export ENV_TSQL_URL=\"mysql://dpnc.unige.ch/nd280calib;mysql://trbsddb.nd280.org/t2kbsd\"\n'
            sql_cascade += 'export ENV_TSQL_USER=\"t2kcaldb_reader;t2kbsd_reader\"\n'
            sql_cascade += 'export ENV_TSQL_PSWD=\"rdt2kcaldb;rdt2kcaldb\"\n'

        command += sql_cascade

        # TMI?
        #         command += 'echo CMTPATH is $CMTPATH\necho CMTROOT is $CMTROOT\necho CMTCONFIG is $CMTCONFIG\n'
        #         command += 'echo PATH=$PATH\n'
        #         command += 'echo LD_LIBRARY_PATH=$LD_LIBRARY_PATH\n'
        #         command += 'echo TSQL settings are $(env | grep TSQL)\n'
        #         command += 'echo DUMPING ENV:\nenv\n'
        command += in_command

        return os.system(command)

    class Error(Exception):
        pass

    ###########################################################################
    def TestCopy(self, dirBegin='', dirEnd='', dirSuff='', srm=''):
        """
        Function that performs a test copy to the log file
        directory associated with the job.
        If the test copy fails then the job exits and returns an error.
        """
        sys.stdout.flush()
        print 'TestCopy'

        if not ND280GRID.IsValidProxy():
            sys.exit('No valid proxy!')

        # Construct logical file name for test copy
        lfn = dirBegin + '/logf'
        if dirSuff: lfn += dirSuff             # append a _suffix to logf?
        lfn += '/' + dirEnd                    # append a subdirectory?
        lfn=lfn.replace('//','/').rstrip('/')  # remove extraneous //

        # Make sure we're in the working directory for the job
        os.chdir(self.base)

        # Create a test file, incorporating a timestamp into the filename
        timeStamp = str(int(time()*100))
        testName  = "file" + timeStamp + ".txt"
        testFile  = open(testName,'w')
        for i in xrange(100000):
            testFile.write('testing 123\n')
        testFile.close()

        ## First make sure file doesn't already exist
        command = 'lfc-ls ' + lfn.replace('lfn:','') +'/' + testName
        if not os.system(command):
            command = 'lcg-del -a ' + lfn + '/' + testName
            lines,errors=runLCG(command)

        ## Copy and register
        testFile = ND280GRID.ND280File(testName)
        if not testFile.Register(lfn+'/', srm):
            print 'Not able to register %s !' % testName
            sys.exit(1)

        ## Then delete
        command = 'lcg-del -a ' + lfn + '/' + testName
        lines,errors = runLCG(command)
        if errors:
            print '\n'.join(errors)
            sys.exit(1)

        return 0

    def CopyAll(self, dir_prot, dir_end='', dir_list=[], dirsuff='', srm=''):
        sys.stdout.flush()
        print 'CopyAll'

        try:
            print 'CE='+os.getenv("CE_ID")
        except:
            print 'Unable to identify CE'

        print 'Listing directory contents...'
        lines,errors = runLCG('ls -lh',is_pexpect=False)
        print '\n'.join(lines+errors)

        self.CopyConfFile       (dir_prot, dir_end, dirsuff, srm)
        self.CopyLogFile        (dir_prot, dir_end, dirsuff, srm)
        self.CopyCatalogueFiles (dir_prot, dir_end, dirsuff, srm)
        self.CopyRootFiles      (dir_prot, dir_end, dir_list, dirsuff, srm)

        return 0

    def CopyLogFile(self, dir_prot, dir_end='', dirsuff = '', srm=''):
        """ Copy the log file. """

        sys.stdout.flush()
        print 'CopyLogFile'

        copy_dir = 'logf'
        if dirsuff:
            copy_dir += dirsuff
        curr_export_dir = dir_prot + '/' + copy_dir + '/' + dir_end
        curr_export_dir = curr_export_dir.replace('//','/')

        os.chdir(self.base)

        for log_file in glob.glob('*.log'):
            f = ND280File(log_file)
            # if not f.Register(curr_export_dir,srm):  # soph-quick-dirty-dfc-fix
              #   sys.exit('Log file missing from output')  # soph-quick-dirty-dfc-fix
            f.Register(curr_export_dir,srm) #:  # soph-quick-dirty-dfc-fix

        return 0

    def CopyConfFile(self, dir_prot, dir_end='', dirsuff = '', srm=''):
        """ Copy the cfg file. """

        sys.stdout.flush()
        print 'CopyConfFile'

        copy_dir = 'cnfg'
        if dirsuff:
            copy_dir += dirsuff
        copy_type = '.cfg'
        curr_export_dir = dir_prot + '/' + copy_dir + '/' + dir_end
        curr_export_dir = curr_export_dir.replace('//','/')

        # soph-quick-dirty-dfc-fix
        # remove this whole block and reqrite in dfc at some point
        ##Check if a cfg file is already saved
        #command="lfc-ls "+curr_export_dir.replace('lfn:','')
        #lines,errors=runLCG(command)
        #for line in lines:
        #    if copy_type in line:
        #        print 'Conf file already stored on LFN'   # soph-quick-dirty-dfc-fix
        #        return 0     # soph-quick-dirty-dfc-fix

        #If not, upload a file
        os.chdir(self.base)
        #command = "ls *.cfg"
        #lines,errors=runLCG(command,is_pexpect=False)
        #copy_ok=''
        if dirsuff:
            copy_dir += dirsuff
        #for line in lines:
        #    if copy_type in line:
        #        curr_file=ND280File(rmNL(line))
        #        copy_ok=curr_file.Register(curr_export_dir,srm)
        #if not copy_ok:
        #    print "File type "+copy_type+" missing from output or could not be stored"

        for file_name in glob.glob('*.cfg'):
            f = ND280File(file_name)
            if not f.Register(curr_export_dir,srm):
                print 'File type %s missing from output or could not be stored' % (copy_type)
        return 0

    def TarCatalogueFiles(self,tar_prot=''):
        """ tar the catalogue files into one tar file. Can be used to create a common tar file name to copy back in the output sandbox. """

        sys.stdout.flush()
        print 'TarCatalogueFiles'

        if not tar_prot:
            os.chdir(self.base)
            tar_prot = glob.glob('oa_*.dat')[0][0:28]

        os.chdir(self.base)
        command = "tar -zcvf " + tar_prot + ".tar.gz *.dat"
        if os.system(command):
            raise self.Error('Tarring of the catalogue files failed')
        return tar_prot + '.tar.gz'

    def CopyCatalogueFiles(self, dir_prot, dir_end='', dirsuff='', srm=''):
        """ Tar and copy the catalogue files. """

        sys.stdout.flush()
        print 'CopyCatalogueFiles'

        os.chdir(self.base)

        tar_prot = glob.glob('oa_*.dat')[0][0:28]
        tarfile_name=self.TarCatalogueFiles(tar_prot)

        curr_dir = dir_prot + '/cata'
        if dirsuff:
            curr_dir += dirsuff
        curr_dir += '/' + dir_end

        curr_dir = curr_dir.replace('//','/')

        ## Copy across catalogue '*.dat' files
        tarfile=ND280File(tarfile_name)
        tarfile.Register(curr_dir,srm)
        return 0

    #################################################
    def LogFileCheck(self):
        """ Perform basic check on the Log file """

        sys.stdout.flush()
        print 'LogFileCheck'

        os.chdir(self.base)

        for file_name in glob.glob('oa_*.log'):
            if '_logf_' in file_name:
                log_name = file_name
                break

        log_lines = open(log_name,'r').readlines()

        for l in log_lines:
            for diedBy in 'FATAL ERROR','Uncaught exception in','Disabling module BeamSummaryData','Segmentation fault':
                if diedBy in l:
                    print '%s detected in %s' % (diedBy, log_name)
                    print ''.join(log_lines)
                    return 1

        return 0


    def CopyRootFiles(self,dir_prot, dir_end='', dir_list=[], dirsuff='', srm=''):
        """ Copy and register the root files """

        sys.stdout.flush()
        print 'CopyRootFiles'
        print dir_list

        os.chdir(self.base)
        filelist  = os.listdir(os.getcwd())

        # Get the list of ROOT files, ignoring any NEUT/GENIE geometry files as these also have the
        # _numc_ or _gnmc_ tag, so can corrupt the {stage:filename} dictionary
        rootfiles = [ f for f in filelist if f.endswith('.root') and not f.endswith('.geo.root')]
        print 'ROOT files in '+self.base +':'
        print '\n'.join(rootfiles)

        # Create a file dictionary of {stage:filename}
        filedict = {}
        for f in rootfiles:
            filedict[f.split('_')[5]] = f

        # Check that all the files to upload are present
        filetags = filedict.keys()
        missing = [t for t in dir_list if t not in filetags]
        #if missing:
            # sys.exit('ROOT file(s):'+' '.join(missing)+' missing from output') #soph-quick-dirty-dfc-fix

        #Copy files to GRID
        for stage,filename in filedict.iteritems():

            # be careful not to pick up files (like the input) not in the dir_list
            if stage not in dir_list or filename == self.input.filename:
                continue

            # define the LFC path for the root file to upload
            curr_export_dir = dir_prot + '/' + stage

            # append a suffix?
            if dirsuff: curr_export_dir += dirsuff

            # append another directory?
            curr_export_dir += '/' + dir_end

            # remove any extraneous double slashes
            curr_export_dir = curr_export_dir.replace('//','/')

            # create a file instance and register
            curr_file = ND280File(filename)
            copy_ok   = ''
            copy_ok   = curr_file.Register(curr_export_dir,srm,timeout=1800)

            # should remove all output if there is a failure...
            #if not copy_ok:
                # sys.exit("ROOT file "+filename+" failed lcg-cr")  #soph-dfc-quick-dirty-fix
        return 0


    def LocateVectorFile(self,vectorPath=''):

        sys.stdout.flush()
        print 'LocateVectorFile()'
        print 'This is a '+self.input.GetStage()+' respin!'

        if vectorPath:
            vectorDir    = vectorPath
            command      = 'lfc-ls '+vectorDir
            lines,errors = ND280GRID.runLCG(command)

            ## If there are files in this directory, try and
            ## locate the correct one
            vectors    = [l for l in lines if self.input.GetRunNumber()+'-'+self.input.GetSubRunNumber()+'_'+self.input.GetFileHash() in l]
            vectorName = vectors[0]

        else:
            inputPath = self.input.alias.replace('//','/')
            production,respin = inputPath.split('/')[4:6]

            ## Look in production respin folders prior to this one
            command = 'lfc-ls /grid/t2k.org/nd280/'+production
            lines,errors = ND280GRID.runLCG(command)

            vectorName = ''

            ## Loop over available production tags
            for tag in lines:
                ## Try all types of vector type
                for type in 'numc','nucp':

                    ## Determine directory path from input path
                    vectorDir = '/'.join(inputPath.split('/')[:-2]).replace('lfn:','')
                    vectorDir = vectorDir.replace('/'+respin+'/','/'+tag+'/')

                    vectorDir+='/'+type
                    print 'Examining '+ vectorDir

                    command = 'lfc-ls '+vectorDir
                    lines,errors = ND280GRID.runLCG(command)

                    if lines:
                        ## If there are files in this directory, try and
                        ## locate the correct one
                        vectors = [l for l in lines if self.input.GetRunNumber()+'-'+self.input.GetSubRunNumber()+'_'+self.input.GetFileHash() in l]

                        ## only one should match
                        vectorName = vectors[0]
                        break
                    else:
                        continue

                ## Break out of tag loop if vector found
                if vectorName:
                    break

                ## Go no further than input tag
                if tag == respin:
                    break

        if not vectorName:
            print 'No vector found!'
            return 1

        print 'Found vector '+vectorDir+'/'+vectorName
        vector = ND280GRID.ND280File('lfn:'+vectorDir+'/'+vectorName)
        # self.localVector = vector.CopyLocal(self.base,ND280GRID.GetDefaultSE())  soph

        return 0


    def RemoveVectorFile(self):
        ## if this is a respin then remove any local vector files...
        if self.localVector:
            sys.stdout.flush()
            print 'Local vector file found, removing...'
            if os.path.exists(self.localVector):
                os.remove(self.localVector)


    ## Set function for NEUT version (called in ND280MC_process.py)
    def SetNEUTVersion(self,neutVersion=''):
        self.neutVersion = neutVersion

    ## Set function for nd280Highland2 version (called in ND280FlatTree_process.py)
    def SetHighlandVersion(self,highlandVersion=''):
        self.highlandVersion = highlandVersion


class ND280Process(ND280Job):
    """Run the nd280 software on raw or MC data """

    def __init__(self, nd280ver, input, jobtype, evtype='', modules='', config='', dbtime='', fmem=20971520, vmem=4194304, tlim=86400):
        super(ND280Process, self).__init__(nd280ver)
        if type(input) is str:
            self.input=ND280File(input)
        else:
            self.input=input

        sys.stdout.flush()
        print self.input.filename
        print type(self.input)

        # Special module list configuration
        self.config_options['module_list']=''
        for module in modules:
            print 'Module to run: ' + str(module)
            self.config_options['module_list'] += str(module) + ' '

        # Special custom configuration list
        if config:
            config = config.replace("'","")
            print 'Custom config: ' + str(config)
            self.config_options['custom_list'] = config

            # Insert custom_list to dictionary
            for line in config.split(','):
                if '=' in line:
                    key,value = line.split('=')
                    self.custom_list_dict[key] = value

                    ## and add to configs (only valid options will be implemented by ND280Configs.py)
                    self.config_options[key] = value

            print 'Custom list dict:'
            print self.custom_list_dict

        if dbtime:
            print 'Setting database time: ' + str(dbtime)
            self.config_options['db_time'] = str(dbtime)

        self.evtype     = evtype
        self.quicktest  = 'false'
        self.memcommand = 'ulimit -f '+str(fmem)+'\nulimit -v '+str(vmem)+'\nulimit -a\nulimit -t '+str(tlim)+'\n'

        ## Don't make a configuration file for non runND280 jobs
        if not jobtype in ND280GRID.NONRUNND280JOBS:
            ## Create a configfilename
            cfgfn = ND280GRID.GetConfigNameFromInput(self.input.filename)
            self.configfile = ND280Config(jobtype,cfgfn)


    def SetQuick(self):
	    self.quicktest='true'

    def GetLocalFile(self,override=''):
        """
        try:
            ## try to get file turl, currently only support for STORM
            self.localfile=self.input.GetTurl()
            print 'Got turl ' + self.localfile
        except:
        """
        sys.stdout.flush()

        if override:
            print('soph - ND280Job.py - ND280Process - GetLocalFioile - override = ' + override)
            print 'GetLocalFile(%s)' % override
            f = ND280File(override)
            self.localfile = f.CopyLocal(self.base,ND280GRID.GetDefaultSE())
            return

        ## If exception is raised by getting the turl then do a local copy
        print 'self.input.filename = ', self.input.filename
        print 'self.input.path     = ', self.input.path
        print 'type(self.input)    = ', (self.input)
        print 'self.base           = ', self.base
        print 'self.input.gridfile = ', self.input.gridfile

        if self.input.gridfile:

            print ('soph ND280Job ND280Process GetLocalFile - is gridfile')
            # self.localfile = self.input.CopyLocal(self.base,ND280GRID.GetDefaultSE())  #soph-quick-dirty-dfc-fix
            # using base is giving it local directory, we want the dfc diractory
            self.localfile = self.input.CopyLocal(self.input.path,ND280GRID.GetDefaultSE())

            print 'Local copy to ' + self.localfile
        else:
            print ('soph ND280Job ND280Process GetLocalFile - is local file')
            self.localfile = self.input.filename
            print self.input.filename + ' is local'

    def RunRaw(self):
        print 'RunRaw()'

        ### Get local input file
        self.GetLocalFile()

        if not self.localfile:
            raise self.Error('Error obtaining file to process.')

        ### control sample filenames coud be corrupting n280Control...

        ### Raw Data Options: Dictionary of options specific to Raw data processing cfg files
        if self.quicktest=='true':
            self.config_options['comment']=self.nd280ver+'_q100'
        else:
            self.config_options['comment']=self.nd280ver+'-'+self.sitename

        ## If it is a processed file then this is a respin!
        if self.input.filetype=='p':
            self.config_options['inputfile']=self.localfile

            ## Increment the version number of the input file
            version=int(self.input.GetVersion())+1
            print 'Version = ', version
            self.config_options['version_number']=str(version)

            ## Get the stage so we know what module list to use
            stage = self.input.GetStage()
            print 'This is a re-spin of stage ' + stage + ' to version ', version

            ## Do not override module_list if an explicit module_list has been passed...
            if not self.config_options['module_list']:
                if stage=='unpk':
                    self.config_options['module_list']='oaCalib oaRecon oaAnalysis'
                elif stage=='cali':
                    self.config_options['module_list']='oaRecon oaAnalysis'
                elif stage=='reco':
                    self.config_options['module_list']='oaAnalysis'
                else:
                    raise self.Error('The file is processed to stage ' + stage + ' so re-processing cannot re-commence')
        ## If it is a CERN testbeam file we need to use special settings
        elif self.input.filetype=='c':
            self.config_options['midas_file']=self.localfile
            if not self.config_options['module_list']:
                self.config_options['module_list']='ecalTestBeam ecalTestBeamCalib ecalRecon oaAnalysis'
            self.config_options['event_select']      =self.evtype
            self.config_options['enable_modules']    ='TECALTestbeamModule'
            self.config_options['disable_modules']   ='TGlobalReconModule TP0DReconModule TBasicDataQualityModule TNRooTrackerVtxModule TGRooTrackerVtxModule.cxx TTrackerReconTOATrackModule TTrackerReconModule TSmrdReconModule TFgdOnlyModule TExample2010aAnalysis1Module TFGDIsoReconTOATrackModule TBeamSummaryDataModule'
            self.config_options['process_truncated'] ='true'
        ## otherwise this is a ND280midas file so start from oaUnpack.
        else:
            self.config_options['midas_file']=self.localfile
            if not self.config_options['module_list']:
                self.config_options['module_list']='oaUnpack oaCalib oaRecon oaAnalysis'
            self.config_options['event_select']=self.evtype

        if self.quicktest=='true':
            self.config_options['num_events'] = '100'
        self.configfile.SetOptions(self.config_options)
        self.configfile.CreateConfig()
        self.configfile.StdOut()

        os.chdir(self.base)
        command = self.memcommand + "runND280 -t ./ -c " + self.configfile.config_filename + "\n"
        rtc = self.RunCommand(command)
        if rtc:
            self.PrintLogs()
            sys.exit("failed to source scripts and execute RunRaw on " + self.configfile.config_filename + " with input " + self.input.filename);

        return 0


    def RunMC(self):
        ### Get local input file
        sys.stdout.flush()

        self.GetLocalFile()

        if not self.localfile:
            raise self.Error('Error obtaining file to process.')

        ## Is this is a respin?
        stage = self.input.GetStage()

        # Do not override module_list if input is a neutrino vector file, or an explicit module_list has been passed
        if stage != 'numc' and stage != 'nucp':
            if not self.config_options['module_list']:
                print 'This is a re-spin of stage ' + stage
                if   stage=='elmc':
                    self.config_options['module_list']='oaCalibMC oaRecon oaAnalysis'
                elif stage=='cali':
                    self.config_options['module_list']='oaRecon oaAnalysis'
                elif stage=='reco':
                    self.config_options['module_list']='oaAnalysis'
                else:
                    raise self.Error('The file is processed to stage ' + stage + ' so re-processing cannot re-commence')

            ## Locate the vector file
            if self.LocateVectorFile():   # soph-quick-dirty-dfc-fix    need to edit this so it downloads form DFC
                raise self.Error('Could not locate input vectors')

        self.config_options['inputfile']      = self.localfile
        self.config_options['count_type']     = 'MEAN'
        self.config_options['bunch_duration'] = '19'
        self.config_options['mc_position']    = 'free'

        # tpc constants and dead tfbs
        if 'run1' in self.input.path:
            self.config_options['ecal_periods_to_activate'] = '1-2'
        elif 'run2' in self.input.path:
            self.config_options['ecal_periods_to_activate'] = '1-2'
            self.config_options['tpc_periods_to_activate']  = 'runs2-3'
        elif ('run3' in self.input.path  or  'run6' in self.input.path):
            self.config_options['ecal_periods_to_activate'] = '3-4'
            self.config_options['tpc_periods_to_activate']  = 'runs2-3'
        elif ( 'run4' in self.input.path  or  'run5' in self.input.path):
            self.config_options['ecal_periods_to_activate'] = '3-4'
            self.config_options['tpc_periods_to_activate']  = 'runs2-3-4'
        else: # (run 7,8,9 ? )
            self.config_options['ecal_periods_to_activate'] = '3-4'
            self.config_options['tpc_periods_to_activate']  = 'run7'


        # 2015-08 geometry and beam configurations
        if '2015-08' in self.input.path:
            self.config_options['baseline'] ='2015-08'

            # water in modes
            if 'water' in self.input.path:
                self.config_options['p0d_water_fill'] ='1'

                if 'run6' in self.input.path and 'anti-' in self.input.path:
                    self.config_options['interactions_per_spill'] ='4.75661'
                    self.config_options['pot_per_spill']          ='1.23832E+14'

                elif 'run7' in self.input.path and 'anti-' in self.input.path:
                    self.config_options['interactions_per_spill'] ='yyy'
                    self.config_options['pot_per_spill']          ='yyy'

                else:
                    self.config_options['interactions_per_spill'] ='zzz'
                    self.config_options['pot_per_spill']          ='zzz'


            # water out modes
            elif 'air' in self.input.path:
                self.config_options['p0d_water_fill'] ='0'

                if 'run6' in self.input.path and 'anti-' in self.input.path:
                    self.config_options['interactions_per_spill'] ='4.74223'
                    self.config_options['pot_per_spill']          ='1.23832E+14'

                elif 'run7' in self.input.path and 'anti-' in self.input.path:
                    self.config_options['interactions_per_spill'] ='yyy'
                    self.config_options['pot_per_spill']          ='yyy'

                else:
                    self.config_options['interactions_per_spill'] ='zzz'
                    self.config_options['pot_per_spill']          ='zzz'



        # 2010-11 geometry and beam configurations
        if '2010-11' in self.input.path:
            self.config_options['baseline'] ='2010-11'

            # water in modes
            if 'water' in self.input.path:
                self.config_options['p0d_water_fill'] ='1'

                if 'beamc' in self.input.path or 'run3' in self.input.path or 'run4' in self.input.path:
                    if 'old-neut' in self.input.path:
                        self.config_options['interactions_per_spill'] ='11.1374'
                    else:
                        self.config_options['interactions_per_spill'] ='10.8294'
                    self.config_options['pot_per_spill']              ='9.462526e+13'
                elif ('beamd' in self.input.path or 'run5' in self.input.path) and 'anti-' in self.input.path:
                    if 'old-neut' in self.input.path:
                        self.config_options['interactions_per_spill'] ='3.7007'
                    else:
                        self.config_options['interactions_per_spill'] ='3.2471'
                    self.config_options['pot_per_spill']              ='9.462526e+13'
                else:
                    if 'old-neut' in self.input.path:
                        self.config_options['interactions_per_spill'] ='9.40276'
                    else:
                        self.config_options['interactions_per_spill'] ='9.1426'
                    self.config_options['pot_per_spill']              ='7.9891e+13'

            # water out modes
            elif 'air' in self.input.path:
                self.config_options['p0d_water_fill'] ='0'

                if 'beamc' in self.input.path or 'run3' in self.input.path or 'run4' in self.input.path:
                    if 'old-neut' in self.input.path:
                        self.config_options['interactions_per_spill'] ='11.1076'
                    else:
                        self.config_options['interactions_per_spill'] ='10.8011'
                    self.config_options['pot_per_spill']              ='9.462526e+13'
                elif 'run6' in self.input.path and 'anti-' in self.input.path:
                    self.config_options['interactions_per_spill']     ='4.82169'
                    self.config_options['pot_per_spill']              ='12.3832e+13'
                else:
                    if 'old-neut' in self.input.path:
                        self.config_options['interactions_per_spill'] ='9.3775'
                    else:
                        self.config_options['interactions_per_spill'] ='9.1187'
                    self.config_options['pot_per_spill']              ='7.9891e+13'

        # 2010-02 geometry and beam configurations
        elif '2010-02' in self.input.path or 'run1' in self.input.path:
            self.config_options['baseline']               ='2010-02'
            self.config_options['nbunches']               ='6'
            # for production 6
            if 'old-neut' in self.input.path:
                self.config_options['interactions_per_spill'] ='4.0750'
            else:
                self.config_options['interactions_per_spill'] ='3.9597'
            self.config_options['pot_per_spill']          ='3.6617e+13'
            self.config_options['bunch_duration']         ='17'
            self.config_options['comment']                ='magnet201002watera'

        # basket beam configurations
        if 'basket' in self.input.path:
            self.config_options['mc_full_spill']          ='0'
            self.config_options['count_type']             ='FIXED'
            self.config_options['interactions_per_spill'] ='1'
            self.config_options['nbunches']               ='1'
            self.config_options['time_offset']            ='0'
            self.config_options['bunch_duration']         ='0'
            self.config_options['time_offset']            ='0'

        if 'oa_nt_' in self.localfile:
		self.config_options['mc_type']     ='Neut_RooTracker'
	elif 'oa_gn_' in self.localfile:
		self.config_options['mc_type']     ='Genie'
        if not self.config_options['module_list']:
            self.config_options['module_list']     ='nd280MC elecSim oaCalibMC oaRecon oaAnalysis'

#        self.config_options['event_select']=self.evtype

        self.configfile.SetOptions(self.config_options)
        self.configfile.CreateConfig()
        self.configfile.StdOut()

        os.chdir(self.base)
        command = self.memcommand + "runND280 -t ./ -c " + self.configfile.config_filename + "\n"

        rtc = self.RunCommand(command)
        if rtc:
            self.PrintLogs()
            sys.exit("failed to source scripts and execute RunMC on " + self.configfile.config_filename + " with input " + self.input.filename);

        return 0

    def RunCalib(self):
        os.chdir(self.base)

        sys.stdout.flush()
        print 'In directory  :'+os.getcwd()
        print '\n'.join(os.listdir(os.getcwd()))

        print 'Copy from srm '+ND280GRID.GetDefaultSE()+' to local'
        print self.input.filename
        print type(self.input)
        print self.base
        self.GetLocalFile()

        if not self.localfile:
            raise self.Error('Error obtaining file to process.')

        ### Raw Data Options: Dictionary of options specific to Raw data processing cfg files
        if self.quicktest=='true':
            self.config_options['comment']=self.nd280ver+'_q100'
        else:
            self.config_options['comment']=self.nd280ver+'-'+self.sitename

        self.calibfn='oa_nd_ecalmod_cos_'+str(self.input.GetRunNumber())+'-'+str(self.input.GetSubRunNumber())+'_cali_'+self.nd280ver+'.root'
        self.logAfn ='oa_nd_ecalmodA_cos_'+str(self.input.GetRunNumber())+'-'+str(self.input.GetSubRunNumber())+'_logf_'+self.nd280ver+'.log'

        command = self.memcommand + "export TFBAPPLYCALIBROOT=$PWD\nexport OACALIBROOT=$PWD\nRunOACalib.exe -t c -o " + self.calibfn + " -m " + self.localfile + " > " + self.logAfn + "\n"

        rtc = self.RunCommand(command)
        if rtc:
            self.PrintLogs()
            sys.exit("failed to source scripts and execute RunCalib on " + self.configfile.config_filename + " with input " + self.input.filename);

        return 0

    def RunSimpleTrackFitter(self):
        ### Run simpleTrackTitter.exe on the cali file in this directory
        os.chdir(self.base)

        sys.stdout.flush()
        print 'In directory  :'+os.getcwd()
        print '\n'.join(os.listdir(os.getcwd()))

        self.califn = glob.glob('oa_*cali*.root')[0]
        if not self.califn:
            self.PrintLogs()
            sys.exit("Can't find input cali file for simpleTrackFitter")

        self.stftfn='oa_nd_ecalmod_cos_' +str(self.input.GetRunNumber())+'-'+str(self.input.GetSubRunNumber())+'_stft_'+self.nd280ver+'.root'
        self.logBfn='oa_nd_ecalmodB_cos_'+str(self.input.GetRunNumber())+'-'+str(self.input.GetSubRunNumber())+'_logf_'+self.nd280ver+'.log'

        command = self.memcommand + "simpleTrackFitter.exe -O par_override=ECALWIDETIMECUT.PARAMETERS.DAT -O SaveEvts -o " + self.stftfn + " " + self.califn + " > " + self.logBfn + "\n"

        rtc = self.RunCommand(command)
        if rtc:
            self.PrintLogs()
            sys.exit("failed to source scripts and execute RunSimpleTrackFitter on " + self.configfile.config_filename + " with input " + self.input.filename);

        return 0


    def RunCollectMuonData(self):
        ### Run simpleTrackTitter.exe on the cali file in this directory
        os.chdir(self.base)

        sys.stdout.flush()
        print 'In directory  :'+os.getcwd()
        print '\n'.join(os.listdir(os.getcwd()))

        if not os.path.exists(self.stftfn):
            self.PrintLogs()
            sys.exit("Can't find input stft file for collectMuonData")

        self.cmudfn='oa_nd_ecalmod_cos_' +str(self.input.GetRunNumber())+'-'+str(self.input.GetSubRunNumber())+'_cmud_'+self.nd280ver+'.root'
        self.logCfn='oa_nd_ecalmodC_cos_'+str(self.input.GetRunNumber())+'-'+str(self.input.GetSubRunNumber())+'_logf_'+self.nd280ver+'.log'

        command = self.memcommand + "collectMuonData.exe -o " + self.cmudfn + " " + self.stftfn + " > " + self.logCfn + "\n"

        rtc = self.RunCommand(command)
        if rtc:
            self.PrintLogs()
            sys.exit("failed to source scripts and execute RunCollectMuonData on " + self.configfile.config_filename + " with input " + self.input.filename);

        return 0


    def RunP0DRecon(self):
        ### Run P0DRECON.exe on the cali file in this directory
        os.chdir(self.base)

        sys.stdout.flush()
        print 'In directory  :'+os.getcwd()
        print '\n'.join(os.listdir(os.getcwd()))

        self.califn = glob.glob('oa_*cali*.root')[0]
        if not self.califn:
            self.PrintLogs()
            sys.exit("Can't find input cali file for P0DRecon")

        self.recofn='oa_nd_spl_'+str(self.input.GetRunNumber())+'-'+str(self.input.GetSubRunNumber())+'_p0dmod_reco_'+self.nd280ver+'.root'
        self.logDfn='oa_nd_spl_'+str(self.input.GetRunNumber())+'-'+str(self.input.GetSubRunNumber())+'_p0dmod_reco_logf_'+self.nd280ver+'.log'

        command = self.memcommand + "P0DRECON.exe -O p0dOnly -o " + self.recofn + " " + self.califn + " > " + self.logDfn + "\n"

        rtc = self.RunCommand(command)
        if rtc:
            self.PrintLogs()
            sys.exit("failed to source scripts and execute P0DRecon on " + self.configfile.config_filename + " with input " + self.input.filename);

        return 0

    def RunP0DControlSample(self):
        ### Run simpleTrackTitter.exe on the reco file in this directory
        os.chdir(self.base)

        sys.stdout.flush()
        print 'In directory  :'+os.getcwd()
        print '\n'.join(os.listdir(os.getcwd()))

        if not os.path.exists(self.recofn):
            self.PrintLogs()
            sys.exit("Can't find input reco file for CreateControlSample")

        self.psmufn='oa_nd_spl_'+str(self.input.GetRunNumber())+'-'+str(self.input.GetSubRunNumber())+'_p0dmod_psmu_'+self.nd280ver+'.root'
        self.logEfn='oa_nd_spl_'+str(self.input.GetRunNumber())+'-'+str(self.input.GetSubRunNumber())+'_p0dmod_psmu_logf_'+self.nd280ver+'.log'

        command = self.memcommand + "CreateControlSample.exe -k -O p0dsmu=" + self.psmufn + " " + self.recofn + " > " + self.logEfn + "\n"

        rtc = self.RunCommand(command)
        if rtc:
            self.PrintLogs()
            sys.exit("failed to source scripts and execute CreateControlSample on " + self.configfile.config_filename + " with input " + self.input.filename);

        return 0

    def RunOAAnalysis(self):
        ### Run RunOAAnalysis.exe on the psmu file in this directory
        os.chdir(self.base)

        sys.stdout.flush()
        print 'In directory  :'+os.getcwd()
        print '\n'.join(os.listdir(os.getcwd()))


        if not os.path.exists(self.psmufn):
            self.PrintLogs()
            sys.exit("Can't find input psmu file for RunOAAnalysis")

        self.analfn='oa_nd_spl_'+str(self.input.GetRunNumber())+'-'+str(self.input.GetSubRunNumber())+'_p0dmod_anal_'+self.nd280ver+'.root'
        self.logFfn='oa_nd_spl_'+str(self.input.GetRunNumber())+'-'+str(self.input.GetSubRunNumber())+'_p0dmod_anal_logf_'+self.nd280ver+'.log'

        command = self.memcommand + "RunOAAnalysis.exe -o " + self.analfn + " " + self.psmufn + " > " + self.logFfn + "\n"

        rtc = self.RunCommand(command)
        if rtc:
            self.PrintLogs()
            sys.exit("failed to source scripts and execute RunOAAnalysis on " + self.configfile.config_filename + " with input " + self.input.filename);

        return 0

    def RunNEUTSetup(self, generator, geometry, vertex, beam, POT):
        ## Run neutSetup using nd280Control
        os.chdir(self.base)

        sys.stdout.flush()
        print 'In directory  :'+os.getcwd()
        print 'Using input   :'+self.input.filename
        print 'Module list   :'+self.config_options['module_list']

        ## Get local input file
        self.GetLocalFile()


        ## Get run and subrun
        # subrun = ND280GRID.GetSubRunFromFlukaFileName(self.input.filename)

        sub_split = str(self.config_options).split("subrunOffset': '" , 1)[1]
        sub_split_slice = sub_split[:-2]

        subrun =  0  # this is an int - arithmetic and stringification in lines below  # soph-neutMC
        subrun=sub_split_slice      # soph-neutMC
        run    = '0' # default to 0

        ## Was the run code specified? - It should be in the format ZABCDEEE - test that length is 8
        # Z   = 9 -> Neutrino MC, 8 -> Anti-neutrino MC
        # A   = Generator (0: NEUT, 1: GENIE, 2: old NEUT)
        # B   = ND280 Data Run (with a certain beam condition and set of dead channels assumed for each run)
        # C   = 0: P0D air, 1: P0D water
        # D   = Volume / Sample type (0: Magnet, 1: Basket (beam), 2: nue, 3: NC1pi0, 4: CC1pi0, 5: NC1pi+, 6: CC1pi+, 7: tpcgas)
        # EEE = 3 digit run number
        if 'runCode' in self.custom_list_dict:
            if len(self.custom_list_dict['runCode']) == 8:
                run = self.custom_list_dict['runCode']
            else:
                print 'Length of runCode != 8, defaulting to 0. runCode = %s' % (self.custom_list_dict['runCode'])

        ## Offset the subrun no. ?
        if 'subrunOffset' in self.custom_list_dict:
            subrun += int(self.custom_list_dict['subrunOffset'])
        else:
            subrun = str(subrun)

        # [software]
        self.config_options['neut_setup_script'] = '%s/NEUT%s/%s/src/neutgeom/setup.sh' % (os.getenv('VO_T2K_ORG_SW_DIR'),self.neutVersion,self.neutVersion)

        # [geometry]
        self.config_options['baseline'] = '-'.join(geometry.split('-')[:2])
        if 'water' in geometry:
            self.config_options['p0d_water_fill'] = '1'
        else:
            self.config_options['p0d_water_fill'] = '0'

        # [configuration]
        #self.config_options['module_list'] = 'neutSetup neutMC'   # soph-neutMC
        self.config_options['module_list'] = 'neutMC' # soph-neutMC


        # [filenaming]
        self.config_options['run_number'] = run
        self.config_options['subrun'    ] = subrun
        self.config_options['comment'   ] = vertex + geometry.replace('-','') + beam
        if 'anti' in generator : self.config_options['comment'] = 'nu_bar' + self.config_options['comment']

        # [neutrino]
        # nutype - must be one of NUE, NUEBAR, NUMU, NUMUBAR or BEAM
        if beam.startswith('beam') or beam.startswith('run'):  # beama, beamb... run1, run2 etc
            nutype = 'beam'
        elif 'nue' in beam:
            if 'anti' in generator : nutype = 'nuebar'
            else                   : nutype = 'nue'
        else:
            if 'anti' in generator : nutype = 'numubar'
            else                   : nutype = 'numu'
        self.config_options['neutrino_type'] = nutype
        self.config_options['master_volume'] = vertex[0].upper() + vertex[1:]
        self.config_options['flux_region'  ] = vertex
        if self.input.path.startswith('/cvmfs') : self.config_options['flux_file'] = self.input.path + self.input.filename
        else                                    : self.config_options['flux_file'] = self.localfile

        #self.config_options['maxint_file'  ] = self.localfile.replace('.root','evtrate_'+self.config_options['comment']+'.root')
        # TODO - soph - should pass this as an option
        self.config_options['maxint_file'  ] = '/cvmfs/t2k.egi.eu/NEUT_event_rate/nu.13a_nom_ND6_250ka_flukain.allevtrate_magnet_201011air.root'
        #self.config_options['maxint_file'  ] = '/cvmfs/t2k.egi.eu/NEUT_event_rate/NEUT5.4.0_nu.13a_nom_ND6_m250ka_flukain.allevtrate_magnet201011water.root' # soph-neutMC - anti run5water 5.4.0
        #self.config_options['maxint_file'  ] = '/cvmfs/t2k.egi.eu/NEUT_event_rate/NEUT5.4.0_nu.13a_nom_ND6_m250ka_flukain.allevtrate_magnet201508water.root'  # soph-neutMC

        self.config_options['pot'          ] = POT
        self.config_options['random_start' ] = '1'

        self.configfile.SetOptions(self.config_options)
        self.configfile.CreateConfig()
        self.configfile.StdOut()

        ## make sure to run NEUT environmental setup script before
        ## nd280Control
        os.chdir(self.base)
        command = 'source %s/NEUT%s/setup.sh\n' % (os.getenv('VO_T2K_ORG_SW_DIR'),self.neutVersion)
        command += 'env\n' + self.memcommand + "runND280 -t ./ -c " + self.configfile.config_filename + "\n"
        rtc = self.RunCommand(command)
        if rtc:
            self.PrintLogs()
            sys.exit("failed to source scripts and execute RunNEUTSetup on " + self.configfile.config_filename + " with input " + self.input.filename);

        return 0

    def RunCreateFlatTree(self):
        ## Run RunCreateFlatTree.exe on an oaAnalysis file.
        sys.stdout.flush()
        os.chdir(self.base)
        print 'RunCreateFlatTree() in directory  :'+os.getcwd()

        if self.input.GetStage() == 'anal':
            self.GetLocalFile()
        else:
            # If the input is not an oaAnalysis file, look for it in the working directory
            filelist = os.listdir(os.getcwd())
            for f in filelist:
                if '_anal_' in f and f.endswith('.root'):
                    self.localfile = f
                    break

        if not self.localfile:
            raise self.Error('Error obtaining file to process.')

        print 'Using input   :'+self.localfile

        ## make sure to run the nd280Highland2 setup script
        command = 'source %s/nd280Highland2%s/setup.sh\n'             % (os.getenv('VO_T2K_ORG_SW_DIR'),self.highlandVersion)
        command += self.memcommand + 'RunCreateFlatTree.exe -o %s %s' % (os.path.basename(self.localfile).replace('_anal_','_flat'+self.highlandVersion+'_'), self.localfile)
        rtc = self.RunCommand(command)
        if rtc:
            self.PrintLogs()
            sys.exit("failed to source scripts and execute RunCreateFlatTree on " + self.localfile);

        return 0


    def RunHADD(self):
        ## Run hadd on a list of ROOT files
        sys.stdout.flush()
        os.chdir(self.base)
        print 'RunHADD() in directory  :'+os.getcwd()

        ## Get the input file
        self.GetLocalFile()
        if not self.localfile:
            raise self.Error('Error obtaining file to process %s' % (self.input.filename))
        print 'Using input   :'+self.localfile

        ## Build up the list of filenames to hadd
        inputString = ''

        ## list of ND280Files
        inputFiles = []

        ## Read the file list
        filenames = [ f.strip() for f in open(self.localfile).readlines() ]
        for filename in filenames:
            print 'Getting ',filename
            if not filename.endswith('.root') : sys.exit('%s is not a valid ROOT file!!'%(filename))
            f            = ND280File(filename)                              # instantiate an ND820File
            localname    = f.CopyLocal(self.base,ND280GRID.GetDefaultSE())  # copy the file to the working directory ready for hadd-ing
            inputString += localname + ' '                                  # add the local file name to the hadd input string
            inputFiles.append(f)                                            # append this file to the list of inputFiles

        ## The name of the hadd-ed file... derives from the input file paths
        # the prefix is simply the logical directory path with '/' substituted with '.'
        stitchName = inputFiles[0].alias.rstrip(inputFiles[0].filename).lstrip('lfn:').lstrip(os.getenv('LFC_HOME')).replace('/','.')

        # is this a processed file?
        if inputFiles[0].GetRunNumber():
            stitchName += inputFiles[0] .GetRunNumber() + '-' + inputFiles[0] .GetSubRunNumber() + '-' # add the run-subrun of the first file
            stitchName += inputFiles[-1].GetRunNumber() + '-' + inputFiles[-1].GetSubRunNumber()       # add the run-subrun of the last file
        else:
            # just concatenate the first and last filenames, less their .root extensions
            stitchName += inputFiles[0].filename.rstrip('.root') + '-' + inputFiles[-1].filename.rstrip('.root')
        stitchName += '.hadded.root'
        print 'hadd-ing to %s' % (stitchName)

        command     = self.memcommand + 'hadd -f %s %s' % (stitchName,inputString)
        rtc         = self.RunCommand(command)
        if rtc:
            self.PrintLogs()
            sys.exit("failed to source scripts and execute RunHADD on " + self.localfile);

        ## Register the output
        f      = ND280File(stitchName)
        lfnDir = os.path.dirname(filenames[0])+'/hadded/'  # write to 'hadded' subdirectory in the path of the first input
        f.Register(lfnDir,ND280GRID.GetDefaultSE())

        return 0

    def RunCreateMiniTree(self):
        ## Run RunCreateMiniTree.exe on an oaAnalysis file.
        sys.stdout.flush()
        os.chdir(self.base)
        print 'RunCreateMiniTree() in directory  :'+os.getcwd()

        if self.input.GetStage() == 'anal':
            self.GetLocalFile()
        else:
            # If the input is not an oaAnalysis file, look for it in the working directory
            filelist = os.listdir(os.getcwd())
            for f in filelist:
                if '_anal_' in f and f.endswith('.root'):
                    self.localfile = f
                    break

        if not self.localfile:
            raise self.Error('Error obtaining file to process.')

        print 'Using input   :'+self.localfile

        ## make sure to run the nd280Highland2 setup script
        command = 'source %s/nd280Highland2%s/setup.sh\n'             % (os.getenv('VO_T2K_ORG_SW_DIR'),self.highlandVersion)
        command += self.memcommand + 'RunCreateMiniTree.exe -o %s %s' % (os.path.basename(self.localfile).replace('_anal_','_mini'+self.highlandVersion+'_'), self.localfile)
        rtc = self.RunCommand(command)
        if rtc:
            self.PrintLogs()
            sys.exit("failed to source scripts and execute RunCreateMiniTree on " + self.localfile);

        return 0

    ## Print out the contents of any log files in the base directory
    def PrintLogs(self):
        sys.stdout.flush()
        os.chdir(self.base)
        for l in glob.glob('*.log'):
            print 'Printing Log File : %s' % (l)
            print ''.join(open(l,'r').readlines())
