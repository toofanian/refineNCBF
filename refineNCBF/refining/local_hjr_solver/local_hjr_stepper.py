from abc import ABC, abstractmethod
from typing import Callable

import attr
import hj_reachability

from refineNCBF.refining.hj_reachability_interface.hj_setup import HjSetup
from refineNCBF.refining.local_hjr_solver.local_hjr_result import LocalUpdateResult
from refineNCBF.utils.types import MaskNd, ArrayNd


@attr.s(auto_attribs=True)
class LocalHjrStepper(ABC, Callable):
    @abstractmethod
    def __call__(self, data: LocalUpdateResult, active_set_prefiltered: MaskNd, active_set_expanded: MaskNd) -> ArrayNd:
        ...


@attr.s(auto_attribs=True)
class ClassicLocalHjrStepper(LocalHjrStepper):
    _hj_setup: HjSetup
    _solver_settings: hj_reachability.SolverSettings
    _time_step: float
    _verbose: bool

    @classmethod
    def from_parts(cls, hj_setup: HjSetup, solver_settings: hj_reachability.SolverSettings, time_step: float,
                   verbose: bool):
        return cls(hj_setup=hj_setup, solver_settings=solver_settings, time_step=time_step, verbose=verbose)

    def __call__(self, data: LocalUpdateResult, active_set_prefiltered: MaskNd, active_set_expanded: MaskNd) -> ArrayNd:
        values = hj_reachability.step(
            solver_settings=self._solver_settings,
            dynamics=self._hj_setup.dynamics,
            grid=self._hj_setup.grid,
            time=0,
            values=data.get_recent_values(),
            target_time=self._time_step,
            active_set=active_set_expanded,
            progress_bar=self._verbose,
        )
        return values


@attr.s(auto_attribs=True)
class DecreaseLocalHjrStepper(LocalHjrStepper):
    _hj_setup: HjSetup
    _solver_settings: hj_reachability.SolverSettings
    _time_step: float
    _verbose: bool

    @classmethod
    def from_parts(cls, hj_setup: HjSetup, solver_settings: hj_reachability.SolverSettings, time_step: float,
                   verbose: bool):
        return cls(hj_setup=hj_setup, solver_settings=solver_settings, time_step=time_step, verbose=verbose)

    def __call__(self, data: LocalUpdateResult, active_set_prefiltered: MaskNd, active_set_expanded: MaskNd) -> ArrayNd:
        values_next = hj_reachability.step(
            solver_settings=self._solver_settings,
            dynamics=self._hj_setup.dynamics,
            grid=self._hj_setup.grid,
            time=0,
            values=data.get_recent_values(),
            target_time=self._time_step,
            active_set=active_set_expanded,
            progress_bar=self._verbose,
        )
        values_decreased = (values_next < data.get_recent_values()) #& active_set_expanded
        values = data.get_recent_values().at[values_decreased].set(values_next[values_decreased])
        return values


@attr.s(auto_attribs=True)
class TrashLocalHjrStepper(LocalHjrStepper):
    """
    used when testing hjr solver performance. computes update but returns input values, so nothing changes in the pipeline,
    and it can be repeated identically for another iteration
    """
    _hj_setup: HjSetup
    _solver_settings: hj_reachability.SolverSettings
    _time_step: float
    _verbose: bool

    @classmethod
    def from_parts(cls, hj_setup: HjSetup, solver_settings: hj_reachability.SolverSettings, time_step: float,
                   verbose: bool):
        return cls(hj_setup=hj_setup, solver_settings=solver_settings, time_step=time_step, verbose=verbose)

    def __call__(self, data: LocalUpdateResult, active_set_prefiltered: MaskNd, active_set_expanded: MaskNd) -> ArrayNd:
        values_next = hj_reachability.step(
            solver_settings=self._solver_settings,
            dynamics=self._hj_setup.dynamics,
            grid=self._hj_setup.grid,
            time=0,
            values=data.get_recent_values(),
            target_time=self._time_step,
            active_set=active_set_expanded,
            progress_bar=self._verbose
        )
        return data.get_recent_values()
