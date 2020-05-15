import dataclasses
import typing as typ
import numpy as np
import astropy.units as u
from .. import Rays
from . import Surface

__all__ = ['ObjectSurface']


@dataclasses.dataclass
class ObjectSurface(Surface):

    def to_zemax(self):
        raise NotImplementedError

    def normal(self, x: u.Quantity, y: u.Quantity) -> u.Quantity:
        return u.Quantity([0, 0, 1])

    def propagate_rays(self, rays: Rays, is_first_surface: bool = False, is_final_surface: bool = False) -> typ.NoReturn:
        if not is_first_surface:
            raise ValueError('Object surface must be first surface')

        if is_final_surface:
            raise ValueError('Object surface must not be last surface')

        if np.isfinite(self.thickness):
            rays.pz -= self.thickness
