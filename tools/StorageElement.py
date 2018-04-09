"""Storage Elements (SE) info in one convenient location"""
import os
from os.path import join

import ND280Grid
from ND280Grid import GetListPopenCommand
from ND280Grid import runLCG, rmNL


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
    os.system(command)

    # Make sure test file is not already registered on LFC
    command = join("lcg-del --vo t2k.org \
-a lfn:/grid/t2k.org/test", testFileName)
    command += " </dev/null >/dev/null 2>&1"
    os.system(command)

    try:
        # Register test file on storage element
        # using relative path name, returns GUID

        # Entry in LFC in the test directory of /grid/t2k.org/
        command = "lcg-cr --vo t2k.org -d " + storageElement
        command += " -P " + testFileName
        command += join(" -l lfn:/grid/t2k.org/test", testFileName)
        command += " file:" + testFileName
        lines, errors = runLCG(command, is_pexpect=False)
        if errors:
            raise Exception

        # Use GUID to retrieve data path to
        # test file, and hence top level directory
        command = "lcg-lr --vo t2k.org " + rmNL(lines[0])
        lines, errors = runLCG(command, is_pexpect=False)
        if errors:
            raise Exception

        surl = lines[0]
        top_level_dir = rmNL(surl.replace(testFileName, ''))

    # Exception handles access errors, bit of a cludge
    except Exception as exception:
        # Carry on regardless, get data path with error
        print str(exception)
        print 'Exception: ' + rmNL(errors[0])
        top_level_dir = rmNL(errors[0].split('lcgCr')[0])

        command = 'lcg-ls --vo t2k.org ' + top_level_dir + testFileName
        lines, errors = runLCG(command, is_pexpect=False)
        if lines:
            command = command.replace('lcg-ls', 'lcg-del -l')
            runLCG(command, is_pexpect=False)

    # Clean up, don't worry about errors
    os.system("rm -f " + testFileName)
    os.system("lcg-del --vo t2k.org -a lfn:/grid/t2k.org/test/" + testFileName)

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

    command = "lcg-infosites --vo %s se" % ND280Grid.VO
    lines, errors = GetListPopenCommand(command)
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
