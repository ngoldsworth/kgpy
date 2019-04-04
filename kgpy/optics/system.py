
import numpy as np
from typing import List, Dict, Union
import quaternion as q
import astropy.units as u
from beautifultable import BeautifulTable

from kgpy.math import CoordinateSystem
from kgpy.math.coordinate_system import GlobalCoordinateSystem as gcs
from kgpy.optics import Surface, Component

__all__ = ['System']


class System:
    """
    The System class simulates an entire optical system, and is represented as a series of Components.

    This class is intended to be a drop-in replacement for a Zemax system.
    """

    object_str = 'Object'
    stop_str = 'Stop'
    image_str = 'Image'
    main_str = 'Main'

    def __init__(self, name: str, comment: str = ''):
        """
        Define an optical system by providing a name.

        :param name: Human-readable name of the system
        :param comment: Additional information about the system.
        """

        # Save input arguments to class variables
        self.name = name
        self.comment = comment

        # Initialize attributes to be set as surfaces are added.
        self._surfaces = []     # type: List[Surface]

        # Create the object surface.
        obj = Surface(self.object_str, thickness=np.inf * u.mm)

        # Create stop surface.
        stop = Surface(self.stop_str)

        # Flag the surface to be the stop
        stop.is_stop = True

        # Create image surface
        image = Surface(self.image_str)

        # Add the three surfaces to the system
        self.append(obj)
        self.append(stop)
        self.append(image)

    @property
    def surfaces(self) -> List[Surface]:
        """
        :return: The private list of surfaces
        """
        return self._surfaces

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
    def components(self) -> Dict[str, Component]:
        """
        :return: A Dictionary with all the Components in the system as values and their names as the keys.
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

    def insert(self, surface: Surface, index: int) -> None:
        """
        Insert a surface into the specified position index the system
        :param surface: Surface object to be added to the system
        :param index: Index that we want the object to be placed at
        :return: None
        """

        # Make sure that the index is positive
        index = index % len(self)

        # Set the system pointer
        surface.sys = self

        # Set the link to the surface before the new surface
        if index > 0:
            self[index - 1].next_surf_in_system = surface
            surface.prev_surf_in_system = self[index - 1]

        # Set the link to the surface after the new surface
        if index < len(self):
            self[index].prev_surf_in_system = surface
            surface.next_surf_in_system = self[index]

        # Add the surface to the list of surfaces
        self._surfaces.insert(index, surface)

        # Reset the coordinate systems, to revaluate with the new surface
        surface.reset_cs()

    def append(self, surface: Surface) -> None:
        """
        Add a surface to the end of an optical system (but before the image).
        :param surface: The surface to be added.
        :return: None
        """

        # Update link from surface to system
        surface.sys = self

        # Link to the previous surface in the system
        if len(self) > 0:
            self[-1].next_surf_in_system = surface
            surface.prev_surf_in_system = self[-1]

        # Append surface to the list of surfaces
        self._surfaces.append(surface)

    def insert_component(self, component: Component, index: int) -> None:
        """
        Add the component and all its surfaces to the end of an optical system.
        :param component: component to be added to the system.
        :return: None
        """

        index = index % len(self)

        # Link the system to the component
        component.sys = self

        # Loop through the surfaces in the component add them to the back of the system
        for surf in component:
            self.insert(surf, index)
            index = index + 1

    def add_baffle(self, baffle_name: str, baffle_cs: CoordinateSystem) -> Component:
        """
        Add a baffle to the system at the specified coordinate system across the x-y plane.
        This function automatically calculates how many times the raypath crosses the baffle plane, and constructs the
        appropriate amount of baffle surfaces
        :param baffle_name: Human-readable name of the baffle
        :param baffle_cs: Coordinate system where the baffle will be placed.
        This function assumes that the baffle lies in the x-y plane of this coordinate system.
        :return: Pointer to Baffle component
        """

        # Create new component to store the baffle
        baffle = Component(baffle_name)

        # Define variable to track how many times the system intersected the
        baffle_pass = 0

        # Make a copy of the surfaces list so we don't try to iterate over and write to the same list
        old_surfaces = self._surfaces.copy()

        # Loop through all surfaces in the system to see if any intersect with a baffle
        for surf in old_surfaces:

            # Compute the intersection between the thickness vector and the x-y plane of the baffle, if it exists.
            intercept = baffle_cs.xy_intercept(surf.front_cs.X, surf.back_cs.X)

            # If the intercept exists, insert the new baffle
            if intercept is not None:

                # Compute the new thickness vectors for both to
                t1 = intercept - surf.front_cs.X  # New thickness of original surface
                t2 = surf.back_cs.X - intercept   # Thickness of new surface to be added after the baffle

                # Modify the original surface to have the correct thickness
                surf.thickness = t1.dot(surf.front_cs.zh)

                # Calculate the tilt/decenter required to put the baffle in the correct place
                cs = baffle_cs.diff(surf.back_cs)

                # Create new baffle surface
                baffle_thickness = t2.dot(surf.front_cs.zh)
                baffle_surf = Surface(baffle_name, thickness=baffle_thickness)
                baffle_surf.comment = 'pass = ' + str(baffle_pass)
                baffle_surf.before_surf_cs_break = cs
                baffle_surf.after_surf_cs_break = cs.inverse

                # Link the new baffle surface into the system
                self.insert(baffle_surf, surf.system_index + 1)

                # Insert new baffle surface into baffle component
                baffle.append(baffle_surf)

                # Update the number of baffle passes
                baffle_pass += 1

        return baffle

    @property
    def _surfaces_dict(self) -> Dict[str, Surface]:
        """
        :return: A dictionary where the key is the surface name and the value is the surface.
        """

        # Allocate space for result
        d = {}

        # Loop through surfaces and add to dict
        for surf in self:
            d[surf.name] = surf

        return d

    # @property
    # def _all_surfaces(self) -> List[Surface]:
    #     """
    #     :return: A list of all surfaces in the object, including the object and image surfaces
    #     """
    #     return [self.object] + self._surfaces + [self.image]

    def __getitem__(self, item: Union[int, str]) -> Surface:
        """
        Gets the surface at index item within the system, or the surface with the name item
        Accessed using the square bracket operator, e.g. surf = sys[i]
        :param item: Surface index or name of surface
        :return: Surface specified by item
        """

        # If the item is an integer, use it to access the surface list
        if isinstance(item, int):
            return self._surfaces.__getitem__(item)

        # If the item is a string, use it to access the surfaces dictionary.
        elif isinstance(item, str):
            return self._surfaces_dict.__getitem__(item)

        # Otherwise, the item is neither an int nor string and we throw an error.
        else:
            raise ValueError('Item is of an unrecognized type')

    def __delitem__(self, key: int):

        self[key].sys = None

        self._surfaces.__delitem__(key)

    def __iter__(self):

        return self._surfaces.__iter__()

    def __len__(self):

        return self._surfaces.__len__()

    def __str__(self) -> str:
        """
        :return: String representation of a system
        """

        # Create output table
        table = BeautifulTable(max_width=200)

        # Append lines for each surface within the component
        for surface in self._surfaces:

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
