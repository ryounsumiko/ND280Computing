#!/usr/bin/env python2

import sys
import re
import tempfile
import os
import optparse
import shutil
import random
from ND280GRID import ND280File, GetRandomSeed

########################################################################################################################
################################################ GENIE configs #########################################################
########################################################################################################################

class ND280Config:


    """
    A class to handle automatically creating nd280Control config files.

    Types

    gnsetup = GENIE setup config
    gnmc    = GENIE MC config
    raw     = Raw data config

    Defaults

    General

    cmtpath = environment
    cmtroot = environment

    gnsetup

    genie_setup_script = $T2K_ORG_VO_SW_DIR/GENIE/setup.sh

    gnmc

    genie_setup_script = $T2K_ORG_VO_SW_DIR/GENIE/setup.sh
    neutrino_type      = beam
    flux_tree          = h3002

    gncp

    module_list            = oaCherryPicker nd280MC elecSim oaCalibMC oaRecon oaAnalysis
    num_events             = 999999999 (I.e. exhaust all events)
    mc_full_spill          = 0
    time_offset            = 50
    mc_position            = free
    interactions_per_spill = 1
    count_type             = FIXED

    raw

    module_list              = oaUnpack oaCalib oaRecon oaAnalysis
    use_grid                 = 1
    register_files           = 1
    register_catalogue_files = 0

    An example use:

    >>> import ND280Configs
    >>> cfg = ND280Configs.ND280Config('gnmc','test_gnmc.cfg')
    >>> cfg.ListOptions()
        comment =
        cmtpath = environment
        random_seed =
        p0d_water_fill =
        neutrino_type = beam
        genie_paths =
        cmtroot = environment
        flux_file =
        flux_tree = h3002
        run_number =
        baseline =
        genie_setup_script = /data/t2k/ND280_soft//GENIE/setup.sh
        nd280ver =
        master_volume =
        subrun =
        genie_xs_table =
        pot =
    >>> cfg.options['random_seed']='3456532423'
    >>> cfg.options['p0d_water_fill']='1'
    >>> cfg.options['genie_paths']='/some/path/geniepaths.root'
    >>> cfg.options['flux_file']='/data/still/FluxFiles/10a/nd6/flux_10a_nd6_1/nu.nd6_horn250ka.1.root'
    >>> cfg.options['genie_paths']='/data/still/GENIE/test/genie_nd280_Magnet_paths_2.6.0.xml'
    >>> cfg.options['run_number']='91000099'
    >>> cfg.options['subrun']='0'
    >>> cfg.options['genie_xs_table']='/data/still/GENIE/test/gxspl-t2k-v2.6.0.xml'
    >>> cfg.options['baseline']='2010-02'
    >>> cfg.options['master_volume']='Magnet'
    >>> cfg.options['nd280ver']='v7r21p1'
    >>> cfg.options['pot']='5E+17'

    """

    def __init__(self, cfgtype, filename):
        self.t2ksoftdir = os.getenv("VO_T2K_ORG_SW_DIR")
        if not self.t2ksoftdir:
            self.t2ksoftdir = os.getenv("VO_T2K_SW_DIR")
        if not self.t2ksoftdir:
            sys.exit("Could not get T2K software directory Env Var")

        self.cfgtype = cfgtype

        self.options        = self.common_options
        self.options_ignore = self.common_options_ignore

        if self.cfgtype == 'gnsetup':
            self.options.update(self.genieSetupt_options)
            self.options['genie_setup_script']=self.t2ksoftdir + '/GENIE/setup.sh'
        elif self.cfgtype == 'gnmc':
            self.options.update(self.genieMC_options)
            self.options['genie_setup_script']=self.t2ksoftdir + '/GENIE/setup.sh'
        elif self.cfgtype == 'Raw':
            self.options.update(self.raw_options)
            self.options_ignore.update(self.raw_options_ignore)
        elif self.cfgtype == 'gncp':
            self.options.update(self.gncp_options)
        elif self.cfgtype == 'MC':
            self.options.update(self.mc_options)
        elif self.cfgtype == 'PG':
            self.options.update(self.pg_options)
        elif self.cfgtype == 'nusetup':
            self.options.update(self.neutSetup_options)
        elif self.cfgtype == 'numc':
            self.options.update(self.neutMC_options)
        else:
            sys.exit('Not a recognised config type %s' % cfgtype)
        self.config_filename=filename

    ### Global
    cfgtype         = ''
    config_filename = ''
    t2ksoftdir      = ''
    options         = {}
    ##################
    ### Options
    ### Common Options: Dictionary of common options amongst all config files
    common_options = {
        'cmtpath'                  :'environment',
        'cmtroot'                  :'environment',
        'nd280ver'                 :'',
        'custom_list'              :'',
        'db_time'                  :''
        }


    ## Ignore options - options that are not essential and can be overlooked
    common_options_ignore = {
        'comment'        :'',
        'midas_file'     :'',
        'event_select'   :'',
        'inputfile'      :'',
        'version_number' :'',
        'custom_list'    :'',
        'db_time'        :''
        }

    ### Raw Data Options: Dictionary of options specific to Raw data processing cfg files
    raw_options = {
        'midas_file'        :'',
        'comment'           :'',
        'event_select'      :'',
        'module_list'       :'oaUnpack oaCalib oaRecon oaAnalysis',
        'version_number'    :'',
        'inputfile'         :'',
        'enable_modules'    :'',
        'disable_modules'   :'',
        'process_truncated' :'',
        'num_events'        :''
        }

    raw_options_ignore = {
        'enable_modules'    :'',
        'disable_modules'   :'',
        'process_truncated' :'',
        'num_events'        :''
        }

    #### MC
    mc_options = {
        'module_list'                          :'nd280MC elecSim oaCalibMC oaRecon oaAnalysis',
        'inputfile'                            :'/lustre/ific.uv.es/sw/t2k.org/nd280Soft/nd280computing/processing_scripts/oa_nt_beam_90210013-0100_3ravbul66rum_numc_000_prod004magnet201011waterb.root',
        'run_number'                           :'90210000',
        'subrun'                               :'0',
        'baseline'                             :'2010-11',
        'p0d_water_fill'                       :'1',
        'num_events'                           :'100000000',
        'mc_type'                              :'Neut_RooTracker',
        #'nd280mc_random_seed'                  :str(random.getranbits(29)),
        'nd280mc_random_seed'                  :'123456',
        'nbunches'                             :'8',
        # for production 5
        'interactions_per_spill'               :'9.2264889',
        'pot_per_spill'                        :'7.9891e+13',
        'mc_full_spill'                        :'1',
        'time_offset'                          :'50',
        'count_type'                           :'MEAN',
        'mc_position'                          :'free',
        'bunch_duration'                       :'19',
        # for production 6
        'ecal_periods_to_activate'             :'1-2',
        'tpc_periods_to_activate'              :'runs2-3',
        # 'elmc_random_seed'                     :str(random.getrandbits(28)),
        'elmc_random_seed'                     :'654321',
        'production'                           :'1',
        'comment'                              :''}


    ### GENIE Setup Options: Dictionary of options specific to GENIE setup cfg files
    genieSetup_options = {
        'baseline'           :'',
        'p0d_water_fill'     :'',
        'genie_xs_table'     :'',
        'master_volume'      :'',
        'genie_setup_script' :''
        }

    ### GENIE MC Options: Dictionary of options specific to GENIE MC cfg files
    genieMC_options = {
        'baseline'           :'',
        'p0d_water_fill'     :'',
        'genie_xs_table'     :'',
        'master_volume'      :'',
        'genie_setup_script' :'',
        'run_number'         :'',
        'subrun'             :'',
        'comment'            :'',
        'neutrino_type'      :'beam',
        'flux_file'          :'',
        'flux_tree'          :'h3002',
        'pot'                :'',
        'genie_paths'        :'',
        'random_seed'        :''}

    gncp_options = {
        'module_list'            :'oaCherryPicker nd280MC elecSim oaCalibMC oaRecon oaAnalysis',
        'run_number'             :'',
        'subrun'                 :'',
        'comment'                :'',
        'baseline'               :'',
        'p0d_water_fill'         :'',
        'num_events'             :'999999999',
        'nd280mc_random_seed'    :'',
        'mc_full_spill'          :'0',
        'time_offset'            :'50',
        'mc_position'            :'free',
        'interactions_per_spill' :'1',
        'count_type'             :'FIXED',
        'elmc_random_seed'       :'',
        'cherry_picker_type'     :''
        }

    ### GRID options are not considered compulsory but I include here for totality.
    grid_options = {
        'use_grid'                 :'0',
        'storage_address'          :'',
        'register_address'         :'',
        'register_files'           :'1',
        'register_catalogue_files' :'0'
        }

    ### Particle Gun options
    pg_options = {
        'geo_baseline'           :'2010-02',
        'p0d_water_fill'         :'1',
        'module_list'            :'nd280MC elecSim oaCalibMC oaRecon oaAnalysis',
        'comment'                :'',
        'num_events'             :'10000',
        'mc_particle'            :'mu-',
        'mc_position'            :'SUBDETECTOR p0d',
        'mc_energy'              :'uniform 500 1000',
        'mc_direction'           :'ISOTROPIC',
        'nd280mc_random_seed'    :'999',
        'interactions_per_spill' :'1',
        'nbunches'               :'1',
        'elmc_random_seed'       :'999'
        }

    ### neutSetup options
    neutSetup_options = {
        'neut_setup_script' : '',
        'baseline'          : '2010-11',
        'p0d_water_fill'    : '1',
        'module_list'       : 'neutSetup',
        'run_number'        : '0',
        'subrun'            : '0',
        'comment'           : '',
        'neutrino_type'     : 'beam',
        'master_volume'     : 'Magnet',
        'flux_region'       : 'magnet',
        'flux_file'         : '',
        'maxint_file'       : '',
        'pot'               : '5E17',
        'random_start'      : '1',
        'random_seed'       : '1234',
        'neut_seed1'        : '5678',
        'neut_seed2'        : '9101',
        'neut_seed3'        : '1121'
        }

    ### neutMC options
    neutMC_options    = {}


    def StdOut(self):
        sys.stdout.flush()
        if(os.path.isfile(self.config_filename)):
           print ''.join(open(self.config_filename,'r').readlines())

    def CheckOptions(self):
        allOK=1
        sys.stdout.flush()
        ## Quick check to see if there are any blank options, only allowed for comment.
        for k,v in self.options.iteritems():
            if not v:
                if k in self.options_ignore:
                    continue
                else:
                    print 'Please ensure a value for ' + k + ' using the object.options[\'' + k + '\']'
                    allOK=0

        return allOK

    def ListOptions(self):
        sys.stdout.flush()
        for k,v in self.options.iteritems():
            print '%25s = %s' % (k,v)
        return 0

    def SetOptions(self,options_in):
        sys.stdout.flush()
        for k,v in options_in.iteritems():
            if not k in self.options:
                print 'Inserting option ' + k + ' into list'
            print 'Setting option ' + k + ' = ' + v
            self.options[k]=v

    def CreateConfig(self):
        if self.cfgtype == 'gnsetup':
            self.CreateGENIEsetupCF()
        elif self.cfgtype == 'gnmc':
            self.CreateGENIEMCCF()
        elif self.cfgtype == 'Raw':
            self.CreateRawCF()
        elif self.cfgtype == 'gncp':
            self.CreateGENIECPCF()
        elif self.cfgtype =='PG':
            self.CreatePGsetupCF()
        elif self.cfgtype == 'MC':
            self.CreateMCCF()
        elif self.cfgtype == 'nusetup':
            self.CreateNEUTSetupCF()
        else:
            sys.exit('Not a reconised config type')


    ######################## MC
    def CreateMCCF(self):
        sys.stdout.flush()
        if not self.cfgtype=='MC':
            print 'ERROR attempting to make a MC config when specified type is ' + self.cfgtype
            return ''
        if not self.CheckOptions():
            print 'ERROR please make sure all options stated above are entered'
            return ''
        self.ListOptions()
        try:
            configfile = open(self.config_filename,"w")
            print "Open config file for writing "
            configfile.write("# Automatically generated config file, from ND280Configs.CreateMCCF\n\n")

            ### Seed MC using sub+subrun - override defaults here
            f = ND280File(self.options['inputfile'])
            run    = f.GetRunNumber()
            subrun = f.GetSubRunNumber()

            self.options['nd280mc_random_seed'] = str(GetRandomSeed(run,subrun,'g4mc'))           # uint32
            self.options['elmc_random_seed']    = str(GetRandomSeed(run,subrun,'elmc',hexbits=7)) # int32

            ### Software Setup
            configfile.write("[software]\n")
            configfile.write("cmtpath = "  + self.options['cmtpath']  + "\n")
            configfile.write("cmtroot = "  + self.options['cmtroot']  + "\n")
            configfile.write("nd280ver = " + self.options['nd280ver'] + "\n\n")

            ### Configuration
            configfile.write('[configuration]\n')
            configfile.write("module_list = " + self.options['module_list'] + '\n')
            configfile.write("inputfile = "   + self.options['inputfile']   + '\n\n')

            ### File naming
            configfile.write("[filenaming]\n")
            configfile.write("comment = " + self.options['comment'] + "\n\n")


            ### Geometry
            configfile.write("[geometry]\n")
            configfile.write("baseline = "       + self.options['baseline']       + "\n")
            configfile.write("p0d_water_fill = " + self.options['p0d_water_fill'] + "\n\n")

            ### nd280mc
            configfile.write('[nd280mc]\n')
            configfile.write('num_events = '             + self.options['num_events']             + '\n')
            configfile.write('mc_type = '                + self.options['mc_type']                + '\n')
            configfile.write('random_seed = '            + self.options['nd280mc_random_seed']    + '\n')
            configfile.write('nbunches = '               + self.options['nbunches']               + '\n')
            configfile.write('interactions_per_spill = ' + self.options['interactions_per_spill'] + '\n')
            configfile.write('pot_per_spill = '          + self.options['pot_per_spill']          + '\n')
            configfile.write('bunch_duration = '         + self.options['bunch_duration']         + '\n')
            configfile.write('mc_full_spill = '          + self.options['mc_full_spill']          + '\n')
            configfile.write('time_offset = '            + self.options['time_offset']            + '\n')
            configfile.write('count_type = '             + self.options['count_type']             + '\n')
            configfile.write('mc_position = '            + self.options['mc_position']            + '\n\n')

            ### elecSim
            configfile.write('[electronics]\n')
            configfile.write('random_seed = ' + self.options['elmc_random_seed'] + '\n\n')

            ### production
            configfile.write('[analysis]\n') # new for P6
            configfile.write('production = ' + self.options['production'] + '\n')
            configfile.write('save_geometry = 1\n')

            ### dead channels
            if 'tpc_periods_to_activate' in self.options or 'ecal_periods_to_activate' in self.options:
                configfile.write('\n[dead_channels]\n')
            if 'tpc_periods_to_activate' in self.options:
                configfile.write('tpc_periods_to_activate = ' + self.options['tpc_periods_to_activate'] +'\n')
            if 'ecal_periods_to_activate' in self.options:
                configfile.write('ecal_periods_to_activate = ' + self.options['ecal_periods_to_activate'] +'\n')


            configfile.close()
            return self.config_filename
        except:
            configfile.close()
            print "Could not write the config file " + self.config_filename
            print open(self.config_filename,"r").readlines()
            sys.exit(1)
        return ''

    def CreatePGsetupCF(self):
        sys.stdout.flush()
        if not self.cfgtype=='PG':
            print 'ERROR attempting to make a particle gun config when specified type is ' + self.cfgtype
            return ''
        if not self.CheckOptions():
            print 'ERROR please make sure all options stated above are entered'
            return ''

        try:
            configfile = open(self.config_filename,"w")
            configfile.write("# Automatically generated config file, from ND280Configs.CreatePGsetupCF\n\n")

            configfile.write("[software]\n")
            configfile.write("cmtpath = "  + self.options['cmtpath']  + "\n")
            configfile.write("cmtroot = "  + self.options['cmtroot']  + "\n")
            configfile.write("nd280ver = " + self.options['nd280ver'] + "\n")

            ### Geometry
            configfile.write("[geometry]\n")
            configfile.write("baseline = "       + self.options['geo_baseline']   + "\n")
            configfile.write("p0d_water_fill = " + self.options['p0d_water_fill'] + "\n\n")

            ### Modules
            configfile.write("[configuration]\n")
            configfile.write("module_list = " + self.options['module_list'] + "\n\n")

            ### File naming
            configfile.write("[filenaming]\n")
            configfile.write("run_number = 0\n")
            configfile.write("subrun = 0\n")
            if self.options['comment']:
                configfile.write("comment = " + self.options['comment'] + "\n\n")

            configfile.write("[nd280mc]\n")
            configfile.write("num_events = "              + self.options['num_events']            + '\n')
            configfile.write("mc_type = ParticleGun\n")
            configfile.write("mc_particle = "             + self.options['mc_particle']            + '\n')
            configfile.write("mc_position = "             + self.options['mc_position']            + '\n')
            configfile.write("mc_energy = "               + self.options['mc_energy']              + '\n')
            configfile.write("mc_direction = "            + self.options['mc_direction']           + '\n')
            configfile.write('random_seed = '             + self.options['nd280mc_random_seed']    + '\n')
            configfile.write("interactions_per_spill = "  + self.options['interactions_per_spill'] + '\n')
            configfile.write('pot_per_spill = '           + self.options['pot_per_spill']          + '\n')
            configfile.write("nbunches = "                + self.options['nbunches']               + '\n\n')


            configfile.write('[electronics]\n')
            configfile.write('random_seed = ' + self.options['elmc_random_seed'] + '\n\n')

            configfile.close()
            return self.config_filename
        except:
            configfile.close()
            print "Could not write the config file " + self.config_filename
            print open(self.config_filename,"r").readlines()
            sys.exit(1)

        return ""


    ######################## GENIE Setup
    def CreateGENIEsetupCF(self):
        sys.stdout.flush()
        if not self.cfgtype=='gnsetup':
            print 'ERROR attempting to make a GENIE setup config when specified type is ' + self.cfgtype
            return ''
        if not self.CheckOptions():
            print 'ERROR please make sure all options stated above are entered'
            return ''

        try:
            configfile = open(self.config_filename,"w")
            configfile.write("# Automatically generated config file, from ND280Configs.CreateGENIEsetupCF\n\n")

            configfile.write("[software]\n")
            configfile.write("cmtpath = "            + self.options['cmtpath']            + "\n")
            configfile.write("cmtroot = "            + self.options['cmtroot']            + "\n")
            configfile.write("nd280ver = "           + self.options['nd280ver']           + "\n")
            configfile.write("genie_setup_script = " + self.options['genie_setup_script'] + "\n\n")

            ### Geometry
            configfile.write("[geometry]\n")
            configfile.write("baseline = "       + self.options['geo_baseline']   + "\n")
            configfile.write("p0d_water_fill = " + self.options['p0d_water_fill'] + "\n\n")

            ### Modules
            configfile.write("[configuration]\n")
            configfile.write("module_list = genieSetup\n\n")

            ### File naming
            configfile.write("[filenaming]\n")
            configfile.write("run_number = 0\n")
            configfile.write("subrun = 0\n\n")


            configfile.write("[neutrino]\n")
            configfile.write("genie_xs_table = " + self.options['genie_xs_table'] + "\n")
            configfile.write("master_volume = "  + self.options['master_vol'] + "\n")

            configfile.close()
            return self.config_filename
        except:
            configfile.close()
            print "Could not write the config file " + self.config_filename
            print open(self.config_filename,"r").readlines()
            sys.exit(1)

        return ""

    ######################## GENIE MC
    def CreateGENIEMCCF(self):
        sys.stdout.flush()
        if not self.cfgtype=='gnmc':
            print 'ERROR attempting to make a GENIE MC config when specified type is ' + self.cfgtype
            return ''
        if not self.CheckOptions():
            print 'ERROR please make sure all options stated above are entered'
            return ''

        try:
            configfile = open(self.config_filename,"w")
            configfile.write("# Automatically generated config file, from ND280Configs.CreateGENIECF\n\n")

            configfile.write("[software]\n")
            configfile.write("cmtpath = "            + self.options['cmtpath']            + "\n")
            configfile.write("cmtroot = "            + self.options['cmtroot']            + "\n")
            configfile.write("nd280ver = "           + self.options['nd280ver']           + "\n")
            configfile.write("genie_setup_script = " + self.options['genie_setup_script'] + "\n\n")

            ### Module list
            configfile.write("[configuration]\n")
            configfile.write("module_list = genieMC genieConvert\n\n")

            ### File naming
            configfile.write("[filenaming]\n")
            configfile.write("run_number = " + self.options['run_number'] + "\n")
            configfile.write("subrun = "     + self.options['subrun']     + "\n")
            configfile.write("comment = "    + self.options['comment']    + "\n\n")

            ### Geometry
            configfile.write("[geometry]\n")
            configfile.write("baseline = "       + self.options['baseline']       + "\n")
            configfile.write("p0d_water_fill = " + self.options['p0d_water_fill'] + "\n\n")

            ### Neutrino
            configfile.write("[neutrino]\n")
            configfile.write("neutrino_type = "   + self.options['neutrino_type']  + "\n") ## beam
            configfile.write("flux_region = "     + self.options['master_volume']  + "\n")
            configfile.write("flux_file = "       + self.options['flux_file']      + "\n")
            configfile.write("flux_tree = "       + self.options['flux_tree']      + "\n") ## h3002
            configfile.write("pot = "             + self.options['pot']            + "\n")
            configfile.write("genie_xs_table = "  + self.options['genie_xs_table'] + "\n")
            configfile.write("genie_paths = "     + self.options['genie_paths']    + "\n")
            configfile.write("random_seed = "     + self.options['random_seed']    + "\n")
            configfile.write("master_volume = "   + self.options['master_volume']  + "\n")

            configfile.close()
            return self.config_filename
        except:
            configfile.close()
            print "Could not write the config file " + self.config_filename
            print open(self.config_filename,"r").readlines()
            sys.exit(1)

        return ""

    ########################################################################################################################
    ######################## Raw Data Processing Config file
    def CreateRawCF(self):
        print 'CreateRawCF()'

        sys.stdout.flush()
        if not self.cfgtype=='Raw':
            print 'ERROR attempting to make a raw config when specified type is ' + self.cfgtype
            return ''
        if not self.CheckOptions():
            print 'ERROR please make sure all options stated above are entered'
            return ''

        try:
            configfile = open(self.config_filename,"w")
            configfile.write("# Automatically generated config file, from ND280Configs.CreateRawCF\n\n")

            ### Software Setup
            configfile.write("[software]\n")
            configfile.write("cmtpath = "  + self.options['cmtpath']  + "\n")
            configfile.write("cmtroot = "  + self.options['cmtroot']  + "\n")
            configfile.write("nd280ver = " + self.options['nd280ver'] + "\n\n")

            ### File naming
            if not self.options['comment']:
                 self.options['comment'] =  self.options['nd280ver']
            configfile.write("[filenaming]\n")
            if self.options['inputfile']:
                print "version_number = "            + self.options['version_number'] + "\n"
                configfile.write("version_number = " + self.options['version_number'] + "\n")
            configfile.write("comment = "            + self.options['comment']        + "\n\n")

            ### Module list
            configfile.write("[configuration]\n")
            if not self.options['midas_file']:
                configfile.write("inputfile = " + self.options['inputfile']   + "\n")
            configfile.write("module_list = "   + self.options['module_list'] + "\n\n")

            if self.options['db_time']:
                configfile.write("database_rollback_date = "    + self.options['db_time'] + " 00:00:00\n")
                configfile.write("dq_database_rollback_date = " + self.options['db_time'] + " 00:00:00\n")
                configfile.write("\n")

            ### oaAnalysis
            configfile.write("[analysis]\n")
            configfile.write('save_geometry = 1\n') # new for P6
            if self.options['enable_modules']:
                configfile.write("enable_modules = "  + self.options['enable_modules']  + "\n")
            if self.options['disable_modules']:
                configfile.write("disable_modules = " + self.options['disable_modules'] + "\n")
            configfile.write("\n")

            ### Unpack - only if this is a midas file
            if self.options['midas_file']:
                configfile.write("[unpack]\n")
                configfile.write("midas_file = "   + self.options['midas_file']   + "\n")
                configfile.write("event_select = " + self.options['event_select'] + "\n")

                if self.options['process_truncated']:
                    configfile.write("process_truncated = " + self.options['process_truncated'] + "\n")
                    configfile.write("\n")
                if self.options['num_events']:
                    configfile.write("num_events = " + self.options['num_events'] + "\n")

            ### GRID Tools
            if 'use_grid' in self.options:
                configfile.write("[grid_tools]\n")
                for o in ('use_grid', 'storage_address', 'register_files', 'register_catalogue_files', 'register_address'):
                    if self.options[o]:
                        configfile.write("%s = %s \n" % (o,self.options[o]))
                        
            ### Custom options
            if 'custom_list' in self.options:
                print 'Detected custom_list'
                configfile.write('\n')
                configlist = self.options['custom_list'].split(',')
                for confline in configlist:
                    configfile.write(str(confline)+"\n")
                configfile.write('\n')

            ### dead channels MC only..
