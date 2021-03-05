from mpi4py import MPI
import sys
import os
import numpy as np
import h5py
import pytest
import collections

# TODO: Remove this when we have a working pip installable main package and
# can test against installed package by
#
# pip3 install -e . && python3 -m pytest
curr_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(curr_path, os.pardir, 'hymd'))


@pytest.fixture
def three_atoms():
    indices = np.array([0, 1, 2], dtype=int)
    molecules = np.array([0, 1, 2], dtype=int)
    bonds = np.empty(shape=(3, 3), dtype=int).fill(-1)
    positions = np.array([
        [3.3373791310195866, 3.0606470524188550, 3.6534883423600704],
        [4.2567447747360480, 3.3079639873791216, 4.7134201398123450],
        [2.1642221859524686, 2.2122847674657260, 4.1836737698720112]
    ], dtype=np.float64)
    velocities = np.array([
        [0.25247916327420140, -0.4067773212594663, -0.2957983111297534],
        [-0.1180891285878425,  0.4014440048143856,  0.3836539403365794],
        [0.35245160777096232,  0.1512649589924152,  0.0694415026280095]
    ], dtype=np.float64)
    names = np.array([b'A', b'B', b'C'], dtype='S5')

    CONF = {}
    for k, v in {'Np': 3, 'types': 3, 'mass': 86.05955822385427,
                 'L': [10.0, 10.0, 10.0], 'dt': 0.0180532028101793}.items():
        CONF[k] = v
    return indices, bonds, names, molecules, positions, velocities, CONF


@pytest.fixture
def dppc_single():
    """
    Sets up a single DPPC molecule test system

    Notes
    -----
    Type names (indices) and bonds::

                      G(3) -- C(8) -- C(9) -- C(10) -- C(11)
                      /
    N(0) -- P(1) -- G(2) -- C(4) -- C(5) -- C(6) -- C(7)
    """
    indices = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], dtype=int)
    molecules = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=int)
    r = np.array([[0.244559E+01, 0.909193E+00, 0.560020E+01],
                  [0.206399E+01, 0.745504E+00, 0.577413E+01],
                  [0.172144E+01, 0.618203E+00, 0.601021E+01],
                  [0.164460E+01, 0.705806E+00, 0.629945E+01],
                  [0.151964E+01, 0.940714E+00, 0.646405E+01],
                  [0.154557E+01, 0.108941E+01, 0.685593E+01],
                  [0.161312E+01, 0.103298E+01, 0.730153E+01],
                  [0.205084E+01, 0.118547E+01, 0.763296E+01],
                  [0.214117E+01, 0.868565E+00, 0.650513E+01],
                  [0.229689E+01, 0.108656E+01, 0.691872E+01],
                  [0.258356E+01, 0.119129E+01, 0.731768E+01],
                  [0.287958E+01, 0.148139E+01, 0.755405E+01]],
                 dtype=np.float64)
    bonds = np.array([[1,           -1, -1],   # N(0)
                      [0, 2,        -1],       # P(1)
                      [1, 3,  4],              # G(2) -- C(4)
                      [2, 8,        -1],       # G(3) -- C(8)
                      [2, 5,        -1],       # C(4)
                      [4, 6,        -1],       # C(5)
                      [5, 7,        -1],       # C(6)
                      [6,           -1, -1],   # C(7)
                      [3, 9,        -1],       # C(8)
                      [8, 10,       -1],       # C(9)
                      [9, 11,       -1],       # C(10)
                      [10,          -1, -1]],  # C(11)
                     dtype=int)
    names = np.array([b'N', b'P', b'G', b'G', b'C', b'C', b'C', b'C', b'C',
                      b'C', b'C', b'C'], dtype='S5')
    CONF = {}
    Bond = collections.namedtuple(
        'Bond', ['atom_1', 'atom_2', 'equilibrium', 'strength']
    )
    Angle = collections.namedtuple(
        'Angle', ['atom_1', 'atom_2', 'atom_3', 'equilibrium', 'strength']
    )
    CONF['bond_2'] = (Bond('N', 'P', 0.47, 1250.0),
                      Bond('P', 'G', 0.47, 1250.0),
                      Bond('G', 'G', 0.37, 1250.0),
                      Bond('G', 'C', 0.47, 1250.0),
                      Bond('C', 'C', 0.47, 1250.0))

    CONF['bond_3'] = (Angle('P', 'G', 'G', 120.0, 25.0),
                      Angle('P', 'G', 'C', 180.0, 25.0),
                      Angle('G', 'C', 'C', 180.0, 25.0),
                      Angle('C', 'C', 'C', 180.0, 25.0))
    for k, v in {'Np': 12, 'types': 5, 'mass': 72.0,
                 'L': [13.0, 13.0, 14.0]}.items():
        CONF[k] = v
    return indices, bonds, names, molecules, r, CONF


