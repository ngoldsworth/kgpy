import dataclasses
import typing as typ
import astropy.units as u
import kgpy.component
from .... import coordinate as base_coordinate
from .. import coordinate

__all__ = ['Tilt']


@dataclasses.dataclass
class Tilt(kgpy.component.Component['coordinate.Transform'], base_coordinate.Tilt):

    def _update(self) -> typ.NoReturn:
        super()._update()
        self.x = self.x
        self.y = self.y
        self.z = self.z

    @property
    def x(self) -> u.Quantity:
        return self._x

    @x.setter
    def x(self, value: u.Quantity):
        self._x = value
        try:
            self._composite._cb_tilt.transform.tilt.x = value
            self._composite._cb_translate.transform.tilt.x = 0 * u.deg
        except AttributeError:
            pass

    @property
    def y(self) -> u.Quantity:
        return self._y

    @y.setter
    def y(self, value: u.Quantity):
        self._y = value
        try:
            self._composite._cb_tilt.transform.tilt.y = value
            self._composite._cb_translate.transform.tilt.y = 0 * u.deg
        except AttributeError:
            pass

    @property
    def z(self) -> u.Quantity:
        return self._z

    @z.setter
    def z(self, value: u.Quantity):
        self._z = value
        try:
            self._composite._cb_tilt.transform.tilt.z = value
            self._composite._cb_translate.transform.tilt.z = 0 * u.deg
        except AttributeError:
            pass
