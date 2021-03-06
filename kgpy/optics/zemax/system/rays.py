import typing as tp
import time
import numpy as np
import nptyping as npt
import astropy.units as u

from kgpy.optics.system import Rays
from kgpy.optics.zemax import ZOSAPI

__all__ = ['trace']


def trace(
        zemax_system: ZOSAPI.IOpticalSystem,
        zemax_units: u.Unit,
        num_pupil: tp.Union[int, tp.Tuple[int, int]] = 5,
        num_field: tp.Union[int, tp.Tuple[int, int]] = 5,
        mask: npt.Array[bool] = None,
        configuration_indices: tp.Optional[tp.List[int]] = None,
        surface_indices: tp.Optional[tp.List[int]] = (~0,),
        wavelength_indices=None,
) -> Rays:
    """
    General Zemax raytracing function.
    Trace a specified number of pupil/field points through an optical system.
    :param zemax_system: Pointer to Zemax optical system.
    :param zemax_units: Lens units of the Zemax optical system.
    :param num_pupil: Number of pupil positions to sample.
    If scalar, this is the number of points per axis.
    If a pair of numbers, the first value is the number of pupil positions along the x-axis and the second value is the
    number of pupil positions along the y-axis.
    :param num_field: Number of field positions to sample.
    This argument can be either a scalar or a pair of numbers, with the same format as `num_pupil`.
    :param mask:
    :param configuration_indices:
    :param surface_indices:
    :param wavelength_indices:
    :return:
    """

    if isinstance(num_field, int):
        num_field = num_field, num_field

    if isinstance(num_pupil, int):
        num_pupil = num_pupil, num_pupil

    field_x = np.linspace(-1, 1, num_field[0])
    field_y = np.linspace(-1, 1, num_field[1])
    pupil_x = np.linspace(-1, 1, num_pupil[0])
    pupil_y = np.linspace(-1, 1, num_pupil[1])

    fg_x, fg_y, pg_x, pg_y = np.meshgrid(field_x, field_y, pupil_x, pupil_y, indexing='ij')

    if mask is None:
        mask = np.broadcast_to(1, fg_x.shape)

    if configuration_indices is None:
        configuration_indices = np.arange(zemax_system.MCE.NumberOfConfigurations)

    if surface_indices is None:
        surface_indices = np.arange(zemax_system.LDE.NumberOfSurfaces - 1)
    surface_indices = np.array(surface_indices) % zemax_system.LDE.NumberOfSurfaces

    if wavelength_indices is None:
        wavelength_indices = np.arange(zemax_system.SystemData.Wavelengths.NumberOfWavelengths)

    starting_config = zemax_system.MCE.CurrentConfiguration

    total_num_rays = 100 * 100 * 100

    sh = (
             len(configuration_indices),
             len(surface_indices),
             len(wavelength_indices),
         ) + fg_x.shape

    rays = Rays.empty(sh)

    zf = zemax_system.SystemData.Fields
    fx = [zf.GetField(f).X for f in range(1, zf.NumberOfFields + 1)] * u.deg
    fy = [zf.GetField(f).Y for f in range(1, zf.NumberOfFields + 1)] * u.deg
    max_field_x = np.max(fx)
    max_field_y = np.max(fy)
    if zf.Normalization == ZOSAPI.SystemData.FieldNormalizationType.Radial:
        r = np.sqrt(max_field_x ** 2 + max_field_y ** 2)
        max_field_x = max_field_y = r

    pfield_x = field_x * max_field_x
    pfield_y = field_y * max_field_y
    wavelengths = u.Quantity([zemax_system.SystemData.Wavelengths.GetWavelength(w + 1).Wavelength * u.um for w in
                              wavelength_indices])
    rays.input_coordinates = pfield_x, pfield_y, wavelengths

    for c, config_index in enumerate(configuration_indices):

        zemax_system.MCE.SetCurrentConfiguration(config_index + 1)

        rt = zemax_system.Tools.OpenBatchRayTrace()
        tool = zemax_system.Tools.CurrentTool

        for s, surf_index in enumerate(surface_indices):

            # rt_dat = rt.CreateNormUnpol(total_num_rays, ZOSAPI.Tools.RayTrace.RaysType.Real, surf_index + 1)

            for w, wavl_index in enumerate(wavelength_indices):

                # for ix, fx in enumerate(field_x):
                #     for iy, fy in enumerate(field_y):
                #         for jx, px in enumerate(pupil_x):
                #             for jy, py in enumerate(pupil_y):
                #                 if mask[ix, iy, jx, jy] == 1:
                #                     rt_dat.AddRay(wavl_index + 1, fx, fy, px, py, ZOSAPI.Tools.RayTrace.OPDMode.None_)
                #
                # tool.RunAndWaitForCompletion()
                # # time.sleep(0.1)
                #
                # rt_dat.StartReadingResults()

                for ix, fx in enumerate(field_x):
                    for iy, fy in enumerate(field_y):
                        for jx, px in enumerate(pupil_x):
                            for jy, py in enumerate(pupil_y):
                                if mask[ix, iy, jx, jy] == 1:
                                    # zemax_ray = rt_dat.ReadNextResult()
                                    zemax_ray = rt.SingleRayNormUnpol(ZOSAPI.Tools.RayTrace.RaysType.Real,
                                                                      surf_index + 1,
                                                                      wavl_index + 1, fx, fy, px, py,
                                                                      ZOSAPI.Tools.RayTrace.OPDMode.None_)
                                    ret, err, vig, x, y, z, l, m, n, l2, m2, n2, opd, intensity = zemax_ray

                                    ind = c, s, w, ix, iy, jx, jy

                                    x_ind = ind + (0,)
                                    y_ind = ind + (1,)
                                    z_ind = ind + (2,)

                                    rays.position[x_ind] = x * zemax_units
                                    rays.position[y_ind] = y * zemax_units
                                    rays.position[z_ind] = z * zemax_units
                                    rays.direction[x_ind] = l
                                    rays.direction[y_ind] = m
                                    rays.direction[z_ind] = n
                                    rays.surface_normal[x_ind] = l2
                                    rays.surface_normal[y_ind] = m2
                                    rays.surface_normal[z_ind] = n2
                                    rays.mask[ind] = vig == 0 and err == 0

                # rt_dat.ClearData()

        tool.Close()

    zemax_system.MCE.SetCurrentConfiguration(starting_config)

    return rays
