import cartopy.crs as ccrs
import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely import wkt

from src.map_animation_base import MapAnimationBase


class ChoroplethMapAnimation(MapAnimationBase):
    """Class to create Zip code-based Choropleth map animations"""

    COLORMAP: str = "viridis"
    ALPHA: float = 0.8

    def __init__(
        self,
        df: pd.DataFrame,
        shapefile_path: str,
        date_field: str,
        label: str,
        output_path: str = "./output/",
    ) -> None:
        if not shapefile_path:
            raise ValueError("shapefile_path is required")

        self.gdf = self._load_shapefile(shapefile_path)
        self._bounds = None

        super().__init__(
            df,
            date_field=date_field,
            label=label,
            output_path=output_path,
        )

    def _load_shapefile(self, path: str) -> gpd.GeoDataFrame:
        try:
            shape_df = pd.read_csv(path)
            if "the_geom" not in shape_df.columns:
                raise ValueError("Shapefile must contain 'the_geom' column")
            if "MODZCTA" not in shape_df.columns:
                raise ValueError("Shapefile must contain 'MODZCTA' column")
            if "pop_est" not in shape_df.columns:
                raise ValueError("Shapefile must contain 'pop_est' column")

            shape_df["geometry"] = shape_df["the_geom"].apply(wkt.loads)
            return gpd.GeoDataFrame(shape_df, geometry="geometry")
        except Exception as e:
            raise ValueError(f"Failed to load shapefile: {str(e)}") from e

    def _calculate_zipcode_density(self, data: pd.DataFrame) -> pd.Series:
        if not len(data):
            return pd.Series(0, index=self.gdf["MODZCTA"].astype(str))

        density = data.groupby("MODZCTA").size().reset_index(name="count")
        density["MODZCTA"] = density["MODZCTA"].astype(str)

        # Create full data series with zeros for missing ZIP codes
        full_data = pd.Series(0, index=self.gdf["MODZCTA"].astype(str))
        full_data.update(density.set_index("MODZCTA")["count"])

        # Normalize by population
        population = self.gdf.set_index("MODZCTA")["pop_est"].astype(float)
        population.index = population.index.astype(str)
        return (full_data / population) * 10000

    def _calculate_timeframe_density(self, data: pd.DataFrame) -> pd.DataFrame:
        return self._calculate_zipcode_density(data)

    def _plot_frame(self, ax: plt.Axes, data: pd.DataFrame) -> None:
        density = self._calculate_zipcode_density(data)
        patches: list[plt.Polygon] = []
        values: list[float] = []

        for geometry, value in zip(self.gdf.geometry, density, strict=False):
            if hasattr(geometry, "geoms"):
                for poly in geometry.geoms:
                    patches.append(
                        plt.Polygon(np.array(poly.exterior.coords), closed=True)
                    )
                    values.append(value)
            else:
                patches.append(
                    plt.Polygon(np.array(geometry.exterior.coords), closed=True)
                )
                values.append(value)

        collection = mpl.collections.PatchCollection(
            patches,
            cmap=self.cmap,
            alpha=self.ALPHA,
            edgecolor="black",
            linewidth=0.1,
            transform=ccrs.PlateCarree(),
        )

        collection.set_array(np.array(values))
        collection.set_clim(vmin=self.VMIN, vmax=self.VMAX)
        ax.add_collection(collection)

    def _add_colorbar(self, cbar_ax: plt.Axes) -> None:
        fig = cbar_ax.figure
        fig.colorbar(
            self.scalar_mappable,
            cax=cbar_ax,
            label="Events per 10000 Residents (log scale)",
        )
