
import typing as tp
import collections
import numpy as np
import astropy.units as u
from beautifultable import BeautifulTable

from kgpy import optics
from . import Wavelength, WavelengthList, Field, FieldList, Surface, Component

__all__ = ['Configuration']


class Configuration(collections.UserList):

    object_str = 'Object'
    stop_str = 'Stop'
    image_str = 'Image'
    main_str = 'Main'

    def __init__(self, surfaces: tp.List[Surface] = None):

        super().__init__(surfaces)

        self.name = ''

        self.system = None

        self._entrance_pupil_radius = 0 * u.mm

        self._wavelengths = WavelengthList()

        self._fields = FieldList()

    @property
    def system(self) -> tp.Optional['optics.System']:
        return self._system

    @system.setter
    def system(self, value: tp.Optional['optics.System']):
        self._system = value

    @property
    def fields(self) -> FieldList:
        return self._fields

    @fields.setter
    def fields(self, value: FieldList):
        self._fields = value

    @property
    def wavelengths(self) -> WavelengthList:
        return self._wavelengths

    @wavelengths.setter
    def wavelengths(self, value: WavelengthList):
        self._wavelengths = value

    @property
    def entrance_pupil_radius(self) -> u.Quantity:
        return self._entrance_pupil_radius

    @entrance_pupil_radius.setter
    def entrance_pupil_radius(self, value: u.Quantity):
        self._entrance_pupil_radius = value

    @property
    def surfaces(self) -> tp.List[optics.system.configuration.Surface]:
        """
        :return: The private list of surfaces
        """
        return self.data

    @property
    def object(self) -> Surface:
        """
        :return: The object surface within the system, defined as the first surface in the list of surfaces.
        """
        return self[0]

    @property
    def image(self) -> Surface:
        """
        :return: The image surface within the system
        """
        return self[-1]

    @property
    def stop(self) -> Surface:
        """
        :return: The stop surface within the system
        """

        # Return the first surface specified as the stop surface
        try:
            return next(s for s in self if s.is_stop)

        # If there is no surface specified as the stop surface, select the first non-object surface and set it to the
        # stop surface
        except StopIteration:
            self.surfaces[1].is_stop = True

            # Recursive call to find new stop surface
            return self.stop

    @stop.setter
    def stop(self, surf: Surface):
        """
        Set the stop surface to the surface provided
        :param surf: Surface to set as the new stop
        :return: None
        """

        # Loop through all the surfaces in the system and find the provided surface
        for s in self:

            # Check if this is the provided surface
            if s is surf:

                # There can only be one surface, so make sure to update the previous stop surface
                self.stop.is_stop = False

                # Update the new stop surface
                surf.is_stop = True

                # Return once we found the stop surface so we can use the end of the loop as a control statement.
                return

        # If the loop exits the provided surface is not part of the system and this function call doesn't make sense.
        raise ValueError('Cannot set stop to surface not in system')


    @property
    def components(self) -> tp.Dict[str, Component]:
        """
        :return: a Dictionary with all the Components in the system as values and their names as the keys.
        """

        # Allocate space to store the new dictionary
        comp = {}

        # Loop through all the surfaces in the system
        for surf in self._surfaces:

            # If this surface is associated with a component
            if surf.component is not None:

                # Add this surface's component to the dictionary if it's not already there.
                if surf.component.name not in comp:
                    comp[surf.component.name] = surf.component

        return comp

    def insert(self, i: int, item: Surface):

        super().insert(i, item)

        # Make sure that the index is positive
        index = i % len(self)

        # Set the system pointer
        item.sys = self

        # Set the link to the surface before the new surface
        if index > 0:
            self[index - 1].next_surf_in_system = item
            item.prev_surf_in_system = self[index - 1]

        # Set the link to the surface after the new surface
        if index < len(self):
            self[index].prev_surf_in_system = item
            item.next_surf_in_system = self[index]

        # Reset the coordinate systems, to revaluate with the new surface
        item.reset_cs()

    def append(self, item: Surface):

        super().append(item)

        # Update link from surface to system
        item.sys = self

        # Link to the previous surface in the system
        if len(self) > 0:
            self[-1].next_surf_in_system = item
            item.prev_surf_in_system = self[-1]

    @property
    def _surfaces_dict(self) -> tp.Dict[str, optics.system.configuration.Surface]:
        """
        :return: a dictionary where the key is the surface name and the value is the surface.
        """

        # Allocate space for result
        d = {}

        # Loop through surfaces and add to dict
        for surf in self:
            d[surf.name] = surf

        return d

    def __str__(self) -> str:
        """
        :return: String representation of a system
        """

        # Create output table
        table = BeautifulTable(max_width=200)

        # Append lines for each surface within the component
        for surface in self.surfaces:

            # Add headers if not already populated
            if not table.column_headers:
                table.column_headers = surface.table_headers

            # Append surface to table
            table.append_row(surface.table_row)

        # Set column alignments
        table.column_alignments['Component'] = BeautifulTable.ALIGN_LEFT
        table.column_alignments['Surface'] = BeautifulTable.ALIGN_LEFT
        table.column_alignments['Thickness'] = BeautifulTable.ALIGN_RIGHT
        table.column_alignments['X_x'] = BeautifulTable.ALIGN_RIGHT
        table.column_alignments['X_y'] = BeautifulTable.ALIGN_RIGHT
        table.column_alignments['X_z'] = BeautifulTable.ALIGN_RIGHT
        table.column_alignments['T_x'] = BeautifulTable.ALIGN_RIGHT
        table.column_alignments['T_y'] = BeautifulTable.ALIGN_RIGHT
        table.column_alignments['T_z'] = BeautifulTable.ALIGN_RIGHT

        # Don't automatically format numeric strings
        table.detect_numerics = False

        return table.__str__()
