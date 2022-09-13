from pathlib import Path
import cool_maps.plot as cplt

output_path = (Path(__file__).parent.with_name("output")).resolve()

# Gulf of Mexico extent
extent = [-99, -79, 18, 31]

def test_map_create():
    cplt.create(extent=extent)
    cplt.export_fig(output_path, "map_default")

def test_map_create_bathymetry():
    cplt.create(extent=extent, bathymetry=True)
    cplt.export_fig(output_path, "map_bathymetry")

# def test_map_create_pickle():
#     fig, _ = cplt.create(extent=extent)
#     cplt.save_fig(fig, output_path, "map_default.pkl")

# def test_map_load_pickle():
#     import cartopy.crs as ccrs
#     fig, ax = cplt.load_fig(output_path / "map_default.pkl")
#     ax.plot(-87, 26, 'ro', markersize=12, transform=ccrs.PlateCarree())
#     cplt.export_fig(output_path, "map_pickle_loaded")