@pytest.fixture()
def h5py_molecules_file(mpi_file_name):
    n_particles = 1000
    indices = np.empty(1000, dtype=int)
    molecules = np.empty(1000, dtype=int)

    if MPI.COMM_WORLD.Get_rank() == 0:
        with h5py.File(mpi_file_name, 'w') as out_file:
            mol_len = np.array([21, 34, 18, 23, 19, 11, 18, 24, 13, 19, 27, 11,
                                31, 14, 37, 30, 38, 24, 16,  5, 30, 25, 19,  5,
                                31, 14, 21, 15, 13, 27, 13, 12,  8,  2, 15, 31,
                                13, 31, 20, 11,  7, 22,  3, 31,  4, 24, 30,  4,
                                36,  5,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
                                1,   1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
                                1,   1,  1,  1,  1,  1,  1,  1,  1,  1,  1,  1,
                                1,   1,  1,  1,  1,  1,  1,  1,  1,  1,  1],
                               dtype=int)
            indices = np.arange(n_particles)
            current_ind = 0
            for ind, mol in enumerate(mol_len):
                next_ind = current_ind + mol
                molecules[current_ind:next_ind].fill(ind)
                current_ind = next_ind

            dset_indices = out_file.create_dataset('indices', (n_particles,),
                                                   dtype='i')
            dset_molecules = out_file.create_dataset('molecules',
                                                     (n_particles,), dtype='i')
            dset_indices[:] = indices[:]
            dset_molecules[:] = molecules[:]
    MPI.COMM_WORLD.Barrier()
    print(mpi_file_name)
    return mpi_file_name, n_particles, indices, molecules


@pytest.fixture()
def config_toml(mpi_file_name):
    out_str = """
    [meta]
    name = "example config.toml"
    tags = ["example", "config"]

    [particles]
    n_particles = 10000
    mass = 72.0
    max_molecule_size = 50

    [simulation]
    n_steps = 100
    n_print = 10
    time_step = 0.03
    box_size = [2.1598, 11.2498, 5.1009]
    integrator = "respa"
    respa_inner = 5
    domain_decomposition = false
    start_temperature = false
    target_temperature = 323
    tau = 0.7

    [field]
    mesh_size = 40
    kappa = 0.05
    sigma = 0.5
    chi = [
      [["C", "W"], [42.24]],
      [["G", "C"], [10.47]],
      [["N", "W"], [-3.77]],
      [["G", "W"],  [4.53]],
      [["N", "P"], [-9.34]],
      [["P", "G"],  [8.04]],
      [["N", "G"],  [1.97]],
      [["P", "C"], [14.72]],
      [["P", "W"], [-1.51]],
      [["N", "C"], [13.56]],
    ]

    [bonds]
    bonds = [
      [["N", "P"], [0.47, 1250.0]],
      [["P", "G"], [0.47, 1250.0]],
      [["G", "G"], [0.37, 1250.0]],
      [["G", "C"], [0.47, 1250.0]],
      [["C", "C"], [0.47, 1250.0]],
    ]
    angle_bonds = [
      [["P", "G", "G"], [120.0, 25.0]],
      [["P", "G", "C"], [180.0, 25.0]],
      [["G", "C", "C"], [180.0, 25.0]],
      [["C", "C", "C"], [180.0, 25.0]],
    ]
    """
    if MPI.COMM_WORLD.Get_rank() == 0:
        with open(mpi_file_name, 'w') as out_file:
            out_file.write(out_str)
    MPI.COMM_WORLD.Barrier()
    return mpi_file_name, out_str


