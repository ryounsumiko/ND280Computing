#!/usr/bin/env python

"""
A bunch of handy commands for use with the ND280 software on the grid or locally.

The object allows one to list information of packages, disable packages and install software.

"""

import sys
import re
import tempfile
import os
import optparse
import shutil
import stat
import glob
from ND280GRID import *
## import pexpect

## Removes those annoying newlines from a string
def rmNL(inStr):
    return inStr.replace("\n","")

class ND280Software:

    def __init__(self,nd280ver,name=''):
        self.nd280ver=nd280ver
        self.nd280name=nd280ver
        if name:
            self.nd280name=name

        #### Get important environment variables
        self.t2ksoftdir = self.GetT2KSoftDir()
        if not self.t2ksoftdir:
            raise Error("Could not get env variable VO_T2K_ORG_SW_DIR")
        self.base = os.getcwd() ## The present working directory
        self.instDir=self.t2ksoftdir+"/nd280"+self.nd280name

        print 'self.base: ' + self.base
        print 'self.instDir: ' + self.instDir

        #### Create cvsrsh file if not present
        self.cvsrsh_filename=self.base + '/cvsrsh.sh'
        print 'cvsrsh: ' + self.cvsrsh_filename
        if not os.path.isfile(self.cvsrsh_filename):
            self.MakeCVSRSH()

        #### Set important environment variables
        os.environ['CVSROOT']=':ext:anoncvs@repo.nd280.org:/home/trt2kmgr/ND280Repository'
        os.environ['CVS_RSH']= self.cvsrsh_filename
        os.environ['BASE']=self.base
        os.environ['CMTPATH'] = self.instDir

        # force a CMTCONFIG
        os.environ['CMTCONFIG'] = 'Linux-x86_64'

        print 'CVSROOT: ' + os.environ['CVSROOT']
        print 'CVS_SSH: ' + os.environ['CVS_RSH']
        print 'BASE: '    + os.environ['BASE']
        print 'CMTPATH: ' + os.environ['CMTPATH']
        print 'CMTCONFIG' + os.environ['CMTCONFIG']

        ### Check the current status of the installation
        self.CheckInstall()

        print 'Check CMT: ' + str(self.install['CMT'])
        print 'Check ND280_dl: ' + str(self.install['ND280_dl'])
        print 'Check ND280_make ' + str(self.install['ND280_make'])

    nd280ver=''
    t2ksoftdir=''
    instDir=''
    base=''
    install={}


    class Error(Exception):
        pass

    ########################################################################################################################
    def CheckInstall(self):
        """ Check the different components of the ND280 installation """
        print 'Checking install'
        self.install['CMT']        =0
        self.install['ND280_dl']   =0
        self.install['ND280_make'] =0
        if os.path.isfile(self.instDir + '/CMT/setup.sh'):
            self.install['CMT']=1
        if os.path.isdir(self.instDir + '/nd280/' + self.nd280ver):
            self.install['ND280_dl']=1
            if os.path.isfile(self.instDir + '/setup.sh'):
                self.install['ND280_make']=1

    ########################################################################################################################
    def RemoveInstall(self):

        """ Completely remove an installation of the ND280 Software """
        print 'Removing install... '

        if self.install['CMT']:
            command = 'rm -rf ' + self.instDir
            rtc = os.system(command)
            if rtc:
                print 'Not removed'
            else:
                print 'Remove done'
                #raise self.Error( "Failed to rm -rf " + self.instDir)
            ### Code here to remove software tags if running on the grid


    ########################################################################################################################
    def InstallCMT(self):

        """ Installs CMT for a specified version of nd280 software """

        if self.install['CMT']:
            print 'CMT already installed'
            return 0

        # Check the install directory.
        if not os.path.isdir(self.instDir):
            try:
                os.makedirs(self.instDir)
            except:
                raise self.Error("Could not make installation directory: " + self.instDir)

        os.chdir(self.instDir) ## cd into the installation directory as all will be done from here

        print 'In dir: ' + os.getcwd()

        if not os.path.isfile(self.cvsrsh_filename):
            raise self.Error('Can\'t see ' + self.cvsrsh_filename)

        command = 'rm -rf CMT'
        print command
        rtc = os.system(command)
        if rtc:
            print 'Nothing to remove'
        else:
            print 'Removed existing CMT'

        command = "cvs checkout CMT"
        print command
        rtc = os.system(command)
        if rtc:
            raise self.Error( "Failed to checkout CMT" )

        print 'Dir contains: ' + str(os.listdir('.'))

        # Now Compile CMT
        print 'Compiling CMT: '
        command = "cd CMT\n./install_cmt"
        rtc = os.system(command)
        if rtc:
            raise self.Error( "Failed to build CMT" )
        else:
            print 'Done'

        self.install['CMT']=1

        return 0

    ########################################################################################################################
    def RunND280Command(self,in_command):
        """ Source the required setups before executing commands """
        command=''
        cmtSetupScr=self.instDir + '/CMT/setup.sh'
        if self.install['CMT']:
            command += 'source ' + cmtSetupScr + '\n'
        nd280SetupScr=self.instDir + '/nd280/' + self.nd280ver + '/cmt/setup.sh'
        if self.install['ND280_dl']:
            command += 'source ' + nd280SetupScr + '\n'
        command += in_command
        rtc = os.system(command)
        return rtc

    ########################################################################################################################
    def GetND280(self):
        """ Obtain the nd280 software from CVS """
        if self.install['ND280_dl']:
            print 'ND280 Software already downloaded'
            return 0

        # Get Variables
        if not self.install['CMT'] and not os.getenv('CMTPATH'):
            raise self.Error('Please make sure CMT is installed first')

        # Check the install directory.
        if not os.path.isdir(self.instDir):
            try:
                os.makedirs(self.instDir)
            except:
                raise self.Error("Could not make installation directory: " + self.instDir)
        os.chdir(self.instDir) ## cd into the installation directory as all will be done from here

        cmtDir = self.instDir+"/CMT"

        cmtpath = os.getenv('CMTPATH')

        # Check the install directory.
        if not os.path.isdir(self.instDir):
            print "echo no installation directory " + self.instDir
            raise self.Error("No Installation directory")

        command="env"
        os.system(command)

        # Pull the code from CVS
        command = 'cmt checkout -R -r '+self.nd280ver+' nd280'
        rtc = self.RunND280Command(command)
        if rtc:
            raise self.Error( "Failed to checkout nd280Soft" )
        self.install['ND280_dl']=1
        return 0

    ########################################################################################################################
    def UnMakeND280(self):
        """ make clean all nd280 software """

        if not self.install['ND280_dl']:
            raise self.Error('Please make sure ND280 is downloaded first')

        os.chdir(self.instDir) ## cd into the installation directory as all will be done from here

        cmtDir = self.instDir+"/CMT"
        cmtpath = os.getenv('CMTPATH')

        command="env"
        os.system(command)

        # Run CMT Config and make
        ## cmt broadcast cmt config\ncmt broadcast source setup.sh\n
        command = 'cd nd280/'+self.nd280ver+'/cmt\ncmt config\nsource setup.sh\ncmt broadcast make clean'
        rtc = self.RunND280Command(command)
        if rtc:
            raise self.Error( "Failed to make clean nd280Soft" )
        return 0

    ########################################################################################################################
    def MakeND280(self):
        """ Make the nd280 software and write setup scripts. """

