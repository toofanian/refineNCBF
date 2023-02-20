import hj_reachability
import jax
import numpy as np
from matplotlib import pyplot as plt
from odp.Plots import PlotOptions
from odp.solver import HJSolver
from odp.Grid import Grid
import odp
import matplotlib

from refineNCBF.dynamic_systems.implementations.active_cruise_control_odp import active_cruise_control_odp_dynamics
from refineNCBF.utils.sets import compute_signed_distance
from refineNCBF.utils.visuals import DimName, ArraySlice2D

matplotlib.use('TkAgg')

dynamics = active_cruise_control_odp_dynamics

# grid is created in the hj_reachability library cause i'm used to that, but i reconstruct it for ODP later.
grid = hj_reachability.Grid.from_lattice_parameters_and_boundary_conditions(
    domain=hj_reachability.sets.Box(
        [0, -20, 20],
        [1e3, 20, 80]
    ),
    shape=(3, 101, 101)
)

# avoid being too close or too far from the car in front (3rd dim is relative distance)
avoid_set = (
        (grid.states[..., 2] > 60)
        |
        (grid.states[..., 2] < 40)
)
obstacle_values = compute_signed_distance(avoid_set)  # positive is inside, negative is outside


# For reach set, i'd really just like it to be nothing, in the pure "avoid" formulation.
# ...But i've created this dummy reach set since i cant figure out how to do that
reach_set = (
        (grid.states[..., 2] < 53)
        &
        (grid.states[..., 2] > 47)
)
target_values = compute_signed_distance(reach_set)

# trying to say "just do the infinite-time BRT for avoiding the obstacle".
system_objectives = {
    "TargetSetMode": "maxVWithVTarget",
    "ObstacleSetMode": "minVWithObstacle"
}

# reconstructing the grid for ODP
odp_grid = Grid(
            np.array(grid.domain.lo),
            np.array(grid.domain.hi),
            len(grid.domain.hi),
            np.array(list(grid.shape)),
            [2]
        )

# i would like the initial values to be -signed_distance(obstacle_values). Not sure if i've accomplished that here...
computed_values = HJSolver(
            dynamics,
            odp_grid,
            [target_values, obstacle_values],
            [0, 1],
            system_objectives,
            PlotOptions(do_plot=False, plot_type="3d_plot", plotDims=[0, 1, 2], slicesCut=[]),
        )

# plotting
reference_slice = ArraySlice2D.from_reference_index(
    reference_index=(1, 0, 0),
    free_dim_1=DimName(1, 'rel_distance'),
    free_dim_2=DimName(2, 'rel_velocity'),
    )

x1, x2 = np.meshgrid(
            grid.coordinate_vectors[reference_slice.free_dim_1.dim],
            grid.coordinate_vectors[reference_slice.free_dim_2.dim]
        )

proxies_for_labels = [
    plt.Rectangle((0, 0), 1, 1, fc='b', ec='w', alpha=.5),
    plt.Rectangle((0, 0), 1, 1, fc='w', ec='b', alpha=1),
]

legend_for_labels = [
    'computed_values',
    'computed_values viability kernel',
]

fig, ax = plt.figure(figsize=(9, 7)), plt.axes(projection='3d')
ax.set(title='value function')

ax.plot_surface(
    x1, x2, reference_slice.get_sliced_array(computed_values).T,
    cmap='Blues', edgecolor='none', alpha=.5
)
ax.contour3D(
    x1, x2, reference_slice.get_sliced_array(computed_values).T,
    levels=[0], colors=['b']
)


ax.contour3D(
    x1, x2, reference_slice.get_sliced_array(-obstacle_values).T,
    levels=[0], colors=['k'], linestyles=['--']
)

ax.legend(proxies_for_labels, legend_for_labels, loc='upper right')
ax.set_xlabel(reference_slice.free_dim_1.name)
ax.set_ylabel(reference_slice.free_dim_2.name)

plt.show(block=False)
plt.pause(0)