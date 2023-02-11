# class SignedDistanceFunctions(IntEnum):
#     X3_DISTANCE = 0
#     X3_DISTANCE_KERNEL = 1
#     X3_DISTANCE_KERNEL_CUT_50dist = 2  # _distance kernel but cut in half along the _distance axis
#     X3_DISTANCE_KERNEL_CUT_55dist = 3  # _distance kernel but cut in half along the _distance axis
#     X3_DISTANCE_KERNEL_PLUS = 4
#     X3_DISTANCE_5LEVELSET = 5
#
#
# def get_saved_signed_distance_function(
#         signed_distance_function: SignedDistanceFunctions,
#         dynamics: HJControlAffineDynamics,
#         grid: hj_reachability.Grid
# ):
#     match signed_distance_function:
#         case SignedDistanceFunctions.X3_DISTANCE:
#             grid_np = np.array(grid.states)
#             where_boundary = np.logical_and(grid_np[:, :, :, 2] > 40, grid_np[:, :, :, 2] < 60)
#             signed_distance_to_boundary = -skfmm.distance(~where_boundary) + skfmm.distance(where_boundary)
#
#         case SignedDistanceFunctions.X3_DISTANCE_KERNEL:
#             grid_np = np.array(grid.states)
#             boundary_for_kernel = np.logical_and(grid_np[:, :, :, 2] > 40, grid_np[:, :, :, 2] < 60)
#             signed_distance_to_boundary = compute_signed_distance(boundary_for_kernel)
#             solver_settings = hj_reachability.SolverSettings.with_accuracy(
#                 accuracy=hj_reachability.solver.SolverAccuracyEnum.VERY_HIGH,
#                 value_postprocessor=NotBiggerator(signed_distance_to_boundary, jnp.ones_like(signed_distance_to_boundary, dtype=bool)),
#             )
#             where_boundary_values = hj_step(
#                 dynamics=dynamics,
#                 grid=grid,
#                 solver_settings=solver_settings,
#                 initial_values=signed_distance_to_boundary,
#                 time_start=0,
#                 time_target=-20,
#                 progress_bar=False
#             ) > 0
#
#             where_boundary = where_boundary_values
#             signed_distance_to_boundary = compute_signed_distance(where_boundary)
#
#         case SignedDistanceFunctions.X3_DISTANCE_KERNEL_CUT_50dist:
#             grid_np = np.array(grid.states)
#             boundary_for_kernel = np.logical_and(grid_np[:, :, :, 2] > 40, grid_np[:, :, :, 2] < 60)
#             signed_distance_to_boundary = compute_signed_distance(boundary_for_kernel)
#             solver_settings = hj_reachability.SolverSettings.with_accuracy(
#                 accuracy=hj_reachability.solver.SolverAccuracyEnum.VERY_HIGH,
#                 value_postprocessor=NotBiggerator(signed_distance_to_boundary, jnp.ones_like(signed_distance_to_boundary, dtype=bool)),
#             )
#             where_boundary_values = hj_step(
#                 dynamics=dynamics,
#                 grid=grid,
#                 solver_settings=solver_settings,
#                 initial_values=signed_distance_to_boundary,
#                 time_start=0,
#                 time_target=-20,
#                 progress_bar=False
#             ) > 0
#             where_boundary_states = (grid_np[:, :, :, 2] < 50)
#             where_boundary = np.logical_and(where_boundary_states, where_boundary_values)
#             signed_distance_to_boundary = compute_signed_distance(where_boundary)
#
#         case SignedDistanceFunctions.X3_DISTANCE_KERNEL_CUT_55dist:
#             grid_np = np.array(grid.states)
#             boundary_for_kernel = np.logical_and(grid_np[:, :, :, 2] > 40, grid_np[:, :, :, 2] < 60)
#             signed_distance_to_boundary = compute_signed_distance(boundary_for_kernel)
#             solver_settings = hj_reachability.SolverSettings.with_accuracy(
#                 accuracy=hj_reachability.solver.SolverAccuracyEnum.VERY_HIGH,
#                 value_postprocessor=NotBiggerator(signed_distance_to_boundary, jnp.ones_like(signed_distance_to_boundary, dtype=bool)),
#             )
#             where_boundary_values = hj_step(
#                 dynamics=dynamics,
#                 grid=grid,
#                 solver_settings=solver_settings,
#                 initial_values=signed_distance_to_boundary,
#                 time_start=0,
#                 time_target=-20,
#                 progress_bar=False
#             ) > 0
#             where_boundary_states = (grid_np[:, :, :, 2] < 55)
#             where_boundary = np.logical_and(where_boundary_states, where_boundary_values)
#             signed_distance_to_boundary = compute_signed_distance(where_boundary)
#
#         case _:
#             raise ValueError(f'Unknown signed distance function {signed_distance_function}')
#
#     return jnp.array(signed_distance_to_boundary)
