import warnings

import numpy as np
from jax import numpy as jnp

import hj_reachability
from odp.dynamics.quad4d import Quad4D
from refineNCBF.local_hjr_solver.solve_odp import create_local_solver_odp
from refineNCBF.utils.files import generate_unique_filename
from refineNCBF.utils.sets import compute_signed_distance

warnings.simplefilter(action='ignore', category=FutureWarning)


def wip_qv_global_odp(save_result: bool = False):
    dynamics = Quad4D()

    grid = hj_reachability.Grid.from_lattice_parameters_and_boundary_conditions(
        domain=hj_reachability.sets.Box(
            [0, -8, -np.pi, -10],
            [10, 8, np.pi, 10]
        ),
        shape=(51, 25, 51, 25)
    )

    avoid_set = (
            (grid.states[..., 0] < 1)
            |
            (grid.states[..., 0] > 9)
    )

    reach_set = jnp.zeros_like(avoid_set, dtype=bool)

    terminal_values = compute_signed_distance(~avoid_set)

    solver = create_local_solver_odp(
        dynamics=dynamics,
        grid=grid,
        periodic_dims=[2],
        avoid_set=avoid_set,
        reach_set=reach_set,
        terminal_values=terminal_values,
        max_iterations=100,
        change_atol=1e-1,
        change_rtol=1e-1,
        solver_timestep=-.2,
        verbose=True
    )

    initial_values = terminal_values.copy()
    active_set = terminal_values >= 0

    result = solver(active_set=active_set, initial_values=initial_values)

    if save_result:
        result.save(generate_unique_filename('data/local_update_results/wip_qv_local_odp', 'dill'))

    return result


if __name__ == '__main__':
    wip_qv_global_odp(save_result=True)
