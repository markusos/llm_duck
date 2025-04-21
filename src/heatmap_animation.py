import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.ndimage as ndimage

from src.map_animation_base import MapAnimationBase


class HeatmapAnimation(MapAnimationBase):
    """Class to create density-based heatmap animations"""

    CELL_RESOLUTION: int = 200
    KM_PER_LATITUDE: float = 111
    COLORMAP: str = "viridis"
    ALPHA: float = 0.7

    def __init__(
        self,
        df: pd.DataFrame,
        date_field: str,
        label: str,
        output_path: str = "./output/",
    ) -> None:
        self._bounds = None
        super().__init__(
            df,
            date_field=date_field,
            label=label,
            output_path=output_path,
        )
        self._setup_grid()

    def _setup_grid(self) -> None:
        min_lon, max_lon, min_lat, max_lat = self._bounds
        self.x_grid = np.linspace(min_lon, max_lon, self.CELL_RESOLUTION)
        self.y_grid = np.linspace(min_lat, max_lat, self.CELL_RESOLUTION)
        self.x_mesh, self.y_mesh = np.meshgrid(self.x_grid, self.y_grid)
        self.cell_area_km2 = self._calculate_cell_area_km2()

    def _calculate_cell_area_km2(self) -> float:
        mean_latitude = np.mean([self._bounds[2], self._bounds[3]])
        km_per_longitude = np.cos(mean_latitude * np.pi / 180) * self.KM_PER_LATITUDE

        total_area = (
            self.KM_PER_LATITUDE
            * km_per_longitude
            * abs(self._bounds[1] - self._bounds[0])
            * abs(self._bounds[3] - self._bounds[2])
        )
        return total_area / (self.CELL_RESOLUTION * self.CELL_RESOLUTION)

    def _create_density_grid(self, data: pd.DataFrame) -> np.ndarray:
        counts, _, _ = np.histogram2d(
            data["latitude"],
            data["longitude"],
            bins=[self.y_grid, self.x_grid],
        )

        return counts / self.cell_area_km2

    def _calculate_timeframe_density(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._create_density_grid(data)

    def _plot_frame(self, ax: plt.Axes, data: pd.DataFrame) -> None:
        counts = self._create_density_grid(data)

        ax.pcolormesh(
            self.x_mesh,
            self.y_mesh,
            counts,
            shading="auto",
            cmap=self.cmap,
            norm=self.norm,
            alpha=self.ALPHA,
            transform=ccrs.PlateCarree(),
        )

    def _add_colorbar(self, cbar_ax: plt.Axes) -> None:
        fig = cbar_ax.figure
        fig.colorbar(
            self.scalar_mappable, cax=cbar_ax, label="Events per km² (log scale)"
        )
