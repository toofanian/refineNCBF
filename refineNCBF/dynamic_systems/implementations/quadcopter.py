from typing import Tuple, Callable, Optional

import attr
import hj_reachability
import jax
import jax.numpy as jnp
import numpy as np

from refineNCBF.dynamic_systems.dynamic_systems import ControlAffineDynamicSystem, ControlAffineDynamicSystemFixedPolicy
from refineNCBF.refining.hj_reachability_interface.hj_dynamics import HJControlAffineDynamics, ActorModes, HJControlAffineDynamicsFixedPolicy
from refineNCBF.utils.types import VectorBatch, MatrixBatch
from scripts.barrier_refinement.pre_constrcuted_stuff.quadcopter_cbf import load_tabularized_ppo, load_tabularized_sac


@attr.dataclass
class QuadcopterVerticalParams:
    gravity: float
    mass: float
    drag_coefficient_v: float
    drag_coefficient_phi: float
    length_between_copters: float
    moment_of_inertia: float

    min_thrust: float
    max_thrust: float


default_quadcopter_vertical_params = QuadcopterVerticalParams(
    drag_coefficient_v=.25,
    gravity=9.81,
    drag_coefficient_phi=.02255,
    mass=2.5,
    length_between_copters=1.0,
    moment_of_inertia=1.0,

    min_thrust=0.,
    max_thrust=20,  # default should be 18.39375
)


@attr.s(auto_attribs=True)
class QuadcopterVertical(ControlAffineDynamicSystem):
    gravity: float
    mass: float
    drag_coefficient_v: float
    drag_coefficient_phi: float
    length_between_copters: float
    moment_of_inertia: float

    state_dimensions: int = 4
    periodic_state_dimensions: Tuple[float, ...] = (2,)

    control_dimensions: int = 2

    disturbance_dimensions: int = 1
    disturbance_lower_bounds: Tuple[float, ...] = (0,)
    disturbance_upper_bounds: Tuple[float, ...] = (0,)

    @classmethod
    def from_specs(
            cls,
            params: QuadcopterVerticalParams,
    ) -> 'QuadcopterVertical':
        control_lower_bounds = (params.min_thrust, params.min_thrust)
        control_upper_bounds = (params.max_thrust, params.max_thrust)
        return cls(
            gravity=params.gravity,
            mass=params.mass,
            drag_coefficient_v=params.drag_coefficient_v,
            drag_coefficient_phi=params.drag_coefficient_phi,
            length_between_copters=params.length_between_copters,
            moment_of_inertia=params.moment_of_inertia,
            control_lower_bounds=control_lower_bounds,
            control_upper_bounds=control_upper_bounds,
        )

    def compute_open_loop_dynamics(self, state: VectorBatch) -> VectorBatch:
        open_loop_dynamics = np.zeros_like(state)

        open_loop_dynamics[..., 0] = state[..., 1]
        open_loop_dynamics[..., 1] = -self.drag_coefficient_v / self.mass * state[..., 1] - self.gravity
        open_loop_dynamics[..., 2] = state[..., 3]
        open_loop_dynamics[..., 3] = -self.drag_coefficient_phi / self.moment_of_inertia * state[..., 3]

        return open_loop_dynamics

    def compute_control_jacobian(self, state: VectorBatch) -> MatrixBatch:
        control_matrix = np.repeat(np.zeros_like(state)[..., None], self.control_dimensions, axis=-1)

        control_matrix[..., 1, :] = np.cos(state[..., 2]) / self.mass
        control_matrix[..., 3, 0] = - self.length_between_copters / self.moment_of_inertia
        control_matrix[..., 3, 1] = self.length_between_copters / self.moment_of_inertia

        return control_matrix

    def compute_disturbance_jacobian(self, state: VectorBatch) -> MatrixBatch:
        disturbance_jacobian = np.repeat(np.zeros_like(state)[..., None], 1, axis=-1)

        return disturbance_jacobian


class QuadcopterVerticalJAX(QuadcopterVertical):
    def compute_open_loop_dynamics(self, state: jax.Array, time: jax.Array = 0.0) -> jax.Array:
        return jnp.array([
            state[1],
            -state[1] * self.drag_coefficient_v / self.mass - self.gravity,
            state[3],
            -state[3] * self.drag_coefficient_phi / self.moment_of_inertia
        ])

    def compute_control_jacobian(self, state, time: jax.Array = 0.0):
        return jnp.array([
            [0, 0],
            [jnp.cos(state[2]) / self.mass, jnp.cos(state[2]) / self.mass],
            [0, 0],
            [-self.length_between_copters / self.moment_of_inertia,
             self.length_between_copters / self.moment_of_inertia]
        ])

    def compute_disturbance_jacobian(self, state: np.ndarray, time: jax.Array = 0.0) -> jax.Array:
        return jnp.expand_dims(jnp.zeros(4), axis=-1)


