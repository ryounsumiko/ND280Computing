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

    def test_env():
        command = "echo $CVSROOT\n"
        command += "which getP0DSandMuonBarEndHits.exe"
        rtc = self.RunCommand(command)
        if rtc:
            print("failed in executing command")
    def Run():
        return


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
    nd280ver = options.version
    if not nd280ver:
        print 'Please enter a version of the ND280 Software to use'
        parser.print_help()
        return

    # Main Program
    ########################################################################
    P0Dcalib = P0DBarEndCalib(nd280ver)
    P0Dcalib.test_env()
    #P0Dcalib.Run()


if __name__ == "__main__":
    main(sys.argv[1:])
