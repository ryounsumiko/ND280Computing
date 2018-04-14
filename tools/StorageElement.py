#!/usr/bin/env python2

"""Storage Elements (SE) info in one convenient location"""
import os
from os import system, getenv
from os.path import join

import ND280GRID
import ND280Computing as ND280Comp


class units(object):
    """stores unit conversions for bytes"""

    def __init__(self, kilobyte=1.0):
        self.RescaleKilobyte(kilobyte)

    def RescaleKilobyte(self, kilobyte=1.0):
        """
        Set the scale for any unit storage
        If you want byte to be size 1, then Rescale(1000.)
        """

        self.kKilobyte = kilobyte
        # decimal units
        self.kMegabyte = 1.0e-03 * self.kKilobyte
        self.kGigabyte = 1.0e-03 * self.kMegabyte
        self.kTerabyte = 1.0e-03 * self.kGigabyte
        self.kByte = 1.0e+03 * self.kKilobyte
        self.kKB = self.kKilobyte
        self.kMB = self.kMegabyte
        self.kGB = self.kGigabyte
        self.kTB = self.kTerabyte

        # powers of 2
        self.kKibibyte = 1024 * self.kByte
        self.kMebibyte = 1024 * self.kKibibyte
        self.kGibibyte = 1024 * self.kMebibyte
        self.kTebibyte = 1024 * self.kGibibyte


# FORMAT se : [root, fts2Channel, hasSpaceToken]
class SE(object):
    """a container for Storage Element (SE) on Grid"""

    def __init__(self, name, root, fts2Channel, hasSpaceToken=True):
        self.name = name
        self.root = root
        self.f2C = fts2Channel
        self.hasSpaceToken = hasSpaceToken

    def GetList(self):
        "Get list of parameters"
        return [self.root, self.f2C, self.hasSpaceToken]

    def GetName(self):
        """Get name"""
        return self.name


ALL_SE = list()

RL = SE('srm-t2k.gridpp.rl.ac.uk',
        'srm://srm-t2k.gridpp.rl.ac.uk/\
castor/ads.rl.ac.uk/prod/t2k.org/nd280/', 'RALLCG2')
ALL_SE.append(RL)

# confirmed default location for new data
QMUL = SE('se03.esc.qmul.ac.uk',
          'srm://se03.esc.qmul.ac.uk/t2k.org/nd280/', 'UKILT2QMUL')
ALL_SE.append(QMUL)

CHEP = SE('gfe02.grid.hep.ph.ic.ac.uk',
          'srm://gfe02.grid.hep.ph.ic.ac.uk/\
pnfs/hep.ph.ic.ac.uk/data/t2k/nd280/', 'UKILT2ICHEP')
ALL_SE.append(CHEP)

NORTHGRIDLIV = SE('hepgrid11.ph.liv.ac.uk',
                  'srm://hepgrid11.ph.liv.ac.uk/\
dpm/ph.liv.ac.uk/home/t2k.org/nd280/', 'UKINORTHGRIDLIVHEP')
ALL_SE.append(NORTHGRIDLIV)

NORTHGRIDSHEF = SE('lcgse0.shef.ac.uk',
                   'srm://lcgse0.shef.ac.uk/\
dpm/shef.ac.uk/home/t2k.org/nd280/', 'UKINORTHGRIDSHEFHEP')
ALL_SE.append(NORTHGRIDSHEF)

# not yet implemented...
SOUTHGRIDOX = SE('t2se01.physics.ox.ac.uk',
                 'srm://t2se01.physics.ox.ac.uk/\
dpm/physics.ox.ac.uk/home/t2k.org/nd280/',
                 'UKISOUTHGRIDOXHEP', False)
ALL_SE.append(SOUTHGRIDOX)

# broke SRM
CCSRMFR = SE('ccsrm02.in2p3.fr',
             'srm://ccsrm02.in2p3.fr/\
pnfs/in2p3.fr/data/t2k/t2k.org/nd280/', 'IN2P3CC', False)
ALL_SE.append(CCSRMFR)

LANCS = SE('fal-pygrid-30.lancs.ac.uk',
           'srm://fal-pygrid-30.lancs.ac.uk/\
dpm/lancs.ac.uk/home/t2k.org/nd280/', 'UKINORTHGRIDLANCSHEP')
ALL_SE.append(LANCS)