#             if 'tpc_periods_to_activate' in self.options or 'ecal_periods_to_activate' in self.options:
#                 configfile.write('\n[dead_channels]\n')
#             if 'tpc_periods_to_activate' in self.options:
#                 configfile.write('tpc_periods_to_activate =' + self.options['tpc_periods_to_activate'] +'\n')
#             if 'ecal_periods_to_activate' in self.options:
#                 configfile.write('ecal_periods_to_activate = ' + self.options['ecal_periods_to_activate'] +'\n')

            print configfile
            configfile.close()
            print 'DUMPING CONFIG FILE'
            with open(self.config_filename, 'r') as fp:  
                 line = fp.readline()
                 cnt = 1
                 while line:
                     print("Line {}: {}".format(cnt, line.strip()))
                     line = fp.readline()
                     cnt += 1
            return self.config_filename
        except:
            configfile.close()
            print "Could not write the config file " + self.config_filename
            print open(self.config_filename,"r").readlines()
            sys.exit(1)

    ########################################################################################################################
    ######################## Cherry Picker
    def CreateGENIECPCF(self):
        sys.stdout.flush()
        if not self.cfgtype=='gncp':
            print 'ERROR attempting to make a raw config when specified type is ' + self.cfgtype
            return ''
        if not self.CheckOptions():
            print 'ERROR please make sure all options stated above are entered'
            return ''

        try:
            configfile = open(self.config_filename,"w")
            configfile.write("# Automatically generated config file, from ND280Configs.CreateGENIECPCF\n\n")

            ### Software Setup
            configfile.write("[software]\n")
            configfile.write("cmtpath = " + self.options['cmtpath'] + "\n")
            configfile.write("cmtroot = " + self.options['cmtroot'] + "\n")
            configfile.write("nd280ver = " + self.options['nd280ver'] + "\n\n")


            configfile.write('[configuration]\n')
            configfile.write("module_list = " + self.options['module_list'] + '\n\n')

            ### File naming
            configfile.write("[filenaming]\n")
            configfile.write("run_number = " + self.options['run_number'] + "\n")
            configfile.write("subrun = " + self.options['subrun'] + "\n")
            configfile.write("comment = " + self.options['comment'] + "\n\n")

            ### Geometry
            configfile.write("[geometry]\n")
            configfile.write("baseline = " + self.options['baseline'] + "\n")
            configfile.write("p0d_water_fill = " + self.options['p0d_water_fill'] + "\n\n")

            ### nd280mc
            configfile.write('[nd280mc]\n')
            configfile.write('num_events = '             + self.options['num_events']             + '\n')
            configfile.write('mc_type = Genie\n')
            configfile.write('random_seed = '            + self.options['nd280mc_random_seed']    + '\n')
            configfile.write('mc_full_spill = '          + self.options['mc_full_spill']          + '\n')
            configfile.write('time_offset = '            + self.options['time_offset']            + '\n')
            configfile.write('mc_position = '            + self.options['mc_position']            + '\n')
            configfile.write('interactions_per_spill = ' + self.options['interactions_per_spill'] + '\n')
            configfile.write('pot_per_spill = '          + self.options['pot_per_spill']          + '\n')
            configfile.write('count_type = '             + self.options['count_type']             + '\n\n')

            configfile.write('[electronics]\n')
            configfile.write('random_seed = ' + self.options['elmc_random_seed'] + '\n\n')

            configfile.write('[cherry_picker]\n')
            if self.options['cherry_picker_type']=='ncpi0':
                configfile.write('num_mesons = 0\n')
                configfile.write('num_leptons = 0\n')
                configfile.write('num_pizero = 1\n')
            elif self.options['cherry_picker_type']=='ccpi0':
                configfile.write('num_mesons = 0\n')
                configfile.write('num_leptons = 1\n')
                configfile.write('num_pizero = 1\n')
            else:
                sys.exit('ERROR Incorrect cherry_picker_type specified: ' + self.options['cherry_picker_type'])
