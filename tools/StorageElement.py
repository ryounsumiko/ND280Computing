"""Store all the Storage Elements (SE) in one convienet location"""


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
