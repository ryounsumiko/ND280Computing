#!/usr/bin/env python

import subprocess
import os
import sys
import optparse

from ND280Job import ND280Job

class P0DBarEndCalib(ND280Job):
    """Run P0DBarEndCalib"""
    def  __init__(self,nd280ver):
        super(P0DBarEndCalib,self).__init__(nd280ver)
        #Hard code intermidiate file name for simplicity.
        self.hitsOutput = "hits.root"
        self.inputToGenCalib = "file.txt"
	
    def RunGetHits(self,input_filelist):
        # Check env:
	command =""
	command += "echo $LD_LIBRARY_PATH\n"
        command += "ls $VO_T2K_ORG_SW_DIR\n" 
	# Check out cvs package.
        command += "cmt checkout -r HEAD mppcCalib\n"
        command += "pushd mppcCalib/*/cmt\n"
        command += "cmt br cmt config\n"
        command += "ls\n"
        command += "source ./setup.sh\n"
        command += "cmt make\n"
        #Create input for next stage.
        command += "popd\n"
        command += "echo `pwd`/%s > %s\n" % (self.hitsOutput, self.inputToGenCalib)
        # Run getP0DSandMuonBarEndHits
        command += "getP0DSandMuonBarEndHits.exe -o %s %s"%(self.hitsOutput,input_filelist)
        rtc = self.RunCommand(command)
        if rtc:
            print("failed in executing command")


def main(argv):
    # Parser Options
    ########################################################################
    parser = optparse.OptionParser()

    # example version is v12r15 or v11r31
    parser.add_option("-v", "--version", dest="version",
                      type="string", help="Version of nd280 software to use")
    parser.add_option("-i", "--input", dest="input",
                      type="string",
                      help="Input to process, must be an lfn")
    
    #parser.add_option("--useTestDB", action='store_true', default=False,
    #                  help="Prepend the DB cascade with the test DB")

    (options, args) = parser.parse_args()

    if not options.version:
        print 'Please enter a version of the ND280 Software to use'
        parser.print_help()
        return

    # Main Program
    ########################################################################
    P0Dcalib = P0DBarEndCalib(options.version)
    P0Dcalib.RunGetHits(options.input)


if __name__ == "__main__":
    main(sys.argv[1:])
