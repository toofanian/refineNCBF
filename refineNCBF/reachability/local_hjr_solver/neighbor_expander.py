from abc import ABC, abstractmethod
from typing import Callable

import attr

from verify_ncbf.toof.src.reachability.reachability_utils.results import LocalUpdateResult
from verify_ncbf.toof.src.utils.carving.masks import expand_mask_by_signed_distance
from verify_ncbf.toof.src.utils.typing.types import MaskNd


@attr.s(auto_attribs=True)
class NeighborExpander(ABC, Callable):
    @abstractmethod
    def __call__(self, data: LocalUpdateResult, source_set: MaskNd) -> MaskNd:
        ...


@attr.s(auto_attribs=True)
class SignedDistanceNeighbors(NeighborExpander):
    _distance: float

    @classmethod
    def from_parts(cls, distance: float):
        return cls(distance=distance)

    def __call__(self, data: LocalUpdateResult, source_set: MaskNd) -> MaskNd:
        expanded_set = expand_mask_by_signed_distance(source_set, self._distance)
        return expanded_set
