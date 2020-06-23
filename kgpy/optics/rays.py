import dataclasses
import typing as typ
import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
import astropy.visualization
import kgpy.vector
from kgpy.vector import x, y, z
from . import coordinate

__all__ = ['Rays']


class AutoAxis:

    def __init__(self):
        super().__init__()
        self.ndim = 0
        self.all = []

    def auto_axis_index(self):
        i = ~self.ndim
        self.all.append(i)
        self.ndim += 1
        return i

    def perp_axes(self, axis: int):
        axes = self.all.copy()
        axes.remove(axis)
        return axes


class CAxis(AutoAxis):
    def __init__(self):
        super().__init__()
        self.components = self.auto_axis_index()


class Axis(AutoAxis):
    def __init__(self):
        super().__init__()
        self.pupil_y = self.auto_axis_index()
        self.pupil_x = self.auto_axis_index()
        self.field_y = self.auto_axis_index()
        self.field_x = self.auto_axis_index()
        self.wavelength = self.auto_axis_index()
        self.surface = self.auto_axis_index()


class VAxis(Axis, CAxis):
    pass


@dataclasses.dataclass
class Rays:

    axis = Axis()
    vaxis = VAxis()

    wavelength: u.Quantity
    position: u.Quantity
    direction: u.Quantity
    polarization: u.Quantity = None
    surface_normal: u.Quantity = None
    index_of_refraction: u.Quantity = None
    vignetted_mask: np.ndarray = None
    error_mask: np.ndarray = None

    wavelength_grid: typ.Optional[u.Quantity] = None
    field_grid_x: typ.Optional[u.Quantity] = None
    field_grid_y: typ.Optional[u.Quantity] = None
    pupil_grid_x: typ.Optional[u.Quantity] = None
    pupil_grid_y: typ.Optional[u.Quantity] = None

    def __post_init__(self):
        if self.polarization is None:
            self.polarization = np.zeros(self.vector_grid_shape) << u.dimensionless_unscaled
            self.polarization[z] = 1
        if self.surface_normal is None:
            self.surface_normal = np.zeros(self.vector_grid_shape) << u.dimensionless_unscaled
            self.surface_normal[z] = 1
        if self.index_of_refraction is None:
            self.surface_normal = np.zeros(self.vector_grid_shape) << u.dimensionless_unscaled
            self.surface_normal[z] = 1
        if self.vignetted_mask is None:
            self.vignetted_mask = np.ones(self.grid_shape, dtype=np.bool)
        if self.error_mask is None:
            self.error_mask = np.ones(self.grid_shape, dtype=np.bool)

    @classmethod
    def from_field_angles(
            cls,
            wavelength_grid: u.Quantity,
            position: u.Quantity,
            field_grid_x: u.Quantity,
            field_grid_y: u.Quantity,
            field_mask_func: typ.Optional[typ.Callable[[u.Quantity, u.Quantity], np.ndarray]] = None,
            pupil_grid_x: typ.Optional[u.Quantity] = None,
            pupil_grid_y: typ.Optional[u.Quantity] = None,
    ) -> 'Rays':
        wavelength = np.expand_dims(wavelength_grid, cls.vaxis.perp_axes(cls.vaxis.wavelength))
        field_x = np.expand_dims(field_grid_x, cls.vaxis.perp_axes(cls.vaxis.field_x))
        field_y = np.expand_dims(field_grid_y, cls.vaxis.perp_axes(cls.vaxis.field_y))

        wavelength, position, field_x, field_y = np.broadcast_arrays(wavelength, position, field_x, field_y, )

        mask = field_mask_func(field_x, field_y)

        direction = np.zeros(position.shape)
        direction[z] = 1
        direction = kgpy.vector.rotate_x(direction, field_x)
        direction = kgpy.vector.rotate_y(direction, field_y)

        return cls(
            wavelength=wavelength,
            position=position,
            direction=direction,
            vignetted_mask=mask,
            wavelength_grid=wavelength_grid,
            field_grid_x=field_grid_x,
            field_grid_y=field_grid_y,
            pupil_grid_x=pupil_grid_x,
            pupil_grid_y=pupil_grid_y,
        )

    @classmethod
    def zeros(cls, shape: typ.Tuple[int, ...] = ()):
        vsh = shape + (3, )
        ssh = shape + (1, )

        direction = np.zeros(vsh) << u.dimensionless_unscaled
        polarization = np.zeros(vsh) << u.dimensionless_unscaled
        normal = np.zeros(vsh) << u.dimensionless_unscaled

        direction[kgpy.vector.z] = 1
        polarization[kgpy.vector.x] = 1
        normal[kgpy.vector.z] = 1

        return cls(
            wavelength=np.zeros(ssh) << u.nm,
            position=np.zeros(vsh) << u.mm,
            direction=direction,
            polarization=polarization,
            surface_normal=normal,
            index_of_refraction=np.ones(ssh) << u.dimensionless_unscaled,
            vignetted_mask=np.ones(shape, dtype=np.bool),
            error_mask=np.ones(shape, dtype=np.bool),
        )

    def tilt_decenter(self, transform: coordinate.TiltDecenter) -> 'Rays':
        return type(self)(
            wavelength=self.wavelength.copy(),
            position=transform(self.position, num_extra_dims=5),
            direction=transform(self.direction, decenter=False, num_extra_dims=5),
            polarization=self.polarization.copy(),
            surface_normal=transform(self.surface_normal, decenter=False, num_extra_dims=5),
            index_of_refraction=self.index_of_refraction.copy(),
            unvignetted_mask=self.vignetted_mask.copy(),
            error_mask=self.error_mask.copy(),
        )

    @property
    def grid_shape(self) -> typ.Tuple[int, ...]:
        return np.broadcast(
            self.wavelength[x],
            self.position[x],
            self.direction[x],
            self.surface_normal[x],
            self.polarization[x],
            self.index_of_refraction[x],
            self.vignetted_mask,
            self.error_mask,
        ).shape

    @property
    def vector_grid_shape(self) -> typ.Tuple[int, ...]:
        return self.grid_shape + (3, )

    @property
    def scalar_shape(self) -> typ.Tuple[int, ...]:
        return self.grid_shape + (1, )

    @property
    def shape(self) -> typ.Tuple[int, ...]:
        return self.vector_grid_shape[:~self.vaxis.ndim]

    @property
    def ndim(self):
        return len(self.shape)

    @property
    def mask(self) -> np.ndarray:
        return self.vignetted_mask & self.error_mask

    @property
    def relative_position(self):
        pupil_axes = (self.vaxis.pupil_x, self.vaxis.pupil_y)
        avg_position = np.mean(self.position.value, axis=pupil_axes, keepdims=True) << self.position.unit
        avg_position = avg_position << self.position.unit
        return self.position - avg_position

    def mean_sparse_grid(self, config_index: typ.Union[int, typ.Tuple[int, ...]]) -> typ.List[np.ndarray]:
        axes = self.axis.all
        out = [None] * len(axes)
        for axis in axes:
            other_axes = axes.copy()
            other_axes.remove(axis)
            other_axes = tuple(other_axes)

            if axis == self.axis.wavelength:
                grid = self.wavelength[config_index][..., 0]
            elif axis == self.axis.field_x:
                grid = self.direction[config_index][kgpy.vector.x]
            elif axis == self.axis.field_y:
                grid = self.direction[config_index][kgpy.vector.y]
            elif axis == self.axis.pupil_x:
                grid = self.relative_position[config_index][kgpy.vector.x]
            elif axis == self.axis.pupil_y:
                grid = self.relative_position[config_index][kgpy.vector.y]
            else:
                raise ValueError('unsupported axis index')
            out[axis] = grid.mean(other_axes)

        return out

    def copy(self) -> 'Rays':
        return Rays(
            wavelength=self.wavelength.copy(),
            position=self.position.copy(),
            direction=self.direction.copy(),
            surface_normal=self.surface_normal.copy(),
            unvignetted_mask=self.vignetted_mask.copy(),
            error_mask=self.error_mask.copy(),
            polarization=self.polarization.copy(),
            index_of_refraction=self.index_of_refraction.copy(),
        )

    def pupil_hist2d(
            self,
            bins: typ.Union[int, typ.Tuple[int, int]] = 10,
            limits: typ.Optional[typ.Tuple[typ.Tuple[int, int], typ.Tuple[int, int]]] = None,
            use_vignetted: bool = False,
            relative_to_centroid: bool = False,
    ) -> typ.Tuple[np.ndarray, np.ndarray, np.ndarray]:

        if isinstance(bins, int):
            bins = (bins, bins)

        if not use_vignetted:
            mask = self.mask
        else:
            mask = self.error_mask

        position = self.position.copy()
        if relative_to_centroid:
            axes = (self.vaxis.pupil_x, self.vaxis.pupil_y)
            position -= np.mean(position.value, axis=axes, keepdims=True) << position.unit

        if limits is None:
            px = position[kgpy.vector.x]
            py = position[kgpy.vector.y]
            if not use_vignetted:
                px = px[self.mask]
                py = py[self.mask]
            print(px.shape)
            limits = (
                (px.min().value, px.max().value),
                (py.min().value, py.max().value),
            )

        base_shape = self.shape[:~1]
        hist = np.empty(base_shape + tuple(bins))
        edges_x = np.empty(base_shape + (bins[kgpy.vector.ix] + 1,))
        edges_y = np.empty(base_shape + (bins[kgpy.vector.iy] + 1,))

        for c, p_c in enumerate(position):
            for w, p_cw in enumerate(p_c):
                for i, p_cwi in enumerate(p_cw):
                    for j, p_cwij in enumerate(p_cwi):
                        cwij = c, w, i, j
                        hist[cwij], edges_x[cwij], edges_y[cwij] = np.histogram2d(
                            x=p_cwij[kgpy.vector.x].flatten().value,
                            y=p_cwij[kgpy.vector.y].flatten().value,
                            bins=bins,
                            weights=mask[cwij].flatten(),
                            range=limits,
                        )

        unit = self.position.unit
        return hist, edges_x << unit, edges_y << unit

    def plot_pupil_hist2d_vs_field(
            self,
            config_index: int = 0,
            wavlen_index: int = 0,
            bins: typ.Union[int, typ.Tuple[int, int]] = 10,
            limits: typ.Optional[typ.Tuple[typ.Tuple[int, int], typ.Tuple[int, int]]] = None,
            use_vignetted: bool = False,
            field_x: typ.Optional[u.Quantity] = None,
            field_y: typ.Optional[u.Quantity] = None,
    ) -> plt.Figure:

        if field_x is None:
            fax_x = (self.axis.field_y, self.axis.pupil_x, self.axis.pupil_y)
            field_x = self.direction[config_index, wavlen_index, ..., kgpy.vector.ix].mean(fax_x)
            field_x = np.arcsin(field_x) << u.rad
        if field_y is None:
            fax_y = (self.axis.field_x, self.axis.pupil_x, self.axis.pupil_y)
            field_y = self.direction[config_index, wavlen_index, ..., kgpy.vector.iy].mean(fax_y)
            field_y = np.arcsin(field_y) << u.rad

        hist, edges_x, edges_y = self.pupil_hist2d(
            bins=bins,
            limits=limits,
            use_vignetted=use_vignetted,
            relative_to_centroid=True,
        )

        fig, axs = plt.subplots(
            nrows=self.shape[self.axis.field_x],
            ncols=self.shape[self.axis.field_y],
            sharex='all',
            sharey='all',
            figsize=(9, 7)
        )

        for i, axs_i in enumerate(axs):
            for j, axs_ij in enumerate(axs_i):
                axs_ij.invert_xaxis()
                cwji = config_index, wavlen_index, j, i
                limits = [
                    edges_x[cwji].min().value,
                    edges_x[cwji].max().value,
                    edges_y[cwji].min().value,
                    edges_y[cwji].max().value,
                ]
                img = axs_ij.imshow(
                    X=hist[cwji].T,
                    extent=limits,
                    aspect='auto',
                    origin='lower',
                    vmin=hist[config_index, wavlen_index].min(),
                    vmax=hist[config_index, wavlen_index].max(),
                )
                if i == 0:
                    axs_ij.set_xlabel('{0.value:0.2f} {0.unit:latex}'.format(field_x[j].to(u.deg)))
                    axs_ij.xaxis.set_label_position('top')
                elif i == len(axs) - 1:
                    axs_ij.set_xlabel(edges_x.unit)

                if j == 0:
                    axs_ij.set_ylabel(edges_y.unit)
                elif j == len(axs_i) - 1:
                    axs_ij.set_ylabel('{0.value:0.2f} {0.unit:latex}'.format(field_y[i].to(u.deg)))
                    axs_ij.yaxis.set_label_position('right')

        wavl_str = np.unique(self.wavelength[config_index, wavlen_index]).squeeze()
        wavl_str = '{0.value:0.3f} {0.unit:latex}'.format(wavl_str)
        fig.suptitle('configuration = ' + str(config_index) + ', wavelength = ' + wavl_str)
        fig.colorbar(img, ax=axs, fraction=0.05)

        return fig


