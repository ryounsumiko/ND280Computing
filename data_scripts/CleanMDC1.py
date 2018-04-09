#!/usr/bin/python
"""
Cleanup script for MDC0 data in
srm://hepgrid11.ph.liv.ac.uk:8446/dpm/ph.liv.ac.uk/home/t2k.org/mdc0/

N.B. standard LFC dependent tools cannot be used due to presence of
large amounts of unregistered data.

Will delete all pre reco files, reco and anal files to be archived at RAL.
"""

import ND280GRID
from ND280GRID import runLCG
from ND280GRID import rmNL
from ND280GRID import IsValidProxy

import os

srm_a='srm://hepgrid11.ph.liv.ac.uk'
root_a='dpm/ph.liv.ac.uk/home/t2k.org'

srm_b='srm://srm-t2k.gridpp.rl.ac.uk'
root_b='castor/ads.rl.ac.uk/prod/t2k.org/nd280'

lfc_root='grid/t2k.org/nd280'

errors=[]
isCleaned=False
nIterations=0

while not isCleaned:
    try:
        nIterations += 1
        print 'Iteration '+str(nIterations)
        
        command='lcg-ls '+srm_a+'/'+root_a+'/mdc0'
        IsValidProxy()
        lines,errors = runLCG(command)
        if errors:
            raise exception
        
        #for line in lines:
        #    generator_dir = rmNL(line)
        #    
        #    command='lcg-ls '+srm_a+generator_dir
        #    IsValidProxy()
        #    lines,errors = runLCG(command)
        #    if errors:
        #        raise exception
    

        for line in lines:
            nd280_dir = rmNL(line)

            command='lcg-ls '+srm_a+nd280_dir
            IsValidProxy()
            lines,errors = runLCG(command)
            if errors:
                raise exception

            for line in lines:
                nd280_file = rmNL(line)

                if nd280_file == nd280_dir:
                    continue

                if not '/anal' in nd280_file and not '/reco' in nd280_file:
                    command = 'lcg-del -l '+srm_a+nd280_file
                    IsValidProxy()
                    lines,errors = runLCG(command)
                    #if errors:
                    #    raise exception
                else:
                    lfc_file = nd280_file.replace(root_a,lfc_root)
                    dest_file= srm_b+nd280_file.replace(root_a,root_b)
                    src_file = srm_a+nd280_file

                    command = 'lfc-ls '+lfc_file
                    IsValidProxy()
                    rtc = os.system(command)

                    if rtc:
                        command = 'lcg-rf -l '+lfc_file+' '+src_file
                        IsValidProxy()
                        lines,errors = runLCG(command)
                        #if errors:
                        #    raise exception

                        ## Throws up error 'Using grid catalog type: UNKNOWN'
                        ## even if successful so check exit code instead
                        command = 'lcg-rep -v -d '+dest_file+' '+src_file
                        IsValidProxy()
                        print 'Try '+command
                        rtc = os.system(command)
                        #if rtc:
                        #    raise exception

                        ## Check for existance of replica before proceeding
                        ## with deletion
                        command = 'lcg-ls '+dest_file
                        IsValidProxy()
                        lines,errors = runLCG(command)
                        if errors:
                            pass  # raise exception
                        else:
                            print 'Now deleting '+src_file
                            command = 'lcg-del '+src_file
                            IsValidProxy()
                            lines,errors = runLCG(command)
                            #if errors:
                            #    raise exception

        ## Finished if made it here:
        isCleaned=True
    
    except:
        print 'Exception'
        for error in errors:
            print error

print "MDC0 Data cleaned in "+str(nIterations)+" iterations!"
