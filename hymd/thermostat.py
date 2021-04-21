"""Thermostat(s)

Scales or otherwise modifies the particle velocities during simulation to
simulate coupling to an external heat bath with temperature T₀.

Functions
---------
csvr_thermostat     Canonical sampling through velocity rescaling thermostat.
_random_gaussian    Generate standard normal deviates.
_random_chi_squared Generate squared sum of standard normal deviates.

"""
import numpy as np
from mpi4py import MPI
from input_parser import Config
from typing import Callable


def _random_gaussian() -> float:
    """Draw a single random number from the standard normal distribution

    Generate a number from the Gaussian distribution centered at zero with unit
    standard deviation, N(0, 1).

    Returns
    -------
    float
        A random number drawn from N(0, 1).
    """
    return np.random.normal()


def _random_chi_squared(M: int) -> float:
    """Draw the sum of `M` squared normally distributed values

    The value is generated by the Gamma distribution, in lieu of generating `M`
    Gaussian distributed numbers and summing their squares.

    Parameters
    ----------
    M : int
        Number of standard normally distributed numbers in the sum.

    Returns
    -------
    float
        The sum of `M` squared normally distributed values centered at zero
        with unit standard deviation.

    Notes
    -----
    The sum of the squares of k independent standard normal random variables is
    distributed according to a χ² distribution.

        ``X²₁ + X²₂ + X²₃ + ... + X² ~ 𝜎²χ²(k)``

    This is a special case of the Γ distribution, Γ(k/2, 2), and may be
    generated by

        ``χ²(k) ~ 2 Γ(k/2, 2)``

    References
    ----------
    Knuth, D.E. 1981, Seminumerical Algorithms, 2nd ed., vol. 2 of The Art of
    Computer Programming (Reading, MA: Addison-Wesley), pp. 120ff.

    J. H. Ahrens and U. Dieter, Computing 12 (1974), 223-246.
    """
    return np.random.chisquare(M)


def csvr_thermostat(
    velocity: np.ndarray, names: np.ndarray, config: Config,
    comm: MPI.Intracomm = MPI.COMM_WORLD,
    random_gaussian: Callable[[], float] = _random_gaussian,
    random_chi_squared: Callable[[int, float], float] = _random_chi_squared,
) -> np.ndarray:
    """Canonical sampling through velocity rescaling thermostat

    Implements the CSVR thermostat. Rescales the system kinetic energy by a
    stochastically chosen factor to keep the temperature constant. Requires
    communcation of the kinetic energies calculated locally for each MPI rank.
    The random numbers sampled through _random_gaussian and random_chi_squared
    and broadcast from the root rank to the other ranks to ensure the scaling
    is performed with the same stochasticity for all particles in the full
    system.

    The velocities are cleaned of center of mass momentum before the thermostat
    is applied, and the center of mass momentum is subsequently reapplied. This
    is performed for each thermostat coupling group, i.e. the center of mass
    momenta of each *group* is separately removed and reapplied after
    thermostatting.

    The implementation here is based on the derivation presented in the 2008
    Comput. Phys. Commun paper, not in the original 2007 J. Chem. Phys. paper.

    Parameters
    ----------
    velocity : (N, D) np.ndarray
        Array of velocities of N particles in D dimensions.
    names : (N,) np.ndarray
        Array of particle names.
    config : Config
        Configuration dataclass containing simulation metadata and parameters.
    comm : MPI.Intracomm, optional
        MPI communicator to use for rank commuication.
    random_gaussian : callable
        Function for generating standard normally distributed numbers.
    random_chi_squared : callable
        Function for generating χ²-distributed numbers

    Returns
    -------
    velocity : (N, D) np.ndarray
        Array containing the rescaled velocities of N particles in D
        dimensions.

    See Also
    --------
    _random_gaussian :    Used to sample Gaussian-distributed numbers.
    _random_chi_squared : Used to sample χ²-distributed numbers.

    References
    ----------
    G. Bussi, D. Donadio, and M. Parrinello, J. Chem. Phys. 126, 014101 (2007).
    G. Bussi and M. Parrinello, Comput. Phys. Commun. 179, 26-29, (2008).
    """
    if not any(config.thermostat_coupling_groups):
        config.thermostat_coupling_groups = [config.unique_names.copy()]
    for i, group in enumerate(config.thermostat_coupling_groups):
        ind = np.where(
            np.logical_or.reduce(list(names == np.string_(t) for t in group))
        )
        group_n_particles = comm.allreduce(len(ind[0]), MPI.SUM)

        # Clean velocities of center of mass momentum
        com_velocity = comm.allreduce(np.sum(velocity[ind], axis=0), MPI.SUM)
        velocity_clean = velocity[ind] - com_velocity / group_n_particles

        K = comm.allreduce(0.5 * config.mass * np.sum(velocity_clean[...]**2))
        K_target = ((3 / 2) * (2.479 / 298.0) * group_n_particles
                    * config.target_temperature)
        N_f = 3 * group_n_particles
        c = np.exp(-(config.time_step * config.respa_inner) / config.tau)

        # Draw random numbers and broadcast them so they are identical across
        # MPI ranks
        R = SNf = None
        if comm.Get_rank() == 0:
            R = random_gaussian()
            SNf = random_chi_squared(N_f - 1)
        R = comm.bcast(R, root=0)
        SNf = comm.bcast(SNf, root=0)

        dK = 0.0
        if group_n_particles > 0:
            alpha2 = (
                c + (1 - c) * (SNf + R**2) * K_target / (N_f * K)
                + 2 * R * np.sqrt(c * (1 - c) * K_target / (N_f * K))
            )
            dK = K * (alpha2 - 1)
            alpha = np.sqrt(alpha2)
            velocity_clean *= alpha
        config.thermostat_work += dK

        # Assign velocities and reapply the previously removed center of mass
        # momentum removed
        velocity[ind] = velocity_clean + com_velocity / group_n_particles
