from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest

import cool_maps.plot as cplt

output_path = (Path(__file__).parent.with_name("output")).resolve()

# Gulf of Mexico extent
extent = [-99, -79, 18, 31]


@pytest.fixture(autouse=True)
def _use_cartopy_engine():
    cplt.set_engine("cartopy")
    yield
    cplt.set_engine("cartopy")

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


def test_set_engine_invalid():
    with pytest.raises(ValueError):
        cplt.set_engine("not-real")


@pytest.mark.skipif("basemap" not in cplt.available_engines(), reason="Basemap engine not available")
def test_map_create_basemap_engine():
    cplt.set_engine("basemap")
    try:
        cplt.create(extent=extent, ticks=False, gridlines=False, bathymetry=False)
    finally:
        cplt.set_engine("cartopy")


@pytest.mark.skipif("basemap" not in cplt.available_engines(), reason="Basemap engine not available")
def test_basemap_accepts_cartopy_crs():
    ccrs = pytest.importorskip("cartopy.crs")
    cplt.set_engine("basemap")
    try:
        cplt.create(extent=extent, proj=ccrs.PlateCarree(), ticks=False, gridlines=False, bathymetry=False)
    finally:
        cplt.set_engine("cartopy")


@pytest.mark.skipif("basemap" not in cplt.available_engines(), reason="Basemap engine not available")
def test_basemap_projection_string():
    cplt.set_engine("basemap")
    try:
        cplt.create(extent=extent, proj="mercator", ticks=False, gridlines=False, bathymetry=False)
    finally:
        cplt.set_engine("cartopy")


@pytest.mark.skipif("basemap" not in cplt.available_engines(), reason="Basemap engine not available")
def test_basemap_projection_unknown():
    cplt.set_engine("basemap")
    try:
        with pytest.raises(TypeError):
            cplt.create(extent=extent, proj="definitely-not-real", ticks=False, gridlines=False, bathymetry=False)
    finally:
        cplt.set_engine("cartopy")


@pytest.mark.skipif("cartopy" not in cplt.available_engines(), reason="Cartopy engine not available")
def test_cartopy_projection_string():
    ccrs = pytest.importorskip("cartopy.crs")
    cplt.set_engine("cartopy")
    fig = None
    try:
        fig, ax = cplt.create(extent=extent, proj="orthographic", ticks=False, gridlines=False, bathymetry=False)
    finally:
        cplt.set_engine("cartopy")
        if fig:
            plt.close(fig)


@pytest.mark.skipif("cartopy" not in cplt.available_engines(), reason="Cartopy engine not available")
def test_add_ticks_accepts_string_projection():
    ccrs = pytest.importorskip("cartopy.crs")
    cplt.set_engine("cartopy")
    extent = [-99, -79, 18, 31]
    fig = None
    try:
        fig, ax = plt.subplots(subplot_kw=dict(projection=ccrs.Mercator()))
        cplt.add_ticks(ax, extent, proj="platecarree", engine="cartopy")
    finally:
        cplt.set_engine("cartopy")
        if fig:
            plt.close(fig)


@pytest.mark.skipif("cartopy" not in cplt.available_engines(), reason="Cartopy engine not available")
def test_add_bathymetry_accepts_string_transform():
    ccrs = pytest.importorskip("cartopy.crs")
    cplt.set_engine("cartopy")
    lon = np.linspace(-75, -74, 5)
    lat = np.linspace(39, 40, 5)
    elevation = np.tile(np.linspace(-1000, -100, lon.size), (lat.size, 1))
    fig = None
    try:
        fig, ax = plt.subplots(subplot_kw=dict(projection=ccrs.Mercator()))
        cplt.add_bathymetry(ax, lon, lat, elevation, transform="platecarree", engine="cartopy")
    finally:
        cplt.set_engine("cartopy")
        if fig:
            plt.close(fig)


def test_map_create_bathymetry_shadedcontour():
    cplt.create(extent=extent, bathymetry=True, bathymetry_method="shadedcontour")
    cplt.export_fig(output_path, "map_bathymetry_shadedcontour")


@pytest.mark.skipif("basemap" not in cplt.available_engines(), reason="Basemap engine not available")
def test_map_create_bathymetry_shadedcontour_basemap():
    cplt.set_engine("basemap")
    try:
        cplt.create(
            extent=extent, bathymetry=True, bathymetry_method="shadedcontour", ticks=False, gridlines=False
        )
    finally:
        cplt.set_engine("cartopy")