##         if self.install['ND280_make']:
##             print 'ND280 Software already made'
##             return 0

        print 'Making ND280'

        if not self.install['ND280_dl']:
            raise self.Error('Please make sure ND280 is downloaded first')

        os.chdir(self.instDir) ## cd into the installation directory as all will be done from here

        #Print requirements
        rfile = self.instDir + '/nd280/' + self.nd280ver + '/cmt/requirements'
        os.system('more '+rfile)

        cmtDir = self.instDir+"/CMT"
        cmtpath = os.getenv('CMTPATH')

        command="env"
        os.system(command)

        # Run CMT Config and make
        ## cmt broadcast cmt config\ncmt broadcast source setup.sh\n
        command = 'cd nd280/'+self.nd280ver+'/cmt\ncmt config\ncmt show uses\nsource setup.sh\ncmt broadcast make'
        rtc = self.RunND280Command(command)
        if rtc:
            raise self.Error( "Failed to make nd280Soft" )

        # Write setup scripts
        bashscr = self.instDir+"/setup.sh"
        try:
            batchFH = open(bashscr,"w")
            batchFH.write("#!/bin/sh\n")
            setupScr =  cmtDir+"/setup.sh"
            batchFH.write("if [ -f "+setupScr+" ];\nthen\nsource "+setupScr+"\nfi\n")
            batchFH.write("export CMTPATH="+cmtpath+"\n")
            batchFH.write("echo Setup ND280 software version "+self.nd280ver+"\n")
            setupScr =  self.instDir+"/nd280/"+self.nd280ver+"/cmt/setup.sh"
            batchFH.write("if [ -f "+setupScr+" ];\nthen\nsource "+setupScr+"\nfi\n")
            batchFH.close()
        except:
            raise self.Error("Could not write bash setup script")

        csscr = self.instDir+"/setup.csh"
        try:
            batchFH = open(csscr,"w")
            batchFH.write("#!/bin/csh\n")
            setupScr =  cmtDir+"/setup.csh"
            batchFH.write("if ( -f "+setupScr+" )then\nsource "+setupScr+"\nendif\n")
            batchFH.write("setenv CMTPATH "+cmtpath+"\n")
            batchFH.write("echo Setup ND280 software version "+self.nd280ver+"\n")
            setupScr =  self.instDir+"/nd280/"+self.nd280ver+"/cmt/setup.csh"
            batchFH.write("if ( -f "+setupScr+" )then\nsource "+setupScr+"\nendif\n")
            batchFH.close()
        except:
            raise self.Error("Could not write cshell setup script")

        # Also write the version setup scripts.
        bashscrVer = self.instDir+"/setup_"+self.nd280ver+".sh"
        csscrVer = self.instDir+"/setup_"+self.nd280ver+".csh"
        shutil.copy(bashscr,bashscrVer)
        shutil.copy(csscr,csscrVer)

        # Need to do a simple test.

        # Register the install.
        ### grid tags...

        print 'Done making ND280'

        print 'Setting permissions'
        os.system('chmod og+r $(find . -type f)')
        os.system('chmod og+rx $(find . type d)')
        os.system('ls -lR')

        self.install['ND280_make']=1
        return 0

    ########################################################################################################################



    ########################################################################################################################
    def Disable_ROOTOpenGL(self):
        """ Disable opengl in root, as grid nodes do not have/need these graphic libraries. """

        if not self.instDir or not os.path.isdir(self.instDir):
            raise self.Error('Please make sure CMT is installed first')

        os.chdir(self.instDir) ## cd into the installation directory as all will be done from here

        rootver = self.GetPackageVersion('ROOT')
        if not rootver:
            raise self.Error("Could not get the ROOT version")
        #Modify the root_compile to disable opengl
        command = 'sed \"s^--enable-opengl^--disable-opengl^g\" < ROOT/'+rootver+'/src/compile_root > tmp.txt\ncp tmp.txt ROOT/'+rootver+'/src/compile_root\nrm tmp.txt'
        rtc = os.system(command)
        if rtc:
            raise self.Error( 'Failed to Modify the ROOT/'+rootver+'/src/compile_root\nIs the version correct?'  )
        return 0

    ########################################################################################################################
    def MakeCVSRSH(self):
        """ Create the cvsrsh.sh file required for cvs access """
        filename = self.cvsrsh_filename

        try:
            batchFH = open(filename,"w")
            batchFH.write("#!/bin/sh\n")
            batchFH.write('ssh -o StrictHostKeyChecking=no \"$@\"')
            batchFH.close()
            os.chmod(filename, 0777)
            test_cvsrsh="cd " + self.base + '\necho ===== list1 =====\nls -lh'
            os.system(test_cvsrsh)

        except:
            raise self.Error("Could not write " + self.base + '/cvsrsh.sh')
        return filename

    ########################################################################################################################
    def ReplaceND280Package(self,package,version=''):

        """ Replaces an ND280 package: changes the version in the global cmt requirements, removes the old version and re-makes the software """

        print 'cd ' + str(self.instDir)
        os.chdir(self.instDir) ## cd into the installation directory as all will be done from here

        ## Check that the nd280/v#r#p#/ directory is there
        nd280Dir=self.instDir + '/nd280/' + self.nd280ver
        print 'nd280Dir: ' + str(nd280Dir)
        if not os.path.isdir(nd280Dir):
            print 'ERROR: ' + nd280Dir + ' does not exist, so am unable to replace ' + package
            return 1

        ## Get the current version before replacing
        currVer=''
        try:
            currVer=self.GetPackageVersion(package)
        except:
            self.Error('Could not get current version of ' + package)

        print 'Current version: ' + str(currVer)

        ## Download the replacement version
        self.GetPackage(package,version)

        ## Modify the nd280 requirements to new version of the package
        command = "sed \"s^use\ " + package + " " + currVer + "^use\ " + package + " " + version + "^g\" < "+nd280Dir+"/cmt/requirements > tmp.txt\ncp tmp.txt "+nd280Dir+"/cmt/requirements\nrm tmp.txt"
        rtc = os.system(command)
        if rtc:
            print "Failed to modify " + package + " in " + nd280Dir + "/cmt/requirements"
            return 1

        #Print modified requirements file
        command='more '+nd280Dir+'/cmt/requirements'
        os.system(command)

        ## Re-Make the software
        self.MakeND280()

        return 0


    ########################################################################################################################
    def GetPackage(self,package,version=''):
        print 'Get package ' + str(package) + ' ' + str(version)

        command ='cmt checkout '
        if version:
            command+='-r ' + version + ' '
        command+= package
        self.RunND280Command(command)
        return 0

    ########################################################################################################################
    def DisableND280Package(self,package):

        """ Disables an ND280 package from being installed (comments it out in the global cmt requirements. Needs to be done before making. """

        print "Disabling "+package

