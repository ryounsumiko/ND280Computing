# ND280Computing

Source the setup.sh while in the ND280Computing directory in which it resides to
set the python path '''PYTHONPATH''' environment variable to look in the tools
directory for the ND280Computing tools.

The intention of this package is to contain scripts and tools used by the people
involved in the ND280Computing group. The core of the package is written in
Python v2 but shell scripts and Perl scripts are welcome; anything and
everything to make the job of those doing computing easier.

CERN Virtual Machine
====================

This software assumes you have a working installation of the CERN virtual
machine file system (CVMFS) for T2K. The documentation on t2k.org is located
here

https://www.t2k.org/nd280/datacomp/cvmfs

Grid Certificates and DIRAC
===========================

In order to utilize the Grid resources, you must have a valid Grid certificate
and production role. The instructions for obtaining a certificate are outlined
on t2k.org under the Data Distribution and Computing group. To gain the
production role, contact the Computing group.

Assuming you have a valid certificate and it is installed on your browser,
you will need to install DIRAC, a middleware software to initiate a Grid proxy
and submit jobs. To install DIRAC, go to the doc directory and follow the
instructions under dirac_installation.md.

Structure
=========
```
ND280Computing
│   README.md
│   setup.sh
│
└───tools  # A collection of methods/classes/tools to generally make life easier
|          # to be used in many of the scripts
│   ND280Computing.py
│   ND280Grid.py
|   ND280DIRACAPI.py
|   ...
│   
└───installation_scripts  # A collection of automated installation scripts for
|                         # the ND280, GENIE and NEUT software
|       
└───processing_scripts  # A collection of submission and bookkeeping scripts
|                       # for processing
|   TutorialProcess.py
|   RunCustom.py
|   CalibProcess.py
|   P0DCalibProcess.py
|   ...
|    
└───data_scripts:  # A collection of scripts designed to initiate, monitor and
|                  # and bookkeep the transfer of data
└───custom_parameters  # Files that specify runND280 settings like ECal and P0D
|                      # timing calibrations
|  	ECALMOD.PARAMETERS.DAT   
|  	P0DMOD.PARAMETERS.DAT   
|
└───docs  # Thorough documentation
|
└───test_jobs  # examples to submit jobs using DIRAC

```

Job Submission
==============

Before submitting any job proxies must be generated for user credentials.

Firstly create 24hr dirac-proxy via the following command assuming you have a
production role:

```bash
cd path/to/ND280Computing
source setup.sh
dirac-proxy-init -g t2k.org_production -M -v 24:00
```

Or if you do not have production role, change "production" to "user"

```bash
dirac-proxy-init -g t2k.org_user -M -v 24:00
```

Go to test_jobs to test how to submit jobs

A more thorough example is to run this command in processing_scripts

```bash
./RunCustom.py -f filelist.dat -v v11r31 -x CalibProcess.py --dirac --sandbox=../custom_parameters/ECALMOD.PARAMETERS.DAT > RunCustom.out
```

which runs the CalibProcess.py script using the CVMFS ND280 software version
v11r31 with the ECALMOD.PARAMETERS.DAT file also uploaded to the computing
element. The filelist.dat contains a full logical file name (LFN) Grid path
to a raw file like so

lfn:/grid/t2k.org/nd280/raw/ND280/ND280/00014000_00014999/nd280_00014000_0000.daq.mid.gz

# DEPRECATED

The following description is kept for legacy support

Job Submission
==============

Before submitting any job proxies must be generated for user credentials.

Firstly create a voms-proxy via the following command:

$ voms-proxy-init -valid 24:0 -voms t2k.org

or if you have a role, E.g. production then:

$ voms-proxy-init -valid 24:0 -voms t2k.org:/t2k.org/Role=production

You will be prompted for your passphrase whvih you enetered when generating/backing up the certificate, and you should then see the output below:
Enter GRID pass phrase:
Your identity: /C=UK/O=eScience/OU=QueenMaryLondon/L=Physics/CN=benjamin still
Creating temporary proxy ........................................................................................................................................ Done
Contacting  voms.gridpp.ac.uk:15003 [/C=UK/O=eScience/OU=Manchester/L=HEP/CN=voms.gridpp.ac.uk/Email=ops@tier2.hep.manchester.ac.uk] "t2k.org" Done
Creating proxy ........................................................................................................................................... Done
Your proxy is valid until Thu Dec 16 22:23:39 2010

