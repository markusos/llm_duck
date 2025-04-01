from contextlib import suppress

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.animation import FuncAnimation

# Load the Parquet file
parquet_file = "./data/service_requests_2024.parquet"
df = pd.read_parquet(parquet_file)

# Ensure the required columns exist
if not {"longitude", "latitude", "created_date"}.issubset(df.columns):
    raise ValueError(
        "The Parquet file must contain 'longitude', 'latitude', and 'created_date' columns."
    )

# Convert event_date to datetime
df["created_date"] = pd.to_datetime(df["created_date"])

# Extract the hour of the day
df["hour"] = df["created_date"].dt.hour

# Define bin size for grouping nearby events
bin_size = 0.002  # Adjust this value to control the spatial resolution

# Bin longitude and latitude
df["longitude_bin"] = (df["longitude"] // bin_size) * bin_size
df["latitude_bin"] = (df["latitude"] // bin_size) * bin_size

# Group by hour, binned longitude, and latitude to calculate event density
density = (
    df.groupby(["hour", "longitude_bin", "latitude_bin"])
    .size()
    .reset_index(name="count")
)

# Pivot the data to create a 3D grid for the heatmap (hour x latitude x longitude)
heatmap_data = {
    hour: density[density["hour"] == hour].pivot(
        index="latitude_bin", columns="longitude_bin", values="count"
    )
    for hour in range(24)
}

# Apply logarithmic scaling to each hour's heatmap
heatmap_data_log = {hour: np.log1p(data) for hour, data in heatmap_data.items()}

# Calculate global min and max for the heatmap data
global_min = np.nanmin([data.min().min() for data in heatmap_data_log.values()])
global_max = np.nanmax([data.max().max() for data in heatmap_data_log.values()])

# Create the animation
fig = plt.figure(figsize=(12, 8))
ax = plt.axes(projection=ccrs.PlateCarree())

# Add map features
ax.add_feature(cfeature.COASTLINE)
ax.add_feature(cfeature.BORDERS, linestyle=":")
ax.add_feature(cfeature.LAND, edgecolor="black")
ax.add_feature(cfeature.OCEAN, facecolor="lightblue")

# Set the map extent
padding = 0.05
ax.set_extent(
    [
        density["longitude_bin"].min() - padding,
        density["longitude_bin"].max() + padding,
        density["latitude_bin"].min() - padding,
        density["latitude_bin"].max() + padding,
    ]
)

# Initialize the heatmap and colorbar
heatmap = None
title = ax.set_title("")

# Add a dedicated axis for the colorbar
cax = fig.add_axes([0.92, 0.25, 0.02, 0.5])  # Adjust position and size as needed

# Render the colorbar once with the global range
dummy_data = np.array([[global_min, global_max]])  # Dummy data for colorbar
heatmap = ax.pcolormesh(
    [0, 1], [0, 1], dummy_data, cmap="viridis", vmin=global_min, vmax=global_max
)
colorbar = plt.colorbar(heatmap, cax=cax, orientation="vertical")


# Custom formatter for the colorbar
def custom_formatter(x, pos):
    value = np.expm1(x)  # Reverse the log(1 + x) transformation
    if value >= 1e6:
        return f"{value / 1e6:.1f}M"
    elif value >= 1e3:
        return f"{value / 1e3:.1f}k"
    else:
        return f"{int(value)}"


colorbar.set_ticks(np.linspace(global_min, global_max, 5))  # Set tick positions
colorbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(custom_formatter))
colorbar.set_label("Event Count", fontsize=10)
heatmap.remove()  # Remove the dummy heatmap


def update(hour):
    global heatmap
    if heatmap is not None:
        with suppress(ValueError):
            heatmap.remove()  # Remove the previous heatmap

    data = heatmap_data_log[hour]
    lon_bins = data.columns.values
    lat_bins = data.index.values
    heatmap = ax.pcolormesh(
        lon_bins,
        lat_bins,
        data.values,
        cmap="viridis",
        shading="auto",
        alpha=0.8,
        transform=ccrs.PlateCarree(),
        vmin=global_min,  # Use global min
        vmax=global_max,  # Use global max
    )
    title.set_text(f"Event Density Heatmap (Hour: {hour:02d})")

    return heatmap, title


# Create the animation
anim = FuncAnimation(fig, update, frames=range(24), interval=500, blit=False)

# Save and display the animation
anim.save("./output/events_per_hour_2024.gif", writer="pillow")
plt.show()