T2KSRM = SE('t2ksrm.nd280.org',
            'srm://t2ksrm.nd280.org/nd280data/', 'CATRIUMFT2K', False)
ALL_SE.append(T2KSRM)

LUSTRE = SE('srmv2.ific.uv.es',
            'srm://srmv2.ific.uv.es/lustre/ific.uv.es/grid/t2k.org/nd280/', '')
ALL_SE.append(LUSTRE)

# confirmed default location for new data
SRMPIC = SE('srm.pic.es',
            'srm://srm.pic.es/pnfs/pic.es/data/t2k.org/nd280/', 'PIC')
ALL_SE.append(SRMPIC)

KEKSE = SE('kek2-se.cc.kek.jp',
           'srm://kek2-se.cc.kek.jp/t2k.org/nd280/', 'JPKEKCRC02', False)
ALL_SE.append(KEKSE)

KEKSE01 = SE('kek2-se01.cc.kek.jp',
             'srm://kek2-se01.cc.kek.jp/t2k.org/nd280/', 'JPKEKCRC02', False)
ALL_SE.append(KEKSE01)

# Master dictionary containing storage elements (SE) bindings
# FORMAT se : [root, fts2Channel, hasSpaceToken]
SE_MASTER = {}

for se in ALL_SE:
    key, value = se.GetName(), se.GetList()
    SE_MASTER[key] = value

# FTS channel name associated with each SRM
SE_CHANNELS = dict()

# Sites enabled with T2KORGDISK space token
SE_SPACETOKENS = dict()

# SRM root directories
SE_ROOTS = dict()

# FTS channel name associated with each SRM
SE_CHANNELS = dict()

# Sites enabled with T2KORGDISK space token
SE_SPACETOKENS = dict()

# Fill from master
for se, [root, channel, token] in SE_MASTER.iteritems():
    SE_ROOTS[se] = root
    SE_CHANNELS[se] = channel
    SE_SPACETOKENS[se] = token


def GetSEChannels():
    """simple get'er method for channel names associated with each SRM"""
    return SE_CHANNELS


def GetSERoots():
    """simple get'er method for SRM root directories"""
    return SE_ROOTS


def GetLiveSERoots():
    """ Compile the SE root-directory dictionary live from
    lcg-infosites rather than hard coding """
    print 'Getting live SE root directories'
    se_roots_live = dict()
    for se in GetListOfSEs():
        se_roots_live[se] = GetTopLevelDir(se)
    return se_roots_live


def GetTopLevelDir(storageElement):
    """ Get top level (../t2k.org/) directory from storage element
    Not perfect, some read/write issues on some SEs, handled by exception """
    print 'GetTopLevelDir'

    # Default empty string
    top_level_dir = str()

    # Use a local test file
    testFileName = 'lcgCrTestfile.'+str(os.getpid())
    command = "dd if=/dev/zero of="+testFileName+" bs=1048576 count=1"
    print command
    system(command)

    # Make sure test file is not already registered on LFC
    command = join("lcg-del --vo t2k.org \
-a lfn:/grid/t2k.org/test", testFileName)
    command += " </dev/null >/dev/null 2>&1"
    system(command)

    try:
        # Register test file on storage element
        # using relative path name, returns GUID

        # Entry in LFC in the test directory of /grid/t2k.org/
        command = "lcg-cr --vo t2k.org -d " + storageElement
        command += " -P " + testFileName
        command += join(" -l lfn:/grid/t2k.org/test", testFileName)
        command += " file:" + testFileName
        lines, errors = ND280GRID.runLCG(command, is_pexpect=False)
        if errors:
            raise Exception

        # Use GUID to retrieve data path to
        # test file, and hence top level directory
        command = "lcg-lr --vo t2k.org " + ND280GRID.rmNL(lines[0])
        lines, errors = ND280GRID.runLCG(command, is_pexpect=False)
        if errors:
            raise Exception

        surl = lines[0]
        top_level_dir = ND280GRID.rmNL(surl.replace(testFileName, ''))

    # Exception handles access errors, bit of a cludge
    except Exception as exception:
        # Carry on regardless, get data path with error
        print str(exception)
        print 'Exception: ' + ND280GRID.rmNL(errors[0])
        top_level_dir = ND280GRID.rmNL(errors[0].split('lcgCr')[0])

        command = 'lcg-ls --vo t2k.org ' + top_level_dir + testFileName
        lines, errors = ND280GRID.runLCG(command, is_pexpect=False)
        if lines:
            command = command.replace('lcg-ls', 'lcg-del -l')
            ND280GRID.runLCG(command, is_pexpect=False)

    # Clean up, don't worry about errors
    system("rm -f " + testFileName)
    system("lcg-del --vo t2k.org -a lfn:/grid/t2k.org/test/" + testFileName)

    # Last ditch, use se_roots but truncate nd280/ subdirectory
    if 'error' in top_level_dir or 'srm://' not in top_level_dir:
        top_level_dir = SE_ROOTS[storageElement].replace('nd280/', '')

    # Make sure there is only one trailing slash
    top_level_dir = top_level_dir.rstrip('//')
    top_level_dir += '/'

    print top_level_dir
    return top_level_dir