You must then produce a myproxy at the proxy server by doing:

$ myproxy-init -s lcgrbp01.gridpp.rl.ac.uk -d -n

Your identity: /C=UK/O=eScience/OU=QueenMaryLondon/L=Physics/CN=benjamin still
Enter GRID pass phrase for this identity:
Creating proxy ........................................................... Done
Proxy Verify OK
Your proxy is valid until: Wed Dec 22 22:25:15 2010
A proxy valid for 168 hours (7.0 days) for user /C=UK/O=eScience/OU=QueenMaryLondon/L=Physics/CN=benjamin still now exists on lcgrbp01.gridpp.rl.ac.uk.

This places authentication on a proxy server and the jobs submitted can recieve user credentials and authentication from this server, extending the proxy lifetime to 7 days.
A variable written into the JDL files lets the job know where to look for this authentication.

ND280Software
=============

If you wish to use this package locally you must set the environment variable VO_T2K_ORG_SW_DIR to poin to the directory where nd280 software resides:

I.e. version v8r5p7 of the software should be found at $VO_T2K_ORG_SW_DIR/nd280v8r5p7/ where the


To Install Software on the GRID
===============================

To install software on the GRID you must have lcgadmin privilages.

There is an example jdl file in the installation_scripts directory, ExampleND280_install.jdl. This JDL should just be modified by changing the version (v7r19p9) to the desired for installation.

After generating proxies (voms-proxy with lcgadmin Role) one just submits the job, while specifying the resource/CE.

$ glite-wms-job-submit -a -c autowms.conf -r <resource> -o install_nd280<version>.jid install_nd280<version>.jdl

<resource> list can be gained using lcg-infosites

$ lcg-infosites --vo t2k.org --list ce

#CPU	Free	Total Jobs	Running	Waiting	ComputingElement
----------------------------------------------------------
1528	   0	 197	        138	  59	heplnv142.pp.rl.ac.uk:8443/cream-pbs-grid
1528	 131	 575	        408	 167	heplnx207.pp.rl.ac.uk:2119/jobmanager-lcgpbs-grid500
1528	 131	 574	        407	 167	heplnx206.pp.rl.ac.uk:2119/jobmanager-lcgpbs-grid500
1528	 131	 576	        428	 148	heplnx206.pp.rl.ac.uk:2119/jobmanager-lcgpbs-grid1000
1528	 131	 576	        427	 149	heplnx207.pp.rl.ac.uk:2119/jobmanager-lcgpbs-grid1000
1528	 131	 715	        437	 278	heplnx207.pp.rl.ac.uk:2119/jobmanager-lcgpbs-grid2000
1528	 131	 715	        437	 278	heplnx206.pp.rl.ac.uk:2119/jobmanager-lcgpbs-grid2000
1954	1787	 167	        167	   0	cclcgceli03.in2p3.fr:2119/jobmanager-bqs-long
 182	 182	   0	          0	   0	cclcgceli03.in2p3.fr:2119/jobmanager-bqs-short
2983	2805	 113	        113	   0	ce04.esc.qmul.ac.uk:8443/cream-sge-lcg_long
2098	2098	   0	          0	   0	cclcgceli03.in2p3.fr:2119/jobmanager-bqs-medium
   0	   0	   0	          0	444444	gw-6.ccc.ucl.ac.uk:2119/jobmanager-lcgpbs-Gim
   0	   0	   0	          0	444444	gw-6.ccc.ucl.ac.uk:2119/jobmanager-lcgpbs-Reep
   0	   0	   0	          0	444444	gw-6.ccc.ucl.ac.uk:2119/jobmanager-lcgpbs-Rokk
   0	   0	   0	          0	444444	gw-6.ccc.ucl.ac.uk:2119/jobmanager-lcgpbs-Lyle
   0	   0	   0	          0	444444	hepgrid3.ph.liv.ac.uk:8443/cream-sge-HEP
   0	   0	   0	          0	444444	gw-6.ccc.ucl.ac.uk:2119/jobmanager-lcgpbs-Imra
   0	   0	   0	          0	444444	gw-6.ccc.ucl.ac.uk:2119/jobmanager-lcgpbs-Tinya
   0	   0	   0	          0	444444	gw-6.ccc.ucl.ac.uk:2119/jobmanager-lcgpbs-Garth
 568	 313	   0	          0	444444	hepgrid6.ph.liv.ac.uk:8443/cream-pbs-long
   0	   0	   0	          0	444444	gw-6.ccc.ucl.ac.uk:2119/jobmanager-lcgpbs-Chuck