##                 configfile.write('num_mesons = '  + self.options['num_mesons'] )
##                 configfile.write('num_leptons = ' + self.options['num_leptons'])
##                 configfile.write('num_pizero = '  + self.options['num_pizero'] )

            configfile.write('inputfile_list = ' + self.options['inputfile_list'])
            configfile.close()
            return self.config_filename
        except:
            configfile.close()
            print "Could not write the config file " + self.config_filename
            print open(self.config_filename,"r").readlines()
            sys.exit(1)

        return ''


    def CreateNEUTSetupCF(self):
        sys.stdout.flush()
        if not self.cfgtype=='nusetup':
            print 'ERROR attempting to make a NEUT setup config when specified type is ' + self.cfgtype
            return ''
        if not self.CheckOptions():
            print 'ERROR please make sure all options stated above are entered'
            return ''

        run    = self.options['run_number']
        subrun = self.options['subrun']

        try:
            configfile = open(self.config_filename,"w")
            configfile.write("# Automatically generated config file, from ND280Configs.CreateNEUTsetupCF\n\n")

            ### Software
            configfile.write("[software]\n")
            configfile.write("cmtpath = "            + self.options['cmtpath'           ] + "\n")
            configfile.write("cmtroot = "            + self.options['cmtroot'           ] + "\n")
            configfile.write("nd280ver = "           + self.options['nd280ver'          ] + "\n")
            configfile.write("neut_setup_script = "  + self.options['neut_setup_script' ] + "\n")
            configfile.write("flux_file = "          + self.options['flux_file'         ] + "\n\n")

            ### Geometry
            configfile.write("[geometry]\n")
            configfile.write("baseline = "       + self.options['baseline' ]      + "\n")
            configfile.write("p0d_water_fill = " + self.options['p0d_water_fill'] + "\n\n")

            ### Configuration
            configfile.write("[configuration]\n")
            configfile.write("module_list = " + self.options['module_list'] + "\n\n")

            ### File naming
            configfile.write("[filenaming]\n")
            configfile.write("run_number = " + run                     + "\n"  )
            configfile.write("subrun = "     + subrun                  + "\n"  )
            configfile.write("comment = "    + self.options['comment'] + "\n\n")

            ### Neutrino
            configfile.write("[neutrino]\n")
            configfile.write("neutrino_type = " + self.options['neutrino_type']          + "\n"  )     # Must be one of NUE, NUEBAR, NUMU, NUMUBAR or BEAM for all.
            configfile.write("master_volume = " + self.options['master_volume']          + "\n"  )
            configfile.write("flux_region = "   + self.options['flux_region'  ]          + "\n"  )
            configfile.write("flux_file = "     + self.options['flux_file'    ]          + "\n"  )
            configfile.write("maxint_file = "   + self.options['maxint_file'  ]          + "\n"  )
            configfile.write("pot = "           + self.options['pot'          ]          + "\n"  )
            configfile.write("random_start = "  + self.options['random_start' ]          + "\n"  )
            configfile.write("random_seed = "   + str(GetRandomSeed(run,subrun,'numc0')) + "\n"  )
            configfile.write("neut_seed1 = "    + str(GetRandomSeed(run,subrun,'numc1')) + "\n"  )
            configfile.write("neut_seed2 = "    + str(GetRandomSeed(run,subrun,'numc2')) + "\n"  )
            configfile.write("neut_seed3 = "    + str(GetRandomSeed(run,subrun,'numc3')) + "\n\n")

            ### nd280_mc
            configfile.write("[nd280mc]\n")
            configfile.write("mc_type = Neut_RooTracker\n\n")

            configfile.close()
            return self.config_filename
        except:
            configfile.close()
            print "Could not write the config file CreateNEUTsetupCF() " + self.config_filename
            print open(self.config_filename,"r").readlines()
            sys.exit(1)

        return ""
