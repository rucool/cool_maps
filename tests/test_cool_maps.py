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


def test_pad_extent_float():
    from cool_maps.calc import pad_extent

    assert pad_extent(extent, 0.25) == pytest.approx((-99.25, -78.75, 17.75, 31.25))


def test_pad_extent_lon_lat_pair():
    from cool_maps.calc import pad_extent

    assert pad_extent(extent, (1, 0.5)) == pytest.approx((-100.0, -78.0, 17.5, 31.5))


def test_pad_extent_zero_is_noop():
    from cool_maps.calc import pad_extent

    assert pad_extent(extent, 0) == pytest.approx(tuple(float(x) for x in extent))


def test_pad_extent_invalid_length_raises():
    from cool_maps.calc import pad_extent

    with pytest.raises(ValueError):
        pad_extent(extent, (1, 2, 3))


@pytest.mark.skipif("cartopy" not in cplt.available_engines(), reason="Cartopy engine not available")
def test_create_default_padding_expands_extent():
    ccrs = pytest.importorskip("cartopy.crs")
    fig, ax = cplt.create(extent=extent, ticks=False, gridlines=False, bathymetry=False)
    try:
        x0, x1, y0, y1 = ax.get_extent(crs=ccrs.PlateCarree())
        assert (x0, x1, y0, y1) == pytest.approx(
            (extent[0] - 0.25, extent[1] + 0.25, extent[2] - 0.25, extent[3] + 0.25), abs=1e-6
        )
    finally:
        plt.close(fig)


@pytest.mark.skipif("cartopy" not in cplt.available_engines(), reason="Cartopy engine not available")
def test_create_padding_zero_matches_extent_exactly():
    ccrs = pytest.importorskip("cartopy.crs")
    fig, ax = cplt.create(extent=extent, padding=0, ticks=False, gridlines=False, bathymetry=False)
    try:
        x0, x1, y0, y1 = ax.get_extent(crs=ccrs.PlateCarree())
        assert (x0, x1, y0, y1) == pytest.approx(tuple(float(x) for x in extent), abs=1e-6)
    finally:
        plt.close(fig)


@pytest.mark.skipif("cartopy" not in cplt.available_engines(), reason="Cartopy engine not available")
def test_create_padding_lon_lat_pair():
    ccrs = pytest.importorskip("cartopy.crs")
    fig, ax = cplt.create(extent=extent, padding=(1, 0.5), ticks=False, gridlines=False, bathymetry=False)
    try:
        x0, x1, y0, y1 = ax.get_extent(crs=ccrs.PlateCarree())
        assert (x0, x1, y0, y1) == pytest.approx(
            (extent[0] - 1, extent[1] + 1, extent[2] - 0.5, extent[3] + 0.5), abs=1e-6
        )
    finally:
        plt.close(fig)


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


def test_map_create_bathymetry_banded_legend_defaults_to_metric():
    # banded's legend should default to meters only (no fathoms), unlike shadedcontour's
    # "both" default -- distinct per-method defaults for the same legend_scale= parameter.
    fig, ax = cplt.create(extent=extent, bathymetry=True, bathymetry_method="banded", ticks=False)
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert labels and all("fth" not in label for label in labels)


def test_map_create_bathymetry_banded_legend_scale_override():
    fig, ax = cplt.create(
        extent=extent, bathymetry=True, bathymetry_method="banded", ticks=False,
        bathymetry_legend_scale="both",
    )
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert labels and all("fth" in label for label in labels)


def test_banded_fill_zorder_stays_below_land_lines_above():
    # Regression test: the banded fill (contourf) must sit below land (add_features draws
    # land at zorder+10, default zorder=0), so a mismatch between the GEBCO bathymetry grid
    # and cartopy's separately-sourced coastline vector doesn't leave stray fill visible
    # over land. The isobath lines (contour) must stay above land so they render crisply,
    # matching the plain "contour" method's behavior.
    fig, ax = cplt.create(extent=extent, bathymetry=True, bathymetry_method="banded", ticks=False)
    try:
        # Cartopy wraps these as GeoContourSet, basemap/plain matplotlib as QuadContourSet;
        # both live in ax.collections rather than ax.get_children() under cartopy.
        contour_sets = [c for c in ax.collections if "ContourSet" in type(c).__name__]
        assert len(contour_sets) == 2  # one contourf (fill), one contour (isobath lines)
        zorders = sorted(c.get_zorder() for c in contour_sets)
        assert zorders[0] < 10, "banded fill must be drawn below land"
        assert zorders[1] > 10, "banded isobath lines must be drawn above land"
    finally:
        plt.close(fig)


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


def test_add_legend_preserves_previous_legend():
    import matplotlib.legend

    fig, ax = cplt.create(extent=extent, bathymetry=True, bathymetry_method="banded", ticks=False)
    try:
        first_legend = ax.get_legend()
        assert first_legend is not None

        sc = ax.scatter([-90.0], [25.0], label="point")
        second_legend = cplt.add_legend(ax, handles=[sc], loc="upper left")

        legends = [c for c in ax.get_children() if isinstance(c, matplotlib.legend.Legend)]
        assert len(legends) == 2
        assert first_legend in legends
        assert second_legend in legends
    finally:
        plt.close(fig)


def test_add_legend_unclips_preserved_legend():
    # Regression test: ax.add_artist() clips any artist without an existing clip path to
    # the axes' rectangular patch, which would make the banded/shadedcontour legend (drawn
    # below the axes via bbox_to_anchor) invisible when preserved naively. add_legend()
    # must undo that.
    fig, ax = cplt.create(extent=extent, bathymetry=True, bathymetry_method="banded", ticks=False)
    try:
        first_legend = ax.get_legend()
        sc = ax.scatter([-90.0], [25.0], label="point")
        cplt.add_legend(ax, handles=[sc], loc="upper left")
        assert first_legend.get_clip_on() is False
    finally:
        plt.close(fig)


def test_add_legend_with_no_existing_legend():
    fig, ax = cplt.create(extent=extent, bathymetry=False, ticks=False)
    try:
        sc = ax.scatter([-90.0], [25.0], label="point")
        legend = cplt.add_legend(ax, handles=[sc], loc="upper left")
        assert legend is ax.get_legend()
    finally:
        plt.close(fig)