2912	2876	  34	         34	   0	ce02.esc.qmul.ac.uk:2119/jobmanager-lcgsge-lcg_long
3019	2854	  93	         93	   0	ce03.esc.qmul.ac.uk:2119/jobmanager-lcgsge-lcg_long
   0	   0	   0	          0	444444	gw-6.ccc.ucl.ac.uk:2119/jobmanager-lcgpbs-Luornu
1613	 319	1295	       1295	   0	ceprod05.grid.hep.ph.ic.ac.uk:8443/cream-sge-grid.q
 632	   2	 348	        250	  98	t2ce06.physics.ox.ac.uk:8443/cream-pbs-longfive
1608	 314	1294	       1294	   0	ceprod04.grid.hep.ph.ic.ac.uk:2119/jobmanager-sge-long
 632	   2	 241	        183	  58	t2ce06.physics.ox.ac.uk:8443/cream-pbs-shortfive
1608	 317	1076	       1076	   0	ceprod03.grid.hep.ph.ic.ac.uk:2119/jobmanager-sge-long
 632	   2	 310	        197	 113	t2ce06.physics.ox.ac.uk:8443/cream-pbs-mediumfive
1613	 321	   2	          2	   0	ceprod03.grid.hep.ph.ic.ac.uk:2119/jobmanager-sge-short
1613	 317	   2	          2	   0	ceprod04.grid.hep.ph.ic.ac.uk:2119/jobmanager-sge-short
1608	 317	 218	        218	   0	ceprod03.grid.hep.ph.ic.ac.uk:2119/jobmanager-sge-medium
 568	 312	 257	        256	   1	hepgrid5.ph.liv.ac.uk:2119/jobmanager-lcgpbs-long
 496	 226	 141	        141	   0	fal-pygrid-44.lancs.ac.uk:2119/jobmanager-lcgpbs-q
 496	 226	 129	        129	   0	fal-pygrid-44.lancs.ac.uk:2119/jobmanager-lcgpbs-sg
 632	   2	 347	        250	  97	t2ce05.physics.ox.ac.uk:2119/jobmanager-lcgpbs-longfive
 632	   2	 241	        183	  58	t2ce05.physics.ox.ac.uk:2119/jobmanager-lcgpbs-shortfive
 632	   2	 310	        197	 113	t2ce05.physics.ox.ac.uk:2119/jobmanager-lcgpbs-mediumfive
4948	2080	   0	          0	   0	lcgce05.gridpp.rl.ac.uk:8443/cream-pbs-gridS
4948	2080	   1	          1	   0	lcgce05.gridpp.rl.ac.uk:8443/cream-pbs-grid500M
 836	 475	 355	        355	   0	ce02.tier2.hep.manchester.ac.uk:8443/cream-pbs-long
 960	 427	 533	        533	   0	ce01.tier2.hep.manchester.ac.uk:2119/jobmanager-lcgpbs-long
 404	 270	   0	          0	   0	lcgce1.shef.ac.uk:8443/cream-pbs-t2k
 404	 270	   0	          0	   0	lcgce0.shef.ac.uk:2119/jobmanager-lcgpbs-t2k

Ones we are interested installing at are:

T1
RAL 		lcgce05.gridpp.rl.ac.uk:8443/cream-pbs-grid500M
IN2P3		cclcgceli03.in2p3.fr:2119/jobmanager-bqs-long

T2
Sheffield	lcgce0.shef.ac.uk:2119/jobmanager-lcgpbs-t2k
Liverpool	hepgrid5.ph.liv.ac.uk:2119/jobmanager-lcgpbs-long
Lancaster	fal-pygrid-44.lancs.ac.uk:2119/jobmanager-lcgpbs-q
IC		ceprod04.grid.hep.ph.ic.ac.uk:2119/jobmanager-sge-long
QMUL		ce03.esc.qmul.ac.uk:2119/jobmanager-lcgsge-lcg_long
Oxford		t2ce05.physics.ox.ac.uk:2119/jobmanager-lcgpbs-longfive


$ND280JOBS/v#r#p#/

*.jid
*.jdl
*_<jobno>/