#         ## Check that the nd280/v#r#p#/ directory is there
#         nd280Dir=self.instDir + '/nd280/' + self.nd280ver
#         if not os.path.isdir(nd280Dir):
#             print 'ERROR: ' + nd280Dir + ' does not exist, so am unable to disable ' + package
#             return 1

        # find the requirements file that enables this module
        command= "grep -e \"use "+package+"[[:space:]]*v\" "+self.instDir+"/*/*/cmt/requirements"
        lines,errors = runLCG(command,is_pexpect=False)
        if not lines or errors:
            print "ERROR: unable to locate requirments for "+package
            return 1

        requirementsFile = lines[0].split(':')[0]

        # Modify the nd280 requirements to not compile this pacakge
        command = "sed \"s^use\ " + package + "^#use\ " + package + "^g\" < "+requirementsFile+" > tmp.txt\ncp tmp.txt "+requirementsFile+"\nrm tmp.txt"
        rtc = os.system(command)
        if rtc:
            print "Failed to disable " + package + " in " + requirementsFile
            return 1

        print package + " disabled"

        return 0

    ### Get the T2K software directory environment variable
    def GetT2KSoftDir(self):
        t2ksoftdir = os.getenv("VO_T2K_ORG_SW_DIR")

        if not t2ksoftdir:
            t2ksoftdir = os.getenv("VO_T2K_SW_DIR")
        if not t2ksoftdir:
            return ""
        print 'VO_T2K_ORG_SW_DIR: ' + t2ksoftdir
        return t2ksoftdir

    ########################################################################################################################
    def AddTag(self,ce=''):
        """ Adds software tags to the CE which the job is being run upon. Only use after a sucesful install. """
        tag='VO-t2k.org-ND280-' + self.nd280name

        if not ce:
            contact=os.getenv('GLOBUS_GRAM_MYJOB_CONTACT')
            if not contact:
                raise Error('Could not get GLOBUS_GRAM_MYJOB_CONTACT environment variable to determine CE')
            ce=contact.split('/')[2].split(':')[0]

        command='lcg-tags --ce ' + ce + ' --vo t2k.org --add --tags ' + tag
        print command
        rtc=os.system(command)
        if rtc:
            raise Error('Could not create software tag ' + tag + ' on the ce ' + ce)

    ########################################################################################################################
    def RemoveTag(self,ce=''):
        """ Removes software tags to the CE which the job is being run upon. Use after sucessfully removing an install. """
        tag='VO-t2k.org-ND280-' + self.nd280name

        if not ce:
            contact=os.getenv('GLOBUS_GRAM_MYJOB_CONTACT')
            if not contact:
                raise Error('Could not get GLOBUS_GRAM_MYJOB_CONTACT environment variable to determine CE')
            ce=contact.split('/')[2].split(':')[0]

        command='lcg-tags --ce ' + ce + ' --vo t2k.org --remove --tags ' + tag
        print command
        rtc=os.system(command)
        if rtc:
            raise Error('Could not create software tag ' + tag + ' on the ce ' + ce)

    ########################################################################################################################
    def GetPackageVersion(self,package):
        """ Gets the version of a package within a relase of nd280
            nd280version=release version of nd280 E.g. v7r17p5
            package=package name E.g. ROOT or oaAnalysis
            Stripped from revelvant requirements files
        """

        print 'Get current package version of ' + str(package)

        ## Check that the nd280/v#r#p#/ directory is there
        nd280Dir=self.instDir + '/nd280/' + self.nd280ver
        if not os.path.isdir(nd280Dir):
            raise Error(nd280Dir + ' does not exist, so am unable to get version of ' + package)
            return 1

        # find the requirements file that enables this module
        command= "grep -e \"use "+package+"[[:space:]]*v\" "+self.instDir+"/*/*/cmt/requirements"
        lines,errors = runLCG(command,is_pexpect=False)
        if not lines or errors:
            print "ERROR: unable to locate requirents for "+package
            return 1

        version = lines[0].strip().split(' ')[-1]
        print 'Found '+package+' version '+version

        return version

    def testerror(self):
        raise self.Error('Test Error')

        ########################################################################################################################
    def RunGetBeam(self):
        """ Runs the oaBeamData nd280-get-beam """
        command = self.instDir + '/oaBeamData/' + self.GetPackageVersion('oaBeamData') + '/src/nd280-get-beam'
        rtc = self.RunND280Command(command)
        if rtc:
            raise self.Error('Failed to get the beam data')
        return 0

        ########################################################################################################################
    def GetTFBMetaData(self):
        """ Gets the TFBApplyCalib metadata file """
        command = 'wget -P' + self.instDir + '/tfbApplyCalib/' + self.GetPackageVersion('tfbApplyCalib') + '/parameters/ http://www-pnp.physics.ox.ac.uk/~wilson/T2K/fullLog_including_logbook.root'
        rtc=os.system(command)
        if rtc:
            raise self.Error('Failed to get the tfbApplyCalib meta data')
        return 0