@pytest.fixture()
def config_CONF(mpi_file_name):
    out_str = """
import numpy as np
import sympy

Np = 5
tau = 0.7
dt = 0.0005
NSTEPS = 100
T0 = 323
Nv = 8
sigma = 0.2988365823859701
nprint = 10
mass = 72
kappa = 0.0524828568359992
L = [7.1598, 11.2498, 5.1009]
types = 2
ntypes = 2
rho0 = Np/(L[0]*L[1]*L[2])
dV=L[0]*L[1]*L[2]/Nv
NAMES = np.array([np.string_(a) for a in ["A", "B"]])
domain_decomp = True
T_start = 300

phi = sympy.var('phi:%d'%(types))

def w(phi):
    return 0.5 / (kappa * rho0) * (sum(phi) - rho0)**2

V_EXT = [sympy.lambdify([phi], sympy.diff(w(phi),'phi%d'%(i)))
         for i in range(types)]
w     = sympy.lambdify([phi], w(phi))
k=sympy.var('k:%d'%(3))

def H1(k):
    return sympy.functions.elementary.exponential.exp(
        -0.5*sigma**2*(k0**2+k1**2+k2**2)
    )

kdHdk = [k0*sympy.diff(H1(k),'k0'),
         k1*sympy.diff(H1(k),'k1'),
         k2*sympy.diff(H1(k),'k2')]
kdHdk = [sympy.lambdify([k], kdHdk[i]) for i in range(3)]
H1=sympy.lambdify([k],H1(k))

def H(k, v):
    return v * H1(k) # numpy.exp(-0.5*sigma**2*k.normp(p=2))
    """
    if MPI.COMM_WORLD.Get_rank() == 0:
        with open(mpi_file_name, 'w') as out_file:
            out_file.write(out_str)
    MPI.COMM_WORLD.Barrier()
    return mpi_file_name, out_str


@pytest.fixture()
def molecules_with_solvent():
    r = np.array([[8.13667513, 5.69074724, 1.07490432],
                  [7.11613859, 4.61697965, 9.10670714],
                  [8.20241234, 9.07211713, 2.80655489],
                  [8.16630918, 4.81143443, 4.40010430],
                  [9.85378304, 5.14335715, 2.90351911],
                  [3.11147497, 2.28322938, 2.68303120],
                  [1.73605866, 7.88070389, 8.42411850],
                  [4.63462918, 8.79913645, 3.95913502],
                  [8.82600104, 5.42442507, 5.77202103],
                  [4.50318499, 0.92639019, 2.40771027],
                  [8.98632120, 5.78185357, 1.51047950],
                  [0.97724350, 4.53665951, 6.35397580],
                  [1.40416440, 8.50456600, 2.90030381],
                  [9.22231112, 9.75627113, 2.69850708],
                  [5.74081308, 3.32663226, 1.99632322],
                  [6.42563880, 5.25326224, 0.47099379],
                  [1.34734941, 1.90932713, 6.40945601],
                  [7.15699879, 4.93841887, 2.46816512],
                  [8.95866799, 4.83718895, 8.79237570],
                  [3.80814683, 4.50229031, 5.50739640],
                  [9.49355966, 0.49681300, 2.52558858],
                  [5.54096659, 6.01678936, 3.66888671],
                  [8.60227403, 2.27086631, 5.83688793],
                  [9.49382901, 3.83585526, 5.40626319],
                  [2.13351655, 2.26102564, 5.12969958],
                  [7.99361137, 2.39261338, 0.57527544],
                  [8.72343502, 9.20949362, 2.86804666],
                  [7.04678315, 7.49039307, 0.53845823],
                  [7.50298867, 9.11984417, 8.06488954],
                  [1.97941691, 0.91173916, 1.74975040]],
                 dtype=np.float32)

    # Used to generate plausible molecules from random positions.
    # kmean = KMeans(n_clusters=8)
    # kmean.fit(r)
    # print(kmean.labels_)
    molecules = np.array([8, 5, 3, 1, 1, 4, 0, 6, 1, 4, 2, 0, 6, 3, 8, 8, 0, 2,
                          5, 0, 7, 2, 1, 1, 4, 7, 3, 2, 5, 4], dtype=np.int)

    r_solvent = np.array([[4.43693068, 1.69432311, 6.72887313],
                          [4.24242544, 9.60397719, 3.30870583],
                          [4.47710443, 5.56872464, 7.49807068],
                          [0.32818528, 1.96213073, 5.09395654],
                          [8.64414239, 7.82686007, 4.85943050],
                          [9.96799103, 6.30234893, 6.01944560],
                          [4.16012475, 6.86023960, 8.47489039],
                          [2.05822013, 0.83134351, 7.73528500],
                          [0.36488306, 8.96068194, 1.83560492],
                          [6.58596030, 0.13976723, 7.73180439],
                          [0.83760117, 7.48156968, 1.27407983],
                          [3.06486403, 8.88103126, 0.48484420],
                          [5.72275525, 6.30133732, 1.94503790],
                          [5.70752801, 7.77619645, 2.50716313],
                          [3.77070584, 7.78962099, 2.55348930]],
                         dtype=np.float32)
    ind = np.argsort(molecules)
    r = np.concatenate((r[ind], r_solvent), axis=0)
    molecules = np.concatenate(
        (molecules[ind], np.arange(9, 9+15)), axis=0
    )
    velocities = np.random.normal(loc=0.0, scale=1.0, size=(r.shape))
    return np.arange(0, r.shape[0]), r, molecules, velocities