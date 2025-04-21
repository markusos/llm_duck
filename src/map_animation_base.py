from abc import ABC, abstractmethod

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation


class MapAnimationBase(ABC):
    """Abstract base class for map-based animations"""

    MAP_PADDING: float = 0.05
    ANIMATION_INTERVAL: int = 500
    ANIMATION_FPS: int = 2
    ANIMATION_DPI: int = 150

    def __init__(
        self,
        df: pd.DataFrame,
        date_field: str,
        label: str,
        output_path: str = "./output/",
    ) -> None:
        if not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a pandas DataFrame")
        if not date_field:
            raise ValueError("date_field is required")
        if not label:
            raise ValueError("category_name is required")

        self._validate_dataframe(df)
        self.df = df
        self.label = label
        self.output_path = output_path

        self.date_field = date_field
        self._setup_bounds()

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        required_columns = ["latitude", "longitude"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

    def _setup_bounds(self) -> None:
        bounds = (
            self.df["longitude"].min(),
            self.df["longitude"].max(),
            self.df["latitude"].min(),
            self.df["latitude"].max(),
        )
        self._bounds = self._add_padding_to_bounds(bounds)

    def update(self, timeframe: int, ax: plt.Axes) -> None:
        ax.clear()
        bounds = self._get_bounds()
        ax.set_extent(bounds)

        timeframe_data = self._get_timeframe_data(timeframe)
        if len(timeframe_data) > 1:
            self._plot_frame(ax, timeframe_data)

        self._add_map_features(ax)
        ax.set_title(self._format_title(len(timeframe_data), timeframe))

    def _get_bounds(self) -> list[float]:
        return list(self._bounds)

    def _add_padding_to_bounds(
        self, bounds: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        """Add padding to map bounds"""
        min_lon, max_lon, min_lat, max_lat = bounds
        padding = self.MAP_PADDING
        return (
            min_lon - padding,
            max_lon + padding,
            min_lat - padding,
            max_lat + padding,
        )

    def _add_map_features(self, ax: plt.Axes) -> None:
        ax.add_feature(cfeature.COASTLINE, zorder=2)
        ax.add_feature(cfeature.BORDERS, linestyle=":", zorder=2)
        ax.add_feature(cfeature.LAND, edgecolor="black", alpha=0.3, zorder=1)
        ax.add_feature(cfeature.OCEAN, facecolor="lightblue", alpha=0.3, zorder=1)

    def _format_title(self, event_count: int, timeframe: int) -> str:
        return f"{self.label} - {event_count:,} Events ({self.date_field.capitalize()}: {timeframe:02d})"

    def _get_timeframe_data(self, timeframe: int) -> pd.DataFrame:
        return self.df[(self.df[self.date_field] == timeframe)]

    @abstractmethod
    def _plot_frame(self, ax: plt.Axes, data: pd.DataFrame) -> None:
        """Plot single animation frame"""
        pass

    @abstractmethod
    def _calculate_timeframe_density(self, data: pd.DataFrame) -> float:
        """Calculate density for a single timeframe"""
        pass

    def create_animation(self) -> None:
        frames = self._get_frames()
        fig = plt.figure(figsize=(12, 8))

        # Create separate axes for map and colorbar
        map_ax = plt.axes([0.1, 0.1, 0.75, 0.8], projection=ccrs.PlateCarree())
        colorbar_ax = fig.add_axes([0.85, 0.1, 0.02, 0.8])

        self._setup_visualization()
        self._add_colorbar(colorbar_ax)  # Pass the colorbar axes

        anim = FuncAnimation(
            fig,
            lambda timeframe: self.update(timeframe, map_ax),
            frames=frames,
            interval=self.ANIMATION_INTERVAL,
            blit=False,
        )

        self._save_animation(anim)
        plt.close(fig)

    def _get_frames(self) -> range:
        match self.date_field:
            case "hour":
                return range(24)
            case "month":
                return range(1, 13)
            case _:
                raise ValueError("date_field must be 'hour' or 'month'")

    def _setup_visualization(self) -> None:
        timeframes = self._get_frames()
        all_densities = []

        # Collect densities from all cells in all frames
        for frame in timeframes:
            data = self._get_timeframe_data(frame)
            cell_densities = self._calculate_timeframe_density(data)
            all_densities.extend(cell_densities[cell_densities > 0])

        all_densities = np.array(all_densities)
        self.VMIN = 10 ** np.floor(np.log10(np.percentile(all_densities, 5)))
        self.VMAX = 10 ** np.ceil(np.log10(np.percentile(all_densities, 95)))

        self.norm = mpl.colors.LogNorm(vmin=self.VMIN, vmax=self.VMAX)
        self.cmap = plt.cm.get_cmap(self.COLORMAP)

        self.scalar_mappable = plt.cm.ScalarMappable(norm=self.norm, cmap=self.cmap)
        self.scalar_mappable.set_array([])

    @abstractmethod
    def _add_colorbar(self, ax: plt.Axes) -> None:
        """Add colorbar to plot"""
        pass

    def _save_animation(self, anim: FuncAnimation) -> None:
        label_filename = self.label.lower().replace("/", "_").replace(" ", "_")

        filename = f"./{self.output_path}/{label_filename}.gif"
        anim.save(
            filename, writer="pillow", fps=self.ANIMATION_FPS, dpi=self.ANIMATION_DPI
        )
