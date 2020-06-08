import typing as typ
import dataclasses
import numpy as np
import astropy.units as u

from . import Aperture, decenterable, obscurable

__all__ = ['Circular']


@dataclasses.dataclass
class Circular(decenterable.Decenterable, obscurable.Obscurable, Aperture):

    radius: u.Quantity = 0 * u.mm

    def to_zemax(self) -> 'Circular':
        raise NotImplementedError

    @property
    def config_broadcast(self):
        return np.broadcast(
            super().config_broadcast,
            self.radius,
        )

    def is_unvignetted(self, points: u.Quantity) -> np.ndarray:
        x = points[..., 0]
        y = points[..., 1]
        r = np.sqrt(np.square(x) + np.square(y))
        return r < self.radius

    @property
    def edges(self) -> u.Quantity:

        a = np.linspace(0 * u.deg, 360 * u.deg, num=self.num_samples)
        r = np.expand_dims(self.radius.copy(), ~0)

        x = r * np.cos(a)
        y = r * np.sin(a)
        z = np.broadcast_to(0, x.shape)

        return np.stack([x, y, z], axis=~0)
