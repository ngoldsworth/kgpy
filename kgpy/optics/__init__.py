"""
kgpy.optics is a package designed to help simulations of optical systems
"""

__all__ = ['ZemaxCompatible', 'OCC_Compatible', 'coordinate', 'Rays', 'Material', 'Aperture', 'Surface', 'System']

from .zemax_compatible import ZemaxCompatible
from .occ_compatible import OCC_Compatible
from . import coordinate
from .rays import Rays
from .material import Material
from .aperture import Aperture
from .surface import Surface
from .system import System
