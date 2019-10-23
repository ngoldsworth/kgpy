import dataclasses
import abc
import typing as tp
import numpy as np
import nptyping as npt
import astropy.units as u

from kgpy import math, optics

__all__ = ['Aperture']


@dataclasses.dataclass
class Aperture(abc.ABC):

    is_obscuration: tp.Union[bool, npt.Array[bool]] = False

    @property
    @abc.abstractmethod
    def points(self) -> u.Quantity:
        pass


@dataclasses.dataclass
class Circular(Aperture):

    radius: u.Quantity = 0 * u.mm


@dataclasses.dataclass
class Rectangular(Aperture):

    decenter_x: u.Quantity = 0 * u.mm
    decenter_y: u.Quantity = 0 * u.mm
    half_width_x: u.Quantity = 0 * u.mm
    half_width_y: u.Quantity = 0 * u.mm

    @property
    def points(self) -> u.Quantity:
        return u.Quantity([
            u.Quantity([self.half_width_x, self.half_width_y]),
            u.Quantity([self.half_width_x, -self.half_width_y]),
            u.Quantity([-self.half_width_x, -self.half_width_y]),
            u.Quantity([-self.half_width_x, self.half_width_y]),
        ])


@dataclasses.dataclass
class RegularPolygon(Aperture):

    radius: u.Quantity = 0 * u.mm
    num_sides: int = 8

    @property
    def points(self) -> u.Quantity:

        # Calculate angles
        angles = np.linspace(0, 2 * np.pi, self.num_sides, endpoint=False) * u.rad  # type: u.Quantity

        # Calculate points
        x = self.radius * np.cos(angles)  # type: u.Quantity
        y = self.radius * np.sin(angles)  # type: u.Quantity
        pts = u.Quantity([x, y])
        pts = pts.transpose()   # type: u.Quantity

        return pts
