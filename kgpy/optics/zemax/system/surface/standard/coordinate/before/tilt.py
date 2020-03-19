import dataclasses

from kgpy.optics.zemax import ZOSAPI
from ..... import configuration, surface
from . import tilt_decenter

__all__ = ['Tilt']


@dataclasses.dataclass
class Tilt(surface.coordinate.Tilt[tilt_decenter.TiltDecenter[surface.Standard]]):

    _x_op: configuration.SurfaceOperand = dataclasses.field(
        default_factory=lambda: configuration.SurfaceOperand(
            op_type=ZOSAPI.Editors.MCE.MultiConfigOperandType.CBTX,
        ),
        init=False,
        repr=False,
    )
    _y_op: configuration.SurfaceOperand = dataclasses.field(
        default_factory=lambda: configuration.SurfaceOperand(
            op_type=ZOSAPI.Editors.MCE.MultiConfigOperandType.CBTY,
        ),
        init=False,
        repr=False,
    )
    _z_op: configuration.SurfaceOperand = dataclasses.field(
        default_factory=lambda: configuration.SurfaceOperand(
            op_type=ZOSAPI.Editors.MCE.MultiConfigOperandType.CBTZ,
        ),
        init=False,
        repr=False,
    )

    def _x_setter(self, value: float):
        self.tilt_decenter.surface.lde_row.TiltDecenterData.BeforeSurfaceTiltX = value

    def _y_setter(self, value: float):
        self.tilt_decenter.surface.lde_row.TiltDecenterData.BeforeSurfaceTiltY = value

    def _z_setter(self, value: float):
        self.tilt_decenter.surface.lde_row.TiltDecenterData.BeforeSurfaceTiltZ = value