def GetListOfSEs():
    """ Get list of Storage Elements """
    print 'GetListOfSEs'

    command = "lcg-infosites --vo %s se" % ND280Comp.VO
    lines, errors = ND280Comp.GetListPopenCommand(command)
    if len(lines) > 2:
        # skip first 2 lines
        lines = lines[2:]
        seList = list()
        for line in lines:
            word = line.split()
            seName = word[3]
            # Ignore following (for now)
            if 'manchester' in seName:
                continue
            if 'heplnx204' in seName:
                continue
            if 'se04.esc.qmul.ac.uk' in seName:
                continue
            # Append se to list
            seList.append(seName)
        # return unique elements only
        return list(set(seList))
    else:
        print 'Could not get list of SEs'
    return list()


def GetDefaultSE():
    """ Get the default SE to store output on, defaults to RAL.
    Also checks if the default SE is in the list of se_roots """

    default_se = getenv("VO_T2K_ORG_DEFAULT_SE")
    if not default_se or default_se not in SE_ROOTS:
        default_se = getenv("VO_T2K_DEFAULT_SE")
    if not default_se or default_se not in SE_ROOTS:
        return "srm-t2k.gridpp.rl.ac.uk"
    return default_se


def GetSEFromSRM(srm):
    """Strip the SE from an SRM"""
    return srm.replace('//', '/').replace('srm:/', '').split('/')[0]


def PrintSEDiskUsage():
    """ Print Storage Element Disk Usage """
    command = "lcg-infosites --vo t2k.org se"
    lines, errors = ND280Comp.GetListPopenCommand(command)

    print 'Free (TB)  Used(TB)  SE'
    print '-------------------------------------------------'

    # skip first 2 lines
    if lines:
        for line in lines[2:]:

            words = line.split()
            seFree, seUsed, seName = words[0], words[1], words[2]

            # Ignore manchester and heplnx204.pp.rl.ac.uk (for now)
            if 'manchester' in seName:
                continue
            if 'heplnx204' in seName:
                continue

            if 'n.a' in seFree:
                seFree = 0
            else:
                seFree = float(seFree) * units().kTerabyte
            if 'n.a' in seUsed:
                seUsed = 0
            else:
                seUsed = float(seUsed) * units().kTerabyte

            # Ignore if free and used both 0
            if seFree == 0 and seUsed == 0:
                continue

            print '%9.2f %9.2f  %s' % (seFree, seUsed, seName)
    else:
        if errors:
            print '\n'.join(errors)


def PrintSESpaceUsage():
    """ Print Storage Element Space Usage """

    command = "lcg-infosites --vo t2k.org space"
    lines, errors = ND280Comp.GetListPopenCommand(command)

    print '    Free     Used     Free     Used              Tag SE'
    print '  Online   Online Nearline Nearline (TB)                   '
    print '--------------------------------------------------------------------------------'

    if lines:
        lines = lines[3:]
        for line in lines:

            words = line.split()
            onlineFree = float(words[0]) / 1024.
            onlineUsed = float(words[1]) / 1024.
            nearlineFree = float(words[3]) / 1024.
            nearlineUsed = float(words[4]) / 1024.
            tag = words[6]
            se = words[7]

            # Ignore if free and used both 0|1
            if onlineUsed <= 1 and onlineUsed <= 1:
                continue

            print '%8.2f %8.2f %8.2f %8.2f %16s %s' % (onlineFree, onlineUsed, nearlineFree, nearlineUsed, tag, se)
    else:
        if errors:
            print '\n'.join(errors)