_BANDED_COLORS = ["cornflowerblue", "lightblue", "lightsteelblue"]


def test_map_create_bathymetry_banded():
    cplt.create(
        extent=extent,
        bathymetry=True,
        bathymetry_method="banded",
        isobaths=(-1000, -100),
        bathymetry_colors=_BANDED_COLORS,
    )
    cplt.export_fig(output_path, "map_bathymetry_banded")


def test_map_create_bathymetry_banded_default_colors():
    # create()'s own defaults (isobaths=(-1000, -100)) produce exactly 3 bands, so
    # bathymetry_method="banded" should work with no bathymetry_colors= at all.
    cplt.create(extent=extent, bathymetry=True, bathymetry_method="banded")
    cplt.export_fig(output_path, "map_bathymetry_banded_default_colors")


@pytest.mark.skipif("basemap" not in cplt.available_engines(), reason="Basemap engine not available")
def test_map_create_bathymetry_banded_basemap():
    # Regression test: this method combines add_bathymetry's contour + contourf/quiver-style
    # backend primitives, which call basemap_obj.<method>(...) directly. Basemap's own
    # implementation of those methods calls back into `ax.<method>(...)`, which the
    # escape-hatch machinery in create() also overrides -- without the _call_basemap_method
    # guard, that inner call re-enters the override and double-projects already-projected
    # coordinates, silently collapsing the contour/fill to a near-empty degenerate result.
    cplt.set_engine("basemap")
    try:
        fig, ax = cplt.create(
            extent=extent,
            bathymetry=True,
            bathymetry_method="banded",
            isobaths=(-1000, -100),
            bathymetry_colors=_BANDED_COLORS,
            ticks=False,
            gridlines=False,
        )
    finally:
        cplt.set_engine("cartopy")


def test_add_bathymetry_banded_default_colors():
    # levels=(-1000, -100) is the common 2-level/3-band case, which has a built-in default
    # (middle band = cfeature.COLORS['water']) -- no colors= needed.
    import cartopy.feature as cfeature

    lon = np.linspace(-75, -74, 5)
    lat = np.linspace(39, 40, 5)
    # min elevation must fall strictly below the shallowest level (-1000) for banded's edges
    elevation = np.tile(np.linspace(-2000, -50, lon.size), (lat.size, 1))
    fig, ax = cplt.create(extent=extent, features=False, ticks=False, bathymetry=False)
    try:
        cplt.add_bathymetry(ax, lon, lat, elevation, levels=(-1000, -100), method="banded")
        colors = cplt._default_banded_colors(3)
        assert np.array_equal(np.asarray(colors[1]), np.asarray(cfeature.COLORS["water"]))
    finally:
        plt.close(fig)


def test_add_bathymetry_banded_requires_colors_without_default():
    # A band count other than 3 (here: a single level -> 2 bands) has no built-in default.
    lon = np.linspace(-75, -74, 5)
    lat = np.linspace(39, 40, 5)
    elevation = np.tile(np.linspace(-1000, -100, lon.size), (lat.size, 1))
    fig, ax = cplt.create(extent=extent, features=False, ticks=False, bathymetry=False)
    try:
        with pytest.raises(ValueError):
            cplt.add_bathymetry(ax, lon, lat, elevation, levels=(-1000,), method="banded")
    finally:
        plt.close(fig)


def test_add_bathymetry_banded_wrong_color_count():
    lon = np.linspace(-75, -74, 5)
    lat = np.linspace(39, 40, 5)
    # min elevation must fall strictly below the shallowest level (-1000) for banded's edges
    elevation = np.tile(np.linspace(-2000, -50, lon.size), (lat.size, 1))
    fig, ax = cplt.create(extent=extent, features=False, ticks=False, bathymetry=False)
    try:
        with pytest.raises(ValueError, match="colors must have"):
            cplt.add_bathymetry(
                ax, lon, lat, elevation, levels=(-1000, -100), method="banded", colors=["red"]
            )
    finally:
        plt.close(fig)


