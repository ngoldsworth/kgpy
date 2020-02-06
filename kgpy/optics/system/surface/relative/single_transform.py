import dataclasses
import typing as typ

from ... import Name, mixin, coordinate
from .. import Surface, Standard, CoordinateTransform

SurfacesT = typ.TypeVar('SurfacesT')


@dataclasses.dataclass
class SingleTransform(mixin.Named, typ.Generic[SurfacesT]):
    """
    This object lets you place a list of surfaces relative to the position of the current surface, and then return to
    the position of the current surface after the list of surfaces.
    This is useful if an optical component is represented as more than one surface and each surface needs to move in
    tandem.
    """

    surfaces: SurfacesT = dataclasses.field(default_factory=lambda: Standard())
    cbreak_before: CoordinateTransform = None
    cbreak_after: CoordinateTransform = None
    is_last_surface: bool = False

    def __post_init__(self):

        if self.cbreak_before is None:
            self.cbreak_before = CoordinateTransform(name=Name(self.name, 'cb_before'))

        if self.cbreak_after is None:
            self.cbreak_after = CoordinateTransform(name=Name(self.name, 'cb_after'))

    @classmethod
    def from_properties(
            cls,
            name: Name,
            main: SurfacesT,
            transform: typ.Optional[coordinate.Transform] = None
    ):

        if transform is None:
            transform = coordinate.Transform()

        s = cls(name, main)
        s.transform = transform

        return s

    @property
    def transform(self) -> coordinate.Transform:
        return self.cbreak_before.transform

    @transform.setter
    def transform(self, value: coordinate.Transform):
        self.cbreak_before.transform = value
        self.cbreak_after.transform = ~value

    def __iter__(self):

        yield from self.cbreak_before

        yield from self.surfaces

        yield from self.cbreak_after