import warnings

from jax import numpy as jnp

import hj_reachability
from refineNCBF.dynamic_systems.active_cruise_control import ActiveCruiseControlJAX, \
    simplified_active_cruise_control_params
from refineNCBF.hj_reachability_interface.hj_dynamics import HJControlAffineDynamics, ActorModes
from refineNCBF.local_hjr_solver.solve import LocalHjrSolver
from refineNCBF.utils.files import generate_unique_filename
from refineNCBF.utils.sets import compute_signed_distance

warnings.simplefilter(action='ignore', category=FutureWarning)


def demo_local_hjr_classic_solver_on_active_cruise_control(save_result: bool = False):
    dynamics = HJControlAffineDynamics.from_parts(
        control_affine_dynamic_system=ActiveCruiseControlJAX.from_params(simplified_active_cruise_control_params),
        control_mode=ActorModes.MAX,
        disturbance_mode=ActorModes.MIN,
    )

    grid = hj_reachability.Grid.from_lattice_parameters_and_boundary_conditions(
        domain=hj_reachability.sets.Box(
            [0, -20, 20],
            [1e3, 20, 80]
        ),
        shape=(3, 201, 201)
    )

    avoid_set = (
            (grid.states[..., 2] > 60)
            |
            (grid.states[..., 2] < 40)
    )

    reach_set = jnp.zeros_like(avoid_set, dtype=bool)

    terminal_values = compute_signed_distance(~avoid_set)

    solver = LocalHjrSolver.as_local_solver(
        dynamics=dynamics,
        grid=grid,
        avoid_set=avoid_set,
        reach_set=reach_set,
        terminal_values=terminal_values,
        max_iterations=100,
        verbose=True
    )

    initial_values = terminal_values.copy()
    active_set = ~avoid_set

    result = solver(active_set=active_set, initial_values=initial_values)

    if save_result:
        result.save(generate_unique_filename('data/local_update_results/result_acc_local_jax', 'dill'))

    return result


if __name__ == '__main__':
    demo_local_hjr_classic_solver_on_active_cruise_control(save_result=True)