@pytest.mark.skipif("basemap" not in cplt.available_engines(), reason="Basemap engine not available")
def test_basemap_contour_bathymetry_produces_real_segments():
    # Regression test for the same double-projection bug as
    # test_map_create_bathymetry_banded_basemap, exercised via the plain "contour" method
    # (the pre-existing default), asserting on actual segment counts rather than just "no
    # exception" -- the bug produced a valid-looking but visually empty/degenerate contour.
    from cool_maps.download import get_bathymetry

    bathy = get_bathymetry(extent)
    cplt.set_engine("basemap")
    try:
        fig, ax = cplt.create(extent=extent, bathymetry=False, ticks=False, gridlines=False)
        h = cplt.add_bathymetry(
            ax, bathy["longitude"].data, bathy["latitude"].data, bathy["z"].data, levels=(-1000, -100)
        )
        assert all(len(segs) > 10 for segs in h.allsegs)
    finally:
        cplt.set_engine("cartopy")


@pytest.mark.skipif("basemap" not in cplt.available_engines(), reason="Basemap engine not available")
def test_engine_inferred_from_axes_created_with_basemap():
    # Global engine stays "cartopy" (autouse fixture), but this axes is explicitly
    # created with the basemap engine -- add_features() must infer "basemap" from
    # the axes rather than falling back to the global default.
    fig = None
    try:
        fig, ax = cplt.create(extent=extent, engine="basemap", ticks=False, gridlines=False, bathymetry=False)
        assert getattr(ax, "_cool_maps_engine") == "basemap"
        assert cplt.get_engine() == "cartopy"
        cplt.add_features(ax)  # no engine= kwarg
    finally:
        if fig:
            plt.close(fig)


@pytest.mark.skipif("cartopy" not in cplt.available_engines(), reason="Cartopy engine not available")
def test_cartopy_escape_hatch_scatter_without_transform():
    fig = None
    try:
        fig, ax = cplt.create(extent=extent, engine="cartopy", ticks=False, gridlines=False, bathymetry=False)
        lon = np.array([-90.0, -85.0, -82.0])
        lat = np.array([22.0, 25.0, 28.0])
        sc = ax.scatter(lon, lat)  # no transform= passed
        assert sc is not None
    finally:
        if fig:
            plt.close(fig)


@pytest.mark.skipif("basemap" not in cplt.available_engines(), reason="Basemap engine not available")
def test_basemap_escape_hatch_scatter_without_latlon():
    fig = None
    try:
        fig, ax = cplt.create(extent=extent, engine="basemap", ticks=False, gridlines=False, bathymetry=False)
        lon = np.array([-90.0, -85.0, -82.0])
        lat = np.array([22.0, 25.0, 28.0])
        sc = ax.scatter(lon, lat)  # no latlon=True passed
        assert sc is not None
    finally:
        if fig:
            plt.close(fig)


def test_escape_hatch_does_not_leak_to_bare_axes():
    # An axes never passed through create() must behave like plain matplotlib --
    # proves the escape-hatch overrides are opt-in via create(), not a global patch.
    fig, ax = plt.subplots()
    try:
        assert not hasattr(ax, "_cool_maps_engine")
        sc = ax.scatter([1, 2, 3], [1, 2, 3])
        assert sc is not None
    finally:
        plt.close(fig)


@pytest.mark.skipif("cartopy" not in cplt.available_engines(), reason="Cartopy engine not available")
def test_cartopy_escape_hatch_double_bind_safety():
    fig = None
    try:
        fig, ax = cplt.create(extent=extent, engine="cartopy", ticks=False, gridlines=False, bathymetry=False)
        cplt.create(
            ax=ax, extent=extent, engine="cartopy", ticks=False, gridlines=False, bathymetry=False, features=False
        )
        lon = np.array([-90.0, -85.0])
        lat = np.array([22.0, 25.0])
        sc = ax.scatter(lon, lat)  # must not recurse or double-inject kwargs
        assert sc is not None
    finally:
        if fig:
            plt.close(fig)


@pytest.mark.skipif("basemap" not in cplt.available_engines(), reason="Basemap engine not available")
def test_basemap_escape_hatch_double_bind_safety():
    fig = None
    try:
        fig, ax = cplt.create(extent=extent, engine="basemap", ticks=False, gridlines=False, bathymetry=False)
        cplt.create(
            ax=ax, extent=extent, engine="basemap", ticks=False, gridlines=False, bathymetry=False, features=False
        )
        lon = np.array([-90.0, -85.0])
        lat = np.array([22.0, 25.0])
        sc = ax.scatter(lon, lat)  # must not recurse or double-inject kwargs
        assert sc is not None
    finally:
        if fig:
            plt.close(fig)
