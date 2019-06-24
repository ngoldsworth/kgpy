
from kgpy import optics

from kgpy.optics.zemax import ZOSAPI

__all__ = ['Configuration']


class Configuration(optics.system.Configuration):

    def __init__(self, name: str):

        super().__init__(name)

    @classmethod
    def conscript(cls, config: optics.system.Configuration):

        zmx_config = cls(config.name)

        zmx_config.entrance_pupil_radius = config.entrance_pupil_radius
        zmx_config.wavelengths = config.wavelengths
        zmx_config.fields = config.fields

        for surf in config:

            zmx_surf = optics.zemax.system.configuration.Surface.conscript(surf)

            zmx_config.append(zmx_surf)

    @property
    def system(self) -> 'optics.zemax.System':
        return super().system

    @system.setter
    def system(self, value: 'optics.zemax.System'):
        super().system = value

    @property
    def fields(self) -> optics.system.configuration.field.FieldList:
        return self._fields

    @fields.setter
    def fields(self, value: optics.system.configuration.field.FieldList):
        self._fields = value.promote_to_zmx(self.zos_sys)

    @property
    def wavelengths(self) -> optics.system.configuration.wavelength.WavelengthList:
        return self._wavelengths

    @wavelengths.setter
    def wavelengths(self, value: optics.system.configuration.wavelength.WavelengthList):
        self._wavelengths = value.promote_to_zmx(self.zos_sys)

    @property
    def entrance_pupil_radius(self):

        if self.zos_sys is not None:

            a = self.zos_sys.SystemData.Aperture

            if a.ApertureType == ZOSAPI.SystemData.ZemaxApertureType.EntrancePuilDiameter:
                return (a.ApertureValue / 2) * self.lens_units

            else:
                raise ValueError('Aperture not defined by entrance pupil diameter')

        else:
            return self._entrance_pupil_radius

    @entrance_pupil_radius.setter
    def entrance_pupil_radius(self, value: u.Quantity):

        if self.zos_sys is not None:

            a = self.zos_sys.SystemData.Aperture

            a.ApertureType = ZOSAPI.SystemData.ZemaxApertureType.EntrancePuilDiameter

            a.ApertureValue = 2 * value.to(self.lens_units).value

        else:
            self._entrance_pupil_radius = value

    @property
    def num_surfaces(self) -> int:
        """
        :return: The number of surfaces in the system
        """
        return self.zos_sys.LDE.NumberOfSurfaces

    def insert(self, surf: zemax.system.configuration, index: int) -> None:
        """
        Insert a new surface at the specified index in the model
        :param surf: Surface to insert into the model
        :param index: Index where the surface will be placed in the model
        :return: None
        """

        # Call superclass method to insert this surface into the list of surfaces
        super().insert(surf, index)

        # Insert a main attribute into this Zemax surface.
        # This adds an ILDERow to the surface.
        surf.insert(ZmxSurface.main_str, ZOSAPI.Editors.LDE.SurfaceType.Standard)