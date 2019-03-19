#!/usr/bin/env python

import os
import sys
import optparse

from ND280Job import ND280Job

def appendLine(command,line):
    return command + line+"\n"


class P0DBarEndCalib(ND280Job):
    """Run P0DBarEndCalib"""
    def  __init__(self,nd280ver):
        super(P0DBarEndCalib,self).__init__(nd280ver)
        #Hard code intermidiate file name for simplicity.
        self.hitsOutput = "hits.root"
        self.inputToGenCalib = "file.txt"

    def CheckoutCodes(self):
        # Export LIBRARY_PATH for searching path when compiling
        command =""
        command += "export LIBRARY_PATH=$LD_LIBRARY_PATH\n"
        # Check out cvs package.
        command += "cmt checkout -r HEAD mppcCalib\n"
        command += "pushd mppcCalib/*/cmt\n"
        command += "cmt config\n"
        # Do compiling
        # Things may go wrong starting here
        command += "source ./setup.sh && "
        command += "cmt make && "
        command += "which getP0DSandMuonBarEndHits.exe && "
        command += "popd; exit $?"
        rtc = self.RunCommand(command)
        if rtc:
            print("failed in checkout codes")
            return False
        return True

    def RunGetHits(self,input_filelist):
        command =""
        #Create input for next stage.
        command += "echo `pwd`/%s > %s\n" % (self.hitsOutput, self.inputToGenCalib)
        # Run getP0DSandMuonBarEndHits
        command += "source ./mppcCalib/*/cmt/setup.sh\n"
        command += "getP0DSandMuonBarEndHits.exe -o %s %s" % (self.hitsOutput,input_filelist)
        rtc = self.RunCommand(command)
        if rtc:
            print("failed in executing getP0DSandMuonBarEndHits")
            return False
        return True

    def RunGenerateCalib(self,output_filename):
        command =""
        #Run genP0DBarEndCalib.exe
        command += "source ./mppcCalib/*/cmt/setup.sh\n"
        command += "genP0DBarEndCalib.exe -o %s %s" % (output_filename, self.hitsOutput)
        rtc = self.RunCommand(command)
        if rtc:
            print("failed in executing genP0DBarEndCalib")
            return False
        return True
    
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
    if not P0Dcalib.CheckoutCodes():
        return False
    P0Dcalib.RunGetHits(options.input.replace("lfn:","lfn:/"))


if __name__ == "__main__":
    main(sys.argv[1:])
