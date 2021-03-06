import dataclasses
import typing as typ
import numpy as np
import astropy.units as u
import kgpy.vector
from kgpy.vector import x, y, z
from .. import Rays, coordinate
from . import surface

__all__ = ['CoordinateBreak']


@dataclasses.dataclass
class CoordinateBreak(surface.Surface):

    transform: coordinate.TiltDecenter = dataclasses.field(default_factory=lambda: coordinate.TiltDecenter())

    @property
    def __init__args(self) -> typ.Dict[str, typ.Any]:
        args = super().__init__args
        args.update({
            'transform': self.transform
        })
        return args

    @property
    def config_broadcast(self):
        return np.broadcast(
            super().config_broadcast,
            self.transform.config_broadcast,
        )

    def to_zemax(self) -> 'CoordinateBreak':
        from kgpy.optics import zemax
        return zemax.system.surface.CoordinateBreak(**self.__init__args)

    def sag(self, x: u.Quantity, y: u.Quantity) -> u.Quantity:
        return 0 * u.mm

    def normal(self, x: u.Quantity, y: u.Quantity) -> u.Quantity:
        return u.Quantity([0, 0, 1])

    def propagate_rays(self, rays: Rays, is_first_surface: bool = False, is_final_surface: bool = False, ) -> Rays:
        if not is_first_surface:
            rays = rays.tilt_decenter(~self.transform)

        if not is_final_surface:
            rays = rays.copy()
            rays.position[z] -= self.thickness

        return rays

    def apply_pre_transforms(self, x: u.Quantity, num_extra_dims: int = 0) -> u.Quantity:
        return self.transform(x, num_extra_dims=num_extra_dims)

    def apply_post_transforms(self, x: u.Quantity, num_extra_dims: int = 0) -> u.Quantity:
        x[kgpy.vector.z] += self.thickness
        return x