class Error(Exception):
    pass

def GRIDInstall():
    """ A GRID style install. """

    ##############################################################################
    # Parser Options

    parser = optparse.OptionParser()
    parser.add_option("-v","--version",dest="version",type="string",help="Version of nd280 software to install")
    parser.add_option("-m","--module", dest="module", type="string",help="To install one specific module inside an existing nd280 package e.g. oaRecon,v0r0")
    parser.add_option("-n","--name",   dest="name",   type="string",help="To specify name and tag of installation, e.g. v9r7p5mod")
    parser.add_option("-u","--unmake", dest="unmake", type="string",help="Set to 1 to run cmt broadcast make clean")
    parser.add_option("-f","--forced", dest="forced", type="string",help="Set to 1 to force install")
    parser.add_option("-c","--compile",dest="compile",type="string",help="Set to 1 to just compile this module")
    parser.add_option("-d","--delete", dest="delete", type="string",help="Set to 1 to delete this version")
    parser.add_option("-b","--beam",   dest="beam",   type="string",help="Set to 1 to just get beam data")
    (options,args) = parser.parse_args()
    ##############################################################################

    # Get Options
    nd280ver = options.version
    if not nd280ver:
        raise Error("Please specify a version to install using the -v or --version flag")
    modrev=options.module
    module = ''
    revision = ''
    if modrev:
        mra=modrev.split(',')
        if len(mra) != 2:
            raise Error("Something went wrong, usage -m oaRecon,v0r0")
        module=str(mra[0])
        revision=str(mra[1])
    if module and not revision:
        raise Error("Something went wrong, usage -m oaRecon,v0r0")
    unmake  = options.unmake
    forced  = options.forced
    compile = options.compile
    delete  = options.delete
    beam    = options.beam
    name=''
    if options.name:
        name=options.name

    os.system('env')

    ## Make sure all content is group (lcgadmin) writeable and readable by all
    os.system('umask 002')

    print 'Set environment'
    sw = ND280Software(nd280ver,name)

    ## Get only the beam data
    if beam:
        print 'Get beam data'
        sw.RunGetBeam()
        return 0

    if unmake:
        print 'Unmaking'
        sw.UnMakeND280()

    if delete:
        print 'Remove install'
        sw.RemoveInstall()

        try:
            sw.RemoveTag()
        except:
            print 'No tags removed, if a grid install please remove by hand'
            return 1
        return 0

    #For the case when we want to add a module
    #to an existing installation
    #-------------------------------------------------------------
    if module:
        print 'Adding module: ' + str(module) + ' ' + str(revision) + ' to nd280 installation'

        os.chdir(sw.instDir) ## cd into the installation directory

        revpath = sw.instDir + '/' + module + '/' + revision
        modpath = sw.instDir + '/' + module
        #If the module of the right revision is there do nothing
        if os.path.exists(revpath):
            print 'Module already installed'
            if forced:
                print 'Forcing install'
                command='rm -rf '+revpath
                rtc = sw.RunND280Command(command)
                if rtc:
                    print 'Remove failed'
                    return 1

        #If the module is there we should replace it with a new version
        if os.path.exists(revpath):
            print 'Not replacing'

        elif os.path.exists(modpath):
            print 'Replacing module'
            rtc = sw.ReplaceND280Package(module,revision)
            if rtc:
                print 'Failed to replace module'
            return rtc

        #Get external module
        else:
            print 'Installing module'
            sw.GetPackage(module,revision)
            compile = '1'

        ## Re-Make the software just in case
        print 'Compiling module'
        if compile:
            os.chdir(revpath + '/cmt')
            rtc = sw.RunND280Command('source setup.sh\ncmt broadcast')
            if rtc:
                print 'Failed to compile package'
                return 1


        #Compile all
        sw.MakeND280()

        return 0

    #Full installation of nd280
    #-------------------------------------------------------------
    print 'Remove install'
    sw.RemoveInstall()
    sw.CheckInstall()

    print 'Install CMT'
    sw.InstallCMT()

    print 'Get ND280'
    sw.GetND280()

    ## There is also the option to modify the root installation, currently just disabling opengl but
    ## can be made more generic if requested/required
    print 'Disable packages'
    sw.Disable_ROOTOpenGL()

    ## You can enable and disable packages - does not consider dependencies so beware!!!
    sw.DisableND280Package('eventDisplay')
    sw.DisableND280Package('ingridRecon')

    ## Make ND280 Software
    print 'Compile software'
    sw.MakeND280()

    ## Get The beam data
    print 'Get beam data'
    sw.RunGetBeam()

    ## Get the tfbApplyCalib metadata
    print 'Get TFB data'
    sw.GetTFBMetaData()

    ## Add Software Tag
    print 'Add tags'
    try:
        sw.AddTag()
    except:
        print 'No tags added, if a grid install please add by hand'
        return 1

    print 'All done'

    return 0