quadcopter_vertical_jax_hj = HJControlAffineDynamics.from_parts(
    control_affine_dynamic_system=QuadcopterVerticalJAX.from_specs(default_quadcopter_vertical_params),
    control_mode=ActorModes.MAX,
    disturbance_mode=ActorModes.MIN,
)


@attr.s(auto_attribs=True, eq=False)
class QuadcopterFixedPolicy(ControlAffineDynamicSystemFixedPolicy):
    gravity: float
    mass: float
    drag_coefficient_v: float
    drag_coefficient_phi: float
    length_between_copters: float
    moment_of_inertia: float

    state_dimensions: int = 4
    periodic_state_dimensions: Tuple[float, ...] = (2,)

    control_dimensions: int = 2

    disturbance_dimensions: int = 1
    disturbance_lower_bounds: Tuple[float, ...] = (0,)
    disturbance_upper_bounds: Tuple[float, ...] = (0,)

    _control_policy: Callable[[VectorBatch], VectorBatch] = attr.ib(factory=lambda: lambda x: jnp.zeros((2, 1)))
    _disturbance_policy: Callable[[VectorBatch], VectorBatch] = attr.ib(factory=lambda: lambda x: jnp.zeros((1, 1)))

    @classmethod
    def from_specs_with_policy(
            cls,
            params: QuadcopterVerticalParams,
            control_policy: Optional[Callable[[VectorBatch], VectorBatch]] = None,
            disturbance_policy: Optional[Callable[[VectorBatch], VectorBatch]] = None,
    ) -> 'QuadcopterFixedPolicy':

        if control_policy is None:
            control_policy = lambda x: jnp.zeros((2, 1))
        if disturbance_policy is None:
            disturbance_policy = lambda x: jnp.zeros((1, 1))

        control_lower_bounds = (params.min_thrust, params.min_thrust)
        control_upper_bounds = (params.max_thrust, params.max_thrust)

        return cls(
            gravity=params.gravity,
            mass=params.mass,
            drag_coefficient_v=params.drag_coefficient_v,
            drag_coefficient_phi=params.drag_coefficient_phi,
            length_between_copters=params.length_between_copters,
            moment_of_inertia=params.moment_of_inertia,
            control_lower_bounds=control_lower_bounds,
            control_upper_bounds=control_upper_bounds,
            control_policy=control_policy,
            disturbance_policy=disturbance_policy,
        )

    def compute_open_loop_dynamics(self, state: jax.Array, time: jax.Array = 0.0) -> jax.Array:
        open_loop_dynamics = jnp.array([
            state[1],
            -state[1] * self.drag_coefficient_v / self.mass - self.gravity,
            state[3],
            -state[3] * self.drag_coefficient_phi / self.moment_of_inertia
        ])
        return open_loop_dynamics

    def compute_control_jacobian(self, state, time: jax.Array = 0.0):
        control_jacobian = jnp.array([
            [0, 0],
            [jnp.cos(state[2]) / self.mass, jnp.cos(state[2]) / self.mass],
            [0, 0],
            [-self.length_between_copters / self.moment_of_inertia,
             self.length_between_copters / self.moment_of_inertia]
        ])
        return control_jacobian

    def compute_disturbance_jacobian(self, state: np.ndarray, time: jax.Array = 0.0) -> jax.Array:
        disturbance_jacobian = jnp.expand_dims(jnp.zeros(4), axis=-1)
        return disturbance_jacobian

    def compute_control(self, state: VectorBatch) -> VectorBatch:
        control = jnp.atleast_1d(self._control_policy(state).squeeze())
        return control

    def compute_disturbance(self, state: VectorBatch) -> VectorBatch:
        disturbance = jnp.atleast_1d(self._disturbance_policy(state).squeeze())
        return disturbance


def load_quadcopter_ppo_jax_hj(
        grid: hj_reachability.Grid
) -> HJControlAffineDynamicsFixedPolicy:
    return HJControlAffineDynamicsFixedPolicy.from_parts(
        dynamics=QuadcopterFixedPolicy.from_specs_with_policy(
            params=default_quadcopter_vertical_params,
            control_policy=load_tabularized_ppo(grid),
        ),
        control_mode=ActorModes.MAX,
        disturbance_mode=ActorModes.MIN,
    )


def load_quadcopter_sac_jax_hj(
        grid: hj_reachability.Grid
) -> HJControlAffineDynamicsFixedPolicy:
    return HJControlAffineDynamicsFixedPolicy.from_parts(
        dynamics=QuadcopterFixedPolicy.from_specs_with_policy(
            params=default_quadcopter_vertical_params,
            control_policy=load_tabularized_sac(grid),
        ),
        control_mode=ActorModes.MAX,
        disturbance_mode=ActorModes.MIN,
    )