def LocalInstall():
    """ A standard style install. """

    ##############################################################################
    # Parser Options

    parser = optparse.OptionParser()
    parser.add_option("-v","--version",dest="version",type="string",help="Version of nd280 software to install")
    parser.add_option("-d","--t2ksoftdir",dest="t2ksoftdir",type="string",help="Optional to pass the t2ksoftdir as an option, otherwise it must be set as an environment variable VO_T2K_ORG_SW_DIR")

    (options,args) = parser.parse_args()
    ##############################################################################

    # Get Options
    nd280ver = options.version
    if not nd280ver:
        raise Error("Please specify a version to install using the -v or --version flag")

    sw = ND280Software(nd280ver)
    sw.InstallCMT()
    sw.GetND280()

    ## Make ND280 Software
    sw.MakeND280()

    ## Get The beam data
    sw.RunGetBeam()

    return 0

def ReplaceND280Package():
    """ Use this to replace a single package """

    ##############################################################################
    # Parser Options

    parser = optparse.OptionParser()
    parser.add_option("-v","--version",dest="version",type="string",help="Version of nd280 software to install")
    parser.add_option("-p","--package",dest="package",type="string",help="The package to replace")
    parser.add_option("-r","--packageversion",dest="packageversion",type="string",help="The version of the package to replace with")

    (options,args) = parser.parse_args()
    ##############################################################################

    # Get Options
    nd280ver = options.version
    if not nd280ver:
        raise Error("Please specify a version to install using the -v or --version flag")

    package = options.package
    if not package:
        raise Error("Please specify which package to change using the -p or --package flag")

    packageversion = options.packageversion

    sw = ND280Software(nd280ver)
    sw.ReplaceND280Package(package,packageversion)
    if 'tfbApplyCalib' in package:
        sw.GetTFBMetaData()

    return 0

if __name__ == '__main__':
    GRIDInstall()

