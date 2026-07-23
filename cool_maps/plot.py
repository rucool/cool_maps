# Import from standard Python libraries
import os
import pickle
import warnings
from pathlib import Path

# Imports from required packages
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from oceans.ocfis import spdir2uv, uv2spdir
import cmocean as cmo

# Imports from cool_maps
from cool_maps.calc import calculate_ticks, dd2dms, fmt, calculate_colorbar_ticks, pad_extent
from cool_maps.download import get_bathymetry, get_glider_bathymetry

# Optional mapping engines
try:
    import cartopy.crs as _cartopy_crs
    import cartopy.feature as _cartopy_feature
except ImportError:  # pragma: no cover - optional dependency
    _cartopy_crs = None
    _cartopy_feature = None

try:
    from mpl_toolkits.basemap import Basemap as _Basemap
except ImportError:  # pragma: no cover - optional dependency
    _Basemap = None


# Suppressing warnings for a "pretty output."
warnings.simplefilter("ignore")

_SUPPORTED_ENGINES = ("cartopy", "basemap")
_ENGINE_ATTR = "_cool_maps_engine"
_BASEMAP_ATTR = "_cool_maps_basemap"
_EXTENT_ATTR = "_cool_maps_extent"


def _get_cartopy_modules():
    if _cartopy_crs is None or _cartopy_feature is None:
        raise ImportError(
            "cartopy is required for the 'cartopy' mapping engine. Install cartopy to use this engine."
        )
    return _cartopy_crs, _cartopy_feature


def _get_basemap_class():
    if _Basemap is None:
        raise ImportError(
            "mpl_toolkits.basemap is required for the 'basemap' mapping engine. Install basemap to use this engine."
        )
    return _Basemap


def _validate_engine(name: str) -> None:
    if name not in _SUPPORTED_ENGINES:
        raise ValueError(
            f"Unknown mapping engine '{name}'. Supported engines are: {', '.join(_SUPPORTED_ENGINES)}."
        )
    if name == "cartopy":
        _get_cartopy_modules()
    else:
        _get_basemap_class()


def _initialize_engine() -> str:
    env_value = os.environ.get("COOL_MAPS_ENGINE")
    if env_value:
        candidate = env_value.lower()
        try:
            _validate_engine(candidate)
        except ImportError as exc:
            raise ImportError(
                "The mapping engine requested via the COOL_MAPS_ENGINE environment variable is not available. "
                "Install the required dependency or choose a different engine."
            ) from exc
        except ValueError as exc:
            raise ValueError(
                f"Unknown mapping engine '{candidate}' requested via the COOL_MAPS_ENGINE environment variable. "
                f"Choose from {', '.join(_SUPPORTED_ENGINES)}."
            ) from exc
        return candidate

    for candidate in ("cartopy", "basemap"):
        try:
            _validate_engine(candidate)
            return candidate
        except ImportError:
            continue

    raise ImportError(
        "cool_maps requires at least one mapping engine (cartopy or basemap). "
        "Install one of these packages to continue."
    )


_ENGINE_NAME = _initialize_engine()


_proj_defaults_cache: dict = {}


def _proj_defaults(key: str):
    """Return the default Cartopy projection for 'map' (Mercator) or 'data' (PlateCarree)."""
    if key not in _proj_defaults_cache:
        ccrs, _ = _get_cartopy_modules()
        _proj_defaults_cache["map"] = ccrs.Mercator()
        _proj_defaults_cache["data"] = ccrs.PlateCarree()
    return _proj_defaults_cache[key]


# Backward-compatible subscript shim so existing code using proj["map"] / proj["data"] still works
class _ProjDefaultsShim:
    def __getitem__(self, key):
        return _proj_defaults(key)


proj = _ProjDefaultsShim()


def available_engines():
    """Return the mapping engines that are currently importable."""

    engines = []
    if _cartopy_crs is not None and _cartopy_feature is not None:
        engines.append("cartopy")
    if _Basemap is not None:
        engines.append("basemap")
    return tuple(engines)


def get_engine():
    """Return the active mapping engine name."""

    return _ENGINE_NAME


def set_engine(name):
    """Set the active mapping engine."""

    global _ENGINE_NAME
    normalized = name.lower()
    _validate_engine(normalized)
    _ENGINE_NAME = normalized


def _get_engine_name(engine=None, ax=None):
    """
    Resolve which engine to use: an explicit `engine` argument always wins; otherwise,
    if `ax` was produced by cool_maps.plot.create(), use the engine it was flagged
    with; otherwise fall back to the active global engine.
    """
    if engine is not None:
        normalized = engine.lower()
        _validate_engine(normalized)
        return normalized
    if ax is not None:
        stashed = getattr(ax, _ENGINE_ATTR, None)
        if stashed is not None:
            return stashed
    return _ENGINE_NAME


def _flag_axes(ax, engine_name, extent=None, basemap_obj=None):
    """Store engine metadata on the matplotlib axes."""

    if ax is None:
        return
    setattr(ax, _ENGINE_ATTR, engine_name)
    if extent is not None:
        setattr(ax, _EXTENT_ATTR, tuple(float(x) for x in extent))
    if basemap_obj is not None:
        setattr(ax, _BASEMAP_ATTR, basemap_obj)
    elif hasattr(ax, _BASEMAP_ATTR):
        delattr(ax, _BASEMAP_ATTR)


def _resolve_basemap(ax):
    """Return a (Basemap, matplotlib.axes.Axes) tuple for basemap-enabled axes."""

    if hasattr(ax, "is_latlong") and hasattr(ax, "ax"):
        basemap_obj = ax
        mpl_ax = ax.ax
        if mpl_ax is None:
            raise ValueError("Provided Basemap instance does not have an associated Matplotlib axis.")
        return basemap_obj, mpl_ax

    basemap_obj = getattr(ax, _BASEMAP_ATTR, None)
    if basemap_obj is None:
        raise ValueError(
            "Basemap engine requires axes created with cool_maps.plot.create(..., engine='basemap') "
            "or passing a Basemap instance."
        )
    mpl_ax = basemap_obj.ax if basemap_obj.ax is not None else ax
    return basemap_obj, mpl_ax


def _coast_to_basemap_resolution(coast):
    mapping = {
        "full": "f",
        "high": "h",
        "mid": "i",
        "low": "l",
        "crude": "c",
    }
    return mapping.get(coast, "i")


def _cartopy_crs_to_basemap_kwargs(crs_obj):
    """
    Translate a Cartopy CRS instance into a Basemap keyword dictionary.

    Args:
        crs_obj (cartopy.crs.CRS): Cartopy CRS to translate.

    Returns:
        dict: Basemap keyword arguments.

    Raises:
        TypeError: If the CRS cannot be converted to a Basemap projection.
    """

    if _cartopy_crs is None:
        raise TypeError("Cartopy is not available to translate CRS definitions.")

    if not isinstance(crs_obj, _cartopy_crs.CRS):
        raise TypeError(
            "Expected a Cartopy CRS instance when translating projections for Basemap."
        )

    params = getattr(crs_obj, "proj4_params", None)
    if params is None:
        raise TypeError(
            "Unable to translate the provided Cartopy CRS to a Basemap projection."
        )

    proj_name = params.get("proj")
    projection_lookup = {
        "longlat": "cyl",
        "eqc": "cyl",
        "merc": "merc",
        "mill": "mill",
        "lcc": "lcc",
        "aea": "aea",
        "aeqd": "aeqd",
        "laea": "laea",
        "ortho": "ortho",
        "stere": "stere",
        "gnom": "gnom",
        "sinu": "sinu",
        "hammer": "hammer",
        "moll": "moll",
        "robin": "robin",
        "poly": "poly",
        "cass": "cass",
        "eck4": "eck4",
        "eck6": "eck6",
        "eqdc": "eqdc",
    }

    basemap_projection = projection_lookup.get(proj_name)
    if basemap_projection is None:
        raise TypeError(
            f"Cartopy CRS '{proj_name}' cannot be automatically translated to a Basemap projection. "
            "Pass a Basemap projection name or keyword dictionary instead."
        )

    numeric_keys = {
        "lon_0",
        "lat_0",
        "lat_1",
        "lat_2",
        "lat_ts",
        "k_0",
        "lon_1",
        "lon_2",
    }

    def _convert_value(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return value

    kwargs = {"projection": basemap_projection}
    for key in numeric_keys:
        if key in params:
            kwargs[key] = _convert_value(params[key])

    if basemap_projection in {"lcc", "aeqd", "aea"}:
        kwargs.setdefault("lat_0", _convert_value(params.get("lat_0", 0)))
        kwargs.setdefault("lon_0", _convert_value(params.get("lon_0", 0)))

    if basemap_projection == "stere":
        lat_0 = params.get("lat_0", None)
        if lat_0 is None:
            lat_ts = params.get("lat_ts", 90.0)
            kwargs.setdefault("lat_0", _convert_value(lat_ts))
        else:
            kwargs.setdefault("lat_0", _convert_value(lat_0))
        kwargs.setdefault("lon_0", _convert_value(params.get("lon_0", 0)))

    return kwargs


def _normalize_proj_name(value):
    if not isinstance(value, str):
        raise TypeError("Projection identifiers must be strings.")
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _extent_center(extent):
    lon0 = float(np.mean(extent[:2]))
    lat0 = float(np.mean(extent[2:]))
    return lon0, lat0


def _standard_parallels(extent):
    lat_min, lat_max = float(extent[2]), float(extent[3])
    span = abs(lat_max - lat_min)
    if span < 1e-6:
        span = 2.0
        lat_min = np.clip(lat_min - 1.0, -89.0, 89.0)
        lat_max = np.clip(lat_max + 1.0, -89.0, 89.0)
    elif span < 2.0:
        pad = (2.0 - span) / 2.0
        lat_min = np.clip(lat_min - pad, -89.0, 89.0)
        lat_max = np.clip(lat_max + pad, -89.0, 89.0)
    lat1 = lat_min + (lat_max - lat_min) / 3.0
    lat2 = lat_max - (lat_max - lat_min) / 3.0
    if np.isclose(lat1, lat2):
        lat1 = np.clip(lat1 - 1.0, -89.0, 89.0)
        lat2 = np.clip(lat2 + 1.0, -89.0, 89.0)
    return float(lat1), float(lat2)


def _orthographic_kwargs(extent):
    lon0, lat0 = _extent_center(extent)
    return {"projection": "ortho", "lon_0": float(lon0), "lat_0": float(lat0)}


def _lambert_conformal_kwargs(extent):
    lon0, lat0 = _extent_center(extent)
    lat1, lat2 = _standard_parallels(extent)
    return {
        "projection": "lcc",
        "lon_0": float(lon0),
        "lat_0": float(lat0),
        "lat_1": float(lat1),
        "lat_2": float(lat2),
    }


def _stereographic_kwargs(extent):
    lon0, lat0 = _extent_center(extent)
    lat_ts = float(np.clip(lat0, -89.0, 89.0))
    return {
        "projection": "stere",
        "lon_0": float(lon0),
        "lat_0": float(lat0),
        "lat_ts": lat_ts if abs(lat_ts) > 1e-6 else (90.0 if lat0 >= 0 else -90.0),
    }


def _azimuthal_equidistant_kwargs(extent):
    lon0, lat0 = _extent_center(extent)
    return {"projection": "aeqd", "lon_0": float(lon0), "lat_0": float(lat0)}


_PROJECTION_DEFINITIONS = [
    {
        "name": "platecarree",
        "aliases": {"platecarree", "plate_carree", "cyl", "eqc", "equirectangular", "latlon"},
        "cartopy": lambda ccrs, extent: ccrs.PlateCarree(),
        "basemap": lambda extent: {"projection": "cyl"},
    },
    {
        "name": "mercator",
        "aliases": {"mercator", "merc"},
        "cartopy": lambda ccrs, extent: ccrs.Mercator(),
        "basemap": lambda extent: {"projection": "merc"},
    },
    {
        "name": "lambertcylindrical",
        "aliases": {"lambertcylindrical", "lambert_cylindrical", "lcyl"},
        "cartopy": lambda ccrs, extent: ccrs.LambertCylindrical(),
        "basemap": lambda extent: {"projection": "cea"},  # cylindrical equal-area; closest Basemap equivalent
    },
    {
        "name": "mill",
        "aliases": {"mill", "millercylindrical", "miller"},
        "cartopy": lambda ccrs, extent: ccrs.Miller(),
        "basemap": lambda extent: {"projection": "mill"},
    },
    {
        "name": "orthographic",
        "aliases": {"orthographic", "ortho"},
        "cartopy": lambda ccrs, extent: ccrs.Orthographic(*_extent_center(extent)),
        "basemap": _orthographic_kwargs,
    },
    {
        "name": "lambertconformal",
        "aliases": {"lambertconformal", "lcc"},
        "cartopy": lambda ccrs, extent: ccrs.LambertConformal(
            central_longitude=float(np.mean(extent[:2])),
            central_latitude=float(np.mean(extent[2:])),
            standard_parallels=_standard_parallels(extent),
        ),
        "basemap": _lambert_conformal_kwargs,
    },
    {
        "name": "stereographic",
        "aliases": {"stere", "stereographic"},
        "cartopy": lambda ccrs, extent: ccrs.Stereographic(
            central_longitude=float(np.mean(extent[:2])),
            central_latitude=float(np.mean(extent[2:])),
            true_scale_latitude=float(np.mean(extent[2:])),
        ),
        "basemap": _stereographic_kwargs,
    },
    {
        "name": "azimuthequidistant",
        "aliases": {"azimuthequidistant", "aeqd"},
        "cartopy": lambda ccrs, extent: ccrs.AzimuthalEquidistant(
            central_longitude=float(np.mean(extent[:2])),
            central_latitude=float(np.mean(extent[2:])),
        ),
        "basemap": _azimuthal_equidistant_kwargs,
    },
]

for entry in _PROJECTION_DEFINITIONS:
    entry["name"] = _normalize_proj_name(entry["name"])
    alias_set = {entry["name"]}
    alias_set.update(_normalize_proj_name(alias) for alias in entry.get("aliases", []))
    entry["aliases"] = alias_set


def _get_projection_definition(value):
    normalized = _normalize_proj_name(value)
    for entry in _PROJECTION_DEFINITIONS:
        aliases = entry["aliases"]
        if normalized == entry["name"] or normalized in aliases:
            return entry
    raise KeyError(value)


def _resolve_cartopy_projection(spec, extent, default, parameter_name):
    if spec is None:
        return default

    if _cartopy_crs is not None and isinstance(spec, _cartopy_crs.CRS):
        return spec

    if isinstance(spec, str):
        try:
            definition = _get_projection_definition(spec)
        except KeyError as exc:
            raise TypeError(
                f"Unknown projection identifier '{spec}' for parameter '{parameter_name}'."
            ) from exc
        cartopy_factory = definition.get("cartopy")
        if cartopy_factory is None:
            raise TypeError(
                f"Projection '{spec}' is not available for the cartopy engine."
            )
        ccrs, _ = _get_cartopy_modules()
        return cartopy_factory(ccrs, extent)

    raise TypeError(
        f"Parameter '{parameter_name}' must be a cartopy CRS instance or a supported projection string when using the cartopy engine."
    )


def _resolve_basemap_projection(spec, extent):
    if spec is None:
        return {}

    if isinstance(spec, dict):
        return dict(spec)

    if isinstance(spec, str):
        try:
            definition = _get_projection_definition(spec)
        except KeyError as exc:
            raise TypeError(
                f"Unknown projection identifier '{spec}' for Basemap."
            ) from exc
        basemap_factory = definition.get("basemap")
        if basemap_factory is None:
            raise TypeError(
                f"Projection '{spec}' is not available for the basemap engine."
            )
        return basemap_factory(extent)

    if _cartopy_crs is not None and isinstance(spec, _cartopy_crs.CRS):
        return _cartopy_crs_to_basemap_kwargs(spec)

    raise TypeError(
        "proj must be a Basemap projection name/dict or a Cartopy CRS that can be translated when using the basemap engine"
    )


class _CartopyBackend:
    """Cartopy implementation of the engine-specific drawing operations."""

    name = "cartopy"

    def create_axes(self, extent, proj, data_proj, ax, figsize, coast, basemap_kwargs):
        ccrs, _ = _get_cartopy_modules()
        map_proj = _resolve_cartopy_projection(proj, extent, _proj_defaults("map"), "proj")
        data_crs = _resolve_cartopy_projection(data_proj, extent, _proj_defaults("data"), "data_proj")

        if ax is None:
            fig_init = True
            fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(projection=map_proj))
        else:
            fig_init = False
            fig = ax.figure

        ax.set_extent(extent, crs=data_crs)
        return {"fig": fig, "ax": ax, "fig_init": fig_init, "data_crs": data_crs, "basemap_obj": None, "coast": coast}

    def transform_kwargs(self, spec, extent_guess):
        crs = _resolve_cartopy_projection(spec, extent_guess, _proj_defaults("data"), "transform")
        return {"transform": crs}

    def contour(self, ax, lons, lats, elevation, **kwargs):
        return ax.contour(lons, lats, elevation, **kwargs)

    def contourf(self, ax, lons, lats, elevation, **kwargs):
        return ax.contourf(lons, lats, elevation, **kwargs)

    def pcolormesh(self, ax, lons, lats, elevation, **kwargs):
        return ax.pcolormesh(lons, lats, elevation, **kwargs)

    def quiver(self, ax, lons, lats, u, v, **kwargs):
        return ax.quiver(lons, lats, u, v, **kwargs)

    def legend_ax(self, ax):
        return ax

    def add_features(self, ax, edgecolor, landcolor, oceancolor, coast, zorder):
        _, cfeature = _get_cartopy_modules()
        if oceancolor is None:
            oceancolor = cfeature.COLORS["water"]

        state_lines = cfeature.NaturalEarthFeature(
            category="cultural",
            name="admin_1_states_provinces_lines",
            scale="50m",
            facecolor="none",
        )

        if coast == "full":
            land_feature = cfeature.GSHHSFeature(scale="full")
        elif coast == "high":
            land_feature = cfeature.NaturalEarthFeature("physical", "land", "10m")
        elif coast == "mid":
            land_feature = cfeature.NaturalEarthFeature("physical", "land", "50m")
        elif coast == "low":
            land_feature = cfeature.NaturalEarthFeature("physical", "land", "110m")
        elif coast == "crude":
            land_feature = cfeature.NaturalEarthFeature("physical", "land", "110m")
        else:
            land_feature = cfeature.NaturalEarthFeature("physical", "land", "50m")

        ax.set_facecolor(oceancolor)
        ax.add_feature(
            land_feature,
            edgecolor=edgecolor,
            facecolor=landcolor,
            zorder=zorder + 10,
        )
        ax.add_feature(cfeature.RIVERS, zorder=zorder + 10.2)
        ax.add_feature(cfeature.LAKES, zorder=zorder + 10.2, alpha=0.5)
        ax.add_feature(state_lines, edgecolor=edgecolor, linestyle="--", zorder=zorder + 10.3)
        ax.add_feature(cfeature.BORDERS, zorder=zorder + 10.3)

    def add_ticks(
        self, ax, extent, proj, fontsize, label_left, label_right, label_bottom, label_top,
        gridlines, decimal_degrees, whole_degree_majors,
    ):
        proj = _resolve_cartopy_projection(proj, extent, _proj_defaults("data"), "proj")

        tick0x, tick1, ticklab = calculate_ticks(
            extent, "longitude", decimal_degrees=decimal_degrees, whole_degree_majors=whole_degree_majors
        )
        ax.set_xticks(tick0x, minor=True, crs=proj)
        ax.set_xticks(tick1, crs=proj)
        ax.set_xticklabels(ticklab, fontsize=fontsize)

        tick0y, tick1, ticklab = calculate_ticks(
            extent, "latitude", decimal_degrees=decimal_degrees, whole_degree_majors=whole_degree_majors
        )
        ax.set_yticks(tick0y, minor=True, crs=proj)
        ax.set_yticks(tick1, crs=proj)
        ax.set_yticklabels(ticklab, fontsize=fontsize)

        ax.tick_params(
            which="major",
            direction="out",
            bottom=True,
            top=True,
            labelbottom=label_bottom,
            labeltop=label_top,
            left=True,
            right=True,
            labelleft=label_left,
            labelright=label_right,
            length=5,
            width=2,
        )

        ax.tick_params(
            which="minor",
            direction="out",
            bottom=True,
            top=True,
            left=True,
            right=True,
            width=1,
        )

        if gridlines:
            gl = ax.gridlines(
                draw_labels=False,
                linewidth=0.5,
                color="black",
                alpha=0.5,
                linestyle="--",
                crs=proj,
                zorder=100,
            )
            gl.xlocator = mticker.FixedLocator(tick0x)
            gl.ylocator = mticker.FixedLocator(tick0y)

    def fallback_gridlines(self, ax, extent):
        ax.gridlines()


class _BasemapBackend:
    """Basemap implementation of the engine-specific drawing operations."""

    name = "basemap"

    def create_axes(self, extent, proj, data_proj, ax, figsize, coast, basemap_kwargs):
        BasemapClass = _get_basemap_class()
        user_basemap_kwargs = dict(basemap_kwargs or {})
        resolved_kwargs = _resolve_basemap_projection(proj, extent)
        resolved_kwargs.update(user_basemap_kwargs)
        resolved_kwargs.setdefault("projection", "merc")
        resolved_kwargs.setdefault("llcrnrlon", extent[0])
        resolved_kwargs.setdefault("urcrnrlon", extent[1])
        resolved_kwargs.setdefault("llcrnrlat", extent[2])
        resolved_kwargs.setdefault("urcrnrlat", extent[3])
        resolved_kwargs.setdefault("resolution", _coast_to_basemap_resolution(coast))

        if ax is None:
            fig_init = True
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig_init = False
            fig = ax.figure

        resolved_kwargs.setdefault("ax", ax)
        try:
            basemap_obj = BasemapClass(**resolved_kwargs)
        except OSError as e:
            if "basemap-data-hires" in str(e):
                warnings.warn(
                    "High-resolution basemap data not found. Falling back to intermediate resolution. "
                    "To use high/full resolution, install the `basemap-data-hires` package."
                )
                resolved_kwargs["resolution"] = "i"
                if coast in ("full", "high"):
                    coast = "mid"  # Align add_features with the intermediate resolution
                basemap_obj = BasemapClass(**resolved_kwargs)
            else:
                raise

        return {
            "fig": fig,
            "ax": ax,
            "fig_init": fig_init,
            "data_crs": None,
            "basemap_obj": basemap_obj,
            "coast": coast,
        }

    def transform_kwargs(self, spec, extent_guess):
        return {"latlon": True}

    def contour(self, ax, lons, lats, elevation, **kwargs):
        kwargs.pop("transform_first", None)  # Basemap.contour has no equivalent parameter
        basemap_obj, _ = _resolve_basemap(ax)
        return _call_basemap_method(ax, basemap_obj, "contour", lons, lats, elevation, **kwargs)

    def contourf(self, ax, lons, lats, elevation, **kwargs):
        basemap_obj, _ = _resolve_basemap(ax)
        return _call_basemap_method(ax, basemap_obj, "contourf", lons, lats, elevation, **kwargs)

    def pcolormesh(self, ax, lons, lats, elevation, **kwargs):
        basemap_obj, _ = _resolve_basemap(ax)
        return _call_basemap_method(ax, basemap_obj, "pcolormesh", lons, lats, elevation, **kwargs)

    def quiver(self, ax, lons, lats, u, v, **kwargs):
        basemap_obj, _ = _resolve_basemap(ax)
        return _call_basemap_method(ax, basemap_obj, "quiver", lons, lats, u, v, **kwargs)

    def legend_ax(self, ax):
        _, mpl_ax = _resolve_basemap(ax)
        return mpl_ax

    def add_features(self, ax, edgecolor, landcolor, oceancolor, coast, zorder):
        basemap_obj, mpl_ax = _resolve_basemap(ax)
        if oceancolor is None:
            if _cartopy_feature is not None:
                oceancolor = mcolors.to_hex(_cartopy_feature.COLORS["water"])
            else:
                oceancolor = "#97b6e1"  # Cartopy water default fallback

        mpl_ax.set_facecolor(oceancolor)
        basemap_obj.drawmapboundary(fill_color=oceancolor, linewidth=0, zorder=zorder)
        basemap_obj.fillcontinents(color=landcolor, lake_color=oceancolor, zorder=zorder + 10)
        basemap_obj.drawcoastlines(color=edgecolor, linewidth=0.5, zorder=zorder + 11)
        basemap_obj.drawcountries(color=edgecolor, linewidth=0.5, zorder=zorder + 11.3)

        # States and rivers data is absent in crude and low Basemap resolutions
        if coast not in ("crude", "low"):
            state_lines = basemap_obj.drawstates(color=edgecolor, linewidth=0.4, zorder=zorder + 11.2)
            state_lines.set_linestyle("--")
            basemap_obj.drawrivers(color=edgecolor, linewidth=0.4, zorder=zorder + 11.1)

    def add_ticks(
        self, ax, extent, proj, fontsize, label_left, label_right, label_bottom, label_top,
        gridlines, decimal_degrees, whole_degree_majors,
    ):
        basemap_obj, mpl_ax = _resolve_basemap(ax)

        lon_minor, lon_major, lon_labels = calculate_ticks(
            extent, "longitude", decimal_degrees=decimal_degrees, whole_degree_majors=whole_degree_majors
        )
        lat_minor, lat_major, lat_labels = calculate_ticks(
            extent, "latitude", decimal_degrees=decimal_degrees, whole_degree_majors=whole_degree_majors
        )

        lon_minor = np.asarray(lon_minor, dtype=float)
        lon_major = np.asarray(lon_major, dtype=float)
        lat_minor = np.asarray(lat_minor, dtype=float)
        lat_major = np.asarray(lat_major, dtype=float)
        lon_labels = [str(label) for label in lon_labels]
        lat_labels = [str(label) for label in lat_labels]

        def _as_float_array(values):
            arr = np.ma.asarray(values, dtype=float)
            if np.ma.isMaskedArray(arr):
                return np.asarray(arr.filled(np.nan), dtype=float)
            return np.asarray(arr, dtype=float)

        def _project_lons(values, lat_ref, labels=None):
            if values.size == 0:
                return np.array([]), [] if labels is not None else np.array([])
            xs, _ = basemap_obj(values, np.full_like(values, lat_ref, dtype=float))
            xs = _as_float_array(xs)
            mask = np.isfinite(xs)
            xs = xs[mask]
            if labels is None:
                return xs, None
            filtered_labels = [labels[i] for i, keep in enumerate(mask) if keep]
            return xs, filtered_labels

        def _project_lats(values, lon_ref, labels=None):
            if values.size == 0:
                return np.array([]), [] if labels is not None else np.array([])
            _, ys = basemap_obj(np.full_like(values, lon_ref, dtype=float), values)
            ys = _as_float_array(ys)
            mask = np.isfinite(ys)
            ys = ys[mask]
            if labels is None:
                return ys, None
            filtered_labels = [labels[i] for i, keep in enumerate(mask) if keep]
            return ys, filtered_labels

        x_major, lon_labels = _project_lons(lon_major, extent[2], lon_labels)
        x_minor, _ = _project_lons(lon_minor, extent[2])
        y_major, lat_labels = _project_lats(lat_major, extent[0], lat_labels)
        y_minor, _ = _project_lats(lat_minor, extent[0])

        if x_major.size:
            mpl_ax.xaxis.set_major_locator(mticker.FixedLocator(x_major))
            mpl_ax.xaxis.set_major_formatter(mticker.FixedFormatter(lon_labels))
        else:
            mpl_ax.xaxis.set_major_locator(mticker.NullLocator())
            mpl_ax.xaxis.set_major_formatter(mticker.NullFormatter())

        if x_minor.size:
            mpl_ax.xaxis.set_minor_locator(mticker.FixedLocator(x_minor))
        else:
            mpl_ax.xaxis.set_minor_locator(mticker.NullLocator())

        if y_major.size:
            mpl_ax.yaxis.set_major_locator(mticker.FixedLocator(y_major))
            mpl_ax.yaxis.set_major_formatter(mticker.FixedFormatter(lat_labels))
        else:
            mpl_ax.yaxis.set_major_locator(mticker.NullLocator())
            mpl_ax.yaxis.set_major_formatter(mticker.NullFormatter())

        if y_minor.size:
            mpl_ax.yaxis.set_minor_locator(mticker.FixedLocator(y_minor))
        else:
            mpl_ax.yaxis.set_minor_locator(mticker.NullLocator())

        mpl_ax.tick_params(
            which="major",
            direction="out",
            bottom=True,
            top=True,
            labelbottom=label_bottom,
            labeltop=label_top,
            left=True,
            right=True,
            labelleft=label_left,
            labelright=label_right,
            length=5,
            width=2,
        )

        mpl_ax.tick_params(
            which="minor",
            direction="out",
            bottom=True,
            top=True,
            left=True,
            right=True,
            length=3,
            width=1,
        )

        for tick in mpl_ax.xaxis.get_majorticklabels():
            tick.set_fontsize(fontsize)
        for tick in mpl_ax.yaxis.get_majorticklabels():
            tick.set_fontsize(fontsize)

        if gridlines:
            line_kwargs = {"linewidth": 0.5, "color": "black", "dashes": [2, 2]}
            grid_lons = lon_minor if lon_minor.size else lon_major
            grid_lats = lat_minor if lat_minor.size else lat_major
            if grid_lons.size:
                basemap_obj.drawmeridians(grid_lons, labels=[0, 0, 0, 0], **line_kwargs)
            if grid_lats.size:
                basemap_obj.drawparallels(grid_lats, labels=[0, 0, 0, 0], **line_kwargs)

    def fallback_gridlines(self, ax, extent):
        _draw_basemap_gridlines(ax, extent)


_BACKENDS = {}  # populated lazily so importing this module never requires both engines


def _get_backend(engine_name):
    if engine_name not in _BACKENDS:
        _BACKENDS[engine_name] = _CartopyBackend() if engine_name == "cartopy" else _BasemapBackend()
    return _BACKENDS[engine_name]


def _bathymetry_legend_labels(levels, legend_scale):
    """Build the {elevation: label} dict shared by both engines' shadedcontour method."""
    if legend_scale == "imperial":
        return {-x: f"{int(x * 0.546807)}fth" for x in np.sort(np.abs(levels))[::-1]}
    if legend_scale == "both":
        return {-x: f"{int(x * 0.546807)}fth, {int(x)}m" for x in np.sort(np.abs(levels))[::-1]}
    return {-x: f"{int(x)}m" for x in np.sort(np.abs(levels))[::-1]}


def _draw_bathymetry_legend(legend_ax, bathy_labels, rgb_col, levels, fontsize):
    cs_cols = [plt.Line2D((0, 1), (0, 1), color=pc) for pc in rgb_col]
    legend_ax.legend(
        cs_cols[::-1],
        list(bathy_labels.values())[::-1],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.05),
        fancybox=True,
        ncol=len(levels),
        fontsize=fontsize,
    )


def _banded_legend_labels(edges, legend_scale):
    """Build one 'depth range' label per band, from deepest to shallowest, for the 'banded' method."""
    labels = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        if legend_scale == "imperial":
            labels.append(f"{int(round(lo * 0.546807))} to {int(round(hi * 0.546807))} fth")
        elif legend_scale == "both":
            labels.append(f"{int(round(lo * 0.546807))} to {int(round(hi * 0.546807))} fth, {int(lo)} to {int(hi)} m")
        else:
            labels.append(f"{int(lo)} to {int(hi)} m")
    return labels


def _draw_banded_legend(legend_ax, band_labels, colors, fontsize):
    handles = [mpatches.Patch(facecolor=color, edgecolor="black", linewidth=0.5) for color in colors]
    # band_labels/colors are computed deepest-to-shallowest (matching contourf's levels/colors
    # convention), but the legend should read shallowest-to-deepest.
    legend_ax.legend(
        handles[::-1],
        band_labels[::-1],
        loc="upper center",
        bbox_to_anchor=(0.5, -0.05),
        fancybox=True,
        ncol=len(colors),
        fontsize=fontsize,
        title="Bathymetry",
        title_fontsize=fontsize,
    )


def _default_banded_colors(n_bands):
    """
    Default fill colors for bathymetry_method='banded', only defined for the common
    3-band case (cool_maps' own default isobaths=(-1000, -100) produces exactly 3 bands),
    with the middle band matching cool_maps' usual default ocean color. Returns None for
    any other band count, since there's no principled way to guess arbitrary colors.
    """
    if n_bands != 3:
        return None
    if _cartopy_feature is not None:
        water = _cartopy_feature.COLORS["water"]
    else:
        water = "#97b6e1"  # Cartopy water default fallback, matches add_features' basemap branch
    return ["cornflowerblue", water, "lightsteelblue"]


_ESCAPE_HATCH_METHODS = ("scatter", "plot", "contour", "contourf", "pcolormesh", "quiver", "fill")

_UNSET = object()


def _call_basemap_method(ax, basemap_obj, name, *args, **kwargs):
    """
    Call basemap_obj.<name>(...), guarding against Basemap's own implementation calling
    back into `ax.<name>(...)` internally once coordinates are projected (which every
    caller of this helper -- the escape-hatch wrapper below, and _BasemapBackend's
    contour/contourf/pcolormesh/quiver primitives -- risks triggering, since `ax.<name>`
    may itself be an escape-hatch override delegating back to this same basemap_obj
    method). Without this guard, that internal call recurses back through the override
    and double-projects already-projected coordinates, silently producing a near-empty
    plot rather than an error.
    """
    saved = ax.__dict__.pop(name, _UNSET)
    try:
        return getattr(basemap_obj, name)(*args, **kwargs)
    finally:
        if saved is not _UNSET:
            ax.__dict__[name] = saved


def _make_cartopy_escape_hatch(ax, original, ccrs):
    def wrapper(*args, **kwargs):
        kwargs.setdefault("transform", ccrs.PlateCarree())
        return original(ax, *args, **kwargs)
    return wrapper


def _make_basemap_escape_hatch(ax, name, basemap_obj):
    def wrapper(*args, **kwargs):
        kwargs.setdefault("latlon", True)
        return _call_basemap_method(ax, basemap_obj, name, *args, **kwargs)
    return wrapper


def _bind_escape_hatch_methods(ax, engine_name, basemap_obj=None):
    """
    Bind instance-level overrides for common plotting verbs directly onto `ax` so that
    lon/lat data passed to ax.scatter/plot/contour/contourf/pcolormesh/quiver/fill
    "just works" under either engine, without the caller passing transform= (cartopy)
    or latlon=True (basemap) themselves. `ax` remains a real matplotlib Axes/GeoAxes in
    every other respect -- this only shadows a handful of instance methods, the same
    monkey-patching pattern _flag_axes already uses on this same object.
    """
    if engine_name == "cartopy":
        ccrs, _ = _get_cartopy_modules()
        cls = type(ax)  # look up the CLASS method, not ax.<name>, so re-flagging an
        for name in _ESCAPE_HATCH_METHODS:  # already-wrapped axes doesn't double-wrap/recurse
            original = getattr(cls, name, None)
            if original is None:
                continue
            setattr(ax, name, _make_cartopy_escape_hatch(ax, original, ccrs))
    else:
        if basemap_obj is None:
            return
        for name in _ESCAPE_HATCH_METHODS:
            if not hasattr(basemap_obj, name):
                continue
            setattr(ax, name, _make_basemap_escape_hatch(ax, name, basemap_obj))


def _preprocess_elevation(elevation, method):
    """Apply log transform and land masking to elevation array before plotting."""
    elevation = np.array(elevation, copy=True)
    if method in ["blues_log", "topo_log", "topofull_log"]:
        elevation[np.abs(elevation) < 1] = 0
        elevation[elevation > 0] = np.log10(elevation[elevation > 0])
        elevation[elevation < 0] = -np.log10(np.abs(elevation[elevation < 0]))
    if method in ["blues", "topo", "blues_log", "topo_log"]:
        elevation[elevation > 0] = np.nan
    return elevation


def _draw_basemap_gridlines(ax, extent, linewidth=0.5):
    basemap_obj, _ = _resolve_basemap(ax)
    _, lon_ticks, _ = calculate_ticks(extent, "longitude", decimal_degrees=True)
    _, lat_ticks, _ = calculate_ticks(extent, "latitude", decimal_degrees=True)
    kwargs = {"linewidth": linewidth, "color": "black", "dashes": [2, 2]}
    if lon_ticks.size:
        basemap_obj.drawmeridians(lon_ticks, labels=[0, 0, 0, 0], **kwargs)
    if lat_ticks.size:
        basemap_obj.drawparallels(lat_ticks, labels=[0, 0, 0, 0], **kwargs)


def add_bathymetry(
    ax,
    lon,
    lat,
    elevation,
    levels=(-1000,),
    method="contour",
    legend_scale=None,
    fontsize=13,
    zorder=5,
    transform=None,
    transform_first=False,
    colors=None,
    engine=None,
):
    """
    Plot bathymetry lines on map

    Args:
        ax (matplotlib.axes.Axes or mpl_toolkits.basemap.Basemap): target axes or basemap
        lon (array-like): Longitudes of bathymetry
        lat (array-like): Latitudes of bathymetry
        elevation (array-like): Elevation of bathymetry
        levels (tuple, optional): Number/positions of contour lines. Defaults to (-1000).
        method (string): Method for plotting bathymetry. Defaults to contour. Options:
            - contour: standard black contour at :levels:
            - shadedcontour: contours in shades of gray varying with depth
            - banded: discrete depth bands at :levels: filled with :colors: (deepest to shallowest), plus the usual black isobath lines/labels and a color-swatch legend
            - blues: pcolormesh using Blues colormap; excludes land and ignores :levels:
            - blues_log: pcolormesh of log-transformed bathymetry using Blues colormap; excludes land and ignores :levels:
            - topo: pcolormesh using cmocean topo colormap; excludes land and ignores :levels:
            - topo_log: pcolormesh of log-transformed bathymetry using cmocean topo colormap; excludes land and ignores :levels:
            - topofull: pcolormesh using cmocean topo colormap; includes land and ignores :levels:
            - topofull_log: pcolormesh of log-transformed altitude/bathymetry using cmocean topo colormap; includes land and ignores :levels:
        legend_scale (string, optional): Measurement system to use for legend. Supported for shadedcontour and banded.
            Defaults to "both" for shadedcontour and "metric" for banded.
            - metric: meters
            - imperial: fathoms
            - both: meters and fathoms
            - off: no legend
        fontsize (int, optional): Font size for legend
        zorder (int, optional): Drawing order. Defaults to 5.
        transform: Cartopy transform/CRS or supported projection string for lon/lat input (cartopy engine only)
        transform_first (bool, optional): Transform points before contouring (cartopy engine only)
        colors (list, optional): Fill colors for method="banded", ordered from deepest to shallowest.
            Must have exactly len(levels) + 1 entries: one for the water deeper than the shallowest
            level, one for each band between consecutive levels, and one for the band up to 0. If
            omitted, defaults to ["cornflowerblue", cfeature.COLORS["water"], "lightsteelblue"] when
            levels produces exactly 3 bands (e.g. the default levels=(-1000, -100)); otherwise required.
        engine (str, optional): Override active mapping engine ("cartopy" or "basemap")

    Returns:
        object: plotted bathymetry handle
    """
    engine_name = _get_engine_name(engine, ax=ax)
    backend = _get_backend(engine_name)

    recognized_methods = [
        "contour",
        "shadedcontour",
        "banded",
        "blues",
        "blues_log",
        "topo",
        "topo_log",
        "topofull",
        "topofull_log",
    ]
    recognized_legends = ["metric", "imperial", "both", "off"]

    if method not in recognized_methods:
        raise ValueError(
            f"{method} is not a currently supported option for bathymetry plotting. "
            f"Please choose from {', '.join(recognized_methods)}"
        )
    if legend_scale is None:
        legend_scale = "metric" if method == "banded" else "both"
    if legend_scale not in recognized_legends:
        raise ValueError(
            f"{legend_scale} is not a currently supported option for the legend. "
            f"Please choose from {', '.join(recognized_legends)}"
        )

    lon = np.asarray(lon)
    lat = np.asarray(lat)
    lons, lats = np.meshgrid(lon, lat)
    elevation = _preprocess_elevation(elevation, method)

    try:
        extent_guess = (
            float(np.nanmin(lon)),
            float(np.nanmax(lon)),
            float(np.nanmin(lat)),
            float(np.nanmax(lat)),
        )
    except (ValueError, TypeError):
        extent_guess = (-180.0, 180.0, -90.0, 90.0)

    tkwargs = backend.transform_kwargs(transform, extent_guess)

    if method == "contour":
        h = backend.contour(
            ax,
            lons,
            lats,
            elevation,
            levels=levels,
            linewidths=0.75,
            alpha=0.5,
            colors="k",
            zorder=zorder,
            transform_first=transform_first,
            **tkwargs,
        )
        backend.legend_ax(ax).clabel(h, levels, inline=True, fontsize=6, fmt=fmt)

    if method == "shadedcontour":
        ci = 1.0 / float(len(levels))
        bathy_labels = _bathymetry_legend_labels(levels, legend_scale)
        rgb_col = [(ci * cs, ci * cs, ci * cs) for cs in range(len(bathy_labels))]
        h = []
        for cs, level in enumerate(bathy_labels):
            h = np.append(
                h,
                backend.contour(
                    ax,
                    lons,
                    lats,
                    elevation,
                    levels=[level],
                    linestyles="solid",
                    linewidths=0.75,
                    colors=[(ci * cs, ci * cs, ci * cs)],
                    zorder=zorder,
                    **tkwargs,
                ),
            )
        if legend_scale != "off":
            _draw_bathymetry_legend(backend.legend_ax(ax), bathy_labels, rgb_col, levels, fontsize)

    if method == "banded":
        sorted_levels = sorted(float(level) for level in levels)
        edges = [float(np.nanmin(elevation)), *sorted_levels, 0.0]
        if any(hi <= lo for lo, hi in zip(edges[:-1], edges[1:])):
            raise ValueError(
                "levels must fall strictly between the data's minimum elevation and 0 "
                "for bathymetry_method='banded'."
            )
        n_bands = len(edges) - 1
        if colors is None:
            colors = _default_banded_colors(n_bands)
            if colors is None:
                raise ValueError(
                    f"colors must be provided when using bathymetry_method='banded' with {n_bands} bands "
                    "(a built-in default is only available for the 2-level/3-band case, e.g. levels=(-1000, -100))."
                )
        if len(colors) != n_bands:
            raise ValueError(
                f"colors must have {n_bands} entries (one per band) to match {len(levels)} level(s) "
                f"for bathymetry_method='banded'; got {len(colors)}."
            )

        h = backend.contourf(ax, lons, lats, elevation, levels=edges, colors=list(colors), zorder=zorder, **tkwargs)

        lines = backend.contour(
            ax,
            lons,
            lats,
            elevation,
            levels=sorted_levels,
            linewidths=0.75,
            alpha=0.5,
            colors="k",
            zorder=zorder + 0.1,
            transform_first=transform_first,
            **tkwargs,
        )
        backend.legend_ax(ax).clabel(lines, sorted_levels, inline=True, fontsize=6, fmt=fmt)

        if legend_scale != "off":
            band_labels = _banded_legend_labels(edges, legend_scale)
            _draw_banded_legend(backend.legend_ax(ax), band_labels, colors, fontsize)

    if method in ["blues", "blues_log"]:
        cmap = plt.cm.Blues_r
        vmin = np.nanquantile(elevation, 0.05)
        vmax = 0
    if method in ["topo", "topo_log", "topofull", "topofull_log"]:
        cmap = cmo.cm.topo
        vmin = -np.nanquantile(np.abs(elevation), 0.95)
        vmax = np.nanquantile(np.abs(elevation), 0.95)
    if method in ["blues", "blues_log", "topo", "topo_log", "topofull", "topofull_log"]:
        h = backend.pcolormesh(
            ax,
            lons,
            lats,
            elevation,
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            shading="auto",
            zorder=zorder,
            **tkwargs,
        )

    return h


def add_glider_bathymetry(ax, deployment, time_start=None, time_end=None, color="black"):
    """
    Download and plot bathymetry measured by glider during a given deployment

    Args:
        ax (matplotlib.axes): matplotlib axes
        deployment (str): name of deployment to grab and plot bathymetry for
        time_start (str, optional): Start time. Defaults to None/beginning of deployment
        time_end (str, optional): End time. Defaults to None/end of deployment
        color (str, optional): name of color to plot bathymetry
    Returns:
        object: Patch
    """

    glider_bathy = get_glider_bathymetry(deployment, time_start=time_start, time_end=time_end)
    floor_depth = np.max(glider_bathy["water_depth"]) * 1.05
    times = np.append(glider_bathy["time"], [max(glider_bathy["time"]), min(glider_bathy["time"])])
    depths = np.append(glider_bathy["water_depth"], [floor_depth, floor_depth])
    h = plt.fill(times, depths, color=color)

    return h


def add_currents(
    ax,
    ds,
    coarsen=2,
    scale=90,
    headwidth=2.75,
    headlength=2.75,
    headaxislength=2.5,
    engine=None,
):
    """
    Plot currents on map

    Args:
        ax (matplotlib.axes): matplotlib axes
        ds (xarray.Dataset): dataset containing lon, lat, u, and v data.
        coarsen (int, optional): Downsampling factor applied to lon/lat dimensions. Defaults to 2.
        scale (float, optional): Number of data units per arrow length unit. Defaults to 90.
        headwidth (float, optional): Head width as multiple of shaft width. Defaults to 2.75.
        headlength (float, optional): Head length as multiple of shaft width. Defaults to 2.75.
        headaxislength (float, optional): Head length at shaft intersection. Defaults to 2.5.
        engine (str, optional): Override active mapping engine ("cartopy" or "basemap")

    Returns:
        object: Quiver
    """

    engine_name = _get_engine_name(engine, ax=ax)
    backend = _get_backend(engine_name)

    _required = {"u", "v"}
    _missing = _required - set(ds.data_vars)
    if _missing:
        raise ValueError(
            f"add_currents() requires variables {sorted(_required)} in the dataset. "
            f"Missing: {sorted(_missing)}"
        )
    _has_lonlat = "lon" in ds.coords and "lat" in ds.coords
    _has_xy = "x" in ds.dims and "y" in ds.dims
    if not (_has_lonlat or _has_xy):
        raise ValueError(
            "add_currents() expects dataset coordinates named 'lon'/'lat' or dimensions named 'x'/'y'."
        )

    try:
        qds = ds.coarsen(lon=coarsen, boundary="pad").mean().coarsen(lat=coarsen, boundary="pad").mean()
        mesh = True
    except ValueError:
        qds = ds.coarsen(x=coarsen, boundary="pad").mean().coarsen(y=coarsen, boundary="pad").mean()
        mesh = False

    angle, speed = uv2spdir(qds["u"], qds["v"])  # convert u/v to angle and speed
    u, v = spdir2uv(
        np.ones_like(speed),
        angle,
        deg=True,
    )

    tkwargs = backend.transform_kwargs(None, None)
    qargs = {
        "scale": scale,
        "headwidth": headwidth,
        "headlength": headlength,
        "headaxislength": headaxislength,
        **tkwargs,
    }
    if mesh:
        lons, lats = np.meshgrid(qds["lon"], qds["lat"])
        return backend.quiver(ax, lons, lats, u, v, **qargs)
    return backend.quiver(
        ax,
        qds.lon.squeeze().data,
        qds.lat.squeeze().data,
        u.squeeze(),
        v.squeeze(),
        **qargs,
    )


def add_features(
    ax,
    edgecolor="black",
    landcolor="tan",
    oceancolor=None,
    coast="full",
    zorder=0,
    engine=None,
):
    """
    Automatically add the following features to make the map nicer looking.

    Args:
        ax (matplotlib.Axis): matplotlib axis
        edgecolor (str, optional): Color of edges of polygons. Defaults to "black".
        landcolor (str, optional): Color of land. Defaults to "tan".
        oceancolor (str, optional): Color of ocean. Defaults to cartopy default water color
        coast (str, optional): Coastline resolution.
        zorder (int, optional): Drawing order.
        engine (str, optional): Override active mapping engine
    """

    engine_name = _get_engine_name(engine, ax=ax)
    backend = _get_backend(engine_name)
    backend.add_features(
        ax,
        edgecolor=edgecolor,
        landcolor=landcolor,
        oceancolor=oceancolor,
        coast=coast,
        zorder=zorder,
    )


def add_double_temp_colorbar(ax, h, vmin, vmax, anomaly=False, fontsize=13):
    """
    Add colorbar with Celsius and Fahrenheit units
    https://pythonmatplotlibtips.blogspot.com/2019/07/draw-two-axis-to-one-colorbar.html

    Args:
        ax (matplotlib.axes): matplotlib axes
        h (matplotlib object handle to match colorbar to):
        vmin (float): minimum value of colorbar (should match vmin of object colorbar is mapped to)
        vmax (float): maximum value of colorbar (should match vmax of object colorbar is mapped to)
        anomaly (bool): whether product is an anomaly
        fontsize (int, optional): font size for tick labels

    Returns:
        object: Colorbar
        axes: Twin axes for colorbar
    """

    cbticks = calculate_colorbar_ticks(vmin, vmax, c0=anomaly)
    if anomaly:
        cbticksF = calculate_colorbar_ticks(vmin * 1.8, vmax * 1.8, c0=anomaly)
    else:
        cbticksF = calculate_colorbar_ticks(vmin * 1.8 + 32, vmax * 1.8 + 32, c0=anomaly)
    cbCLabels = [str(int(cbticks[i])) + "°" + "C" for i in range(len(cbticks))]
    cbFLabels = [str(int(cbticksF[i])) + "°" + "F" for i in range(len(cbticksF))]

    cb = plt.colorbar(h)
    cb.ax.set_yticks(cbticks, labels=cbCLabels, fontsize=fontsize)
    pcb = cb.ax.get_position()
    pax = ax.get_position()

    cb.ax.set_aspect("auto")
    pcb.x0 = pax.x1 + 0.055
    pcb.x1 = pax.x1 + 0.085
    pcb.y0 = pax.y0
    pcb.y1 = pax.y1
    cb2 = cb.ax.twinx()
    ax.set_position(pax)
    cb2.set_ylim(np.array([vmin, vmax]) * 1.8 + (32 * (not anomaly)))
    cb2.yaxis.set_label_position("left")
    cb2.yaxis.set_ticks_position("left")
    cb.ax.yaxis.set_label_position("right")
    cb.ax.yaxis.set_ticks_position("right")
    cb2.set_yticks(cbticksF, labels=cbFLabels, fontsize=fontsize)
    cb.ax.set_position(pcb)
    cb2.set_position(pcb)
    cb2.spines["right"].set_visible(False)
    cb2.spines["top"].set_visible(False)
    cb2.spines["bottom"].set_visible(False)

    return cb, cb2


def add_colorbar(ax, h, label=None, fontsize=12, pad=0.02, **kwargs):
    """
    Add a colorbar to the figure attached to the given axes.

    Args:
        ax (matplotlib.axes): The axes to attach the colorbar to.
        h: Mappable object (e.g. from pcolormesh, contourf, scatter).
        label (str, optional): Colorbar label. Defaults to None.
        fontsize (int, optional): Font size for the label and tick labels. Defaults to 12.
        pad (float, optional): Fraction of original axes between colorbar and axes. Defaults to 0.02.
        **kwargs: Additional keyword arguments passed to plt.colorbar().

    Returns:
        matplotlib.colorbar.Colorbar
    """
    cb = plt.colorbar(h, ax=ax, pad=pad, **kwargs)
    if label:
        cb.set_label(label, fontsize=fontsize)
    cb.ax.tick_params(labelsize=fontsize)
    return cb


def add_legend(ax, *args, **kwargs):
    """
    Add a legend to `ax` without discarding any legend already there.

    Matplotlib keeps only one "current" legend per axes -- a second `ax.legend()` call
    normally replaces the first outright. This is common with cool_maps maps: `create()`
    with `bathymetry_method="shadedcontour"`/`"banded"` already builds one legend, and you
    often want a second one for your own overlaid data (markers, tracks, etc.). This
    function preserves whatever legend is already on `ax` (re-registering it as a plain
    artist, with clipping turned back off since `ax.add_artist()` would otherwise clip it
    to the axes' rectangular patch -- fatal for legends positioned outside the axes, like
    cool_maps' own bathymetry legends) before creating the new one, so you can call this
    repeatedly to build up any number of legends on the same axes.

    Args:
        ax (matplotlib.axes): Axes to add the legend to.
        *args: Passed through to ax.legend().
        **kwargs: Passed through to ax.legend().

    Returns:
        matplotlib.legend.Legend: the newly created legend.
    """
    existing = ax.get_legend()
    if existing is not None:
        ax.add_artist(existing)
        existing.set_clip_on(False)
    return ax.legend(*args, **kwargs)


def add_marker(ax, lon, lat, engine=None, **scatter_kwargs):
    """
    Plot one or more markers at geographic coordinates, handling engine differences automatically.

    Args:
        ax (matplotlib.axes): Axes created by cool_maps.create().
        lon (float or array-like): Longitude(s) of marker(s).
        lat (float or array-like): Latitude(s) of marker(s).
        engine (str, optional): Override active mapping engine ("cartopy" or "basemap").
        **scatter_kwargs: Keyword arguments passed to ax.scatter() or basemap.scatter().
                          Common: marker, color/c, s (size), zorder, label.

    Returns:
        PathCollection: scatter handle
    """
    engine_name = _get_engine_name(engine, ax=ax)
    lon = np.atleast_1d(lon)
    lat = np.atleast_1d(lat)

    if engine_name == "cartopy":
        ccrs, _ = _get_cartopy_modules()
        scatter_kwargs.setdefault("transform", ccrs.PlateCarree())
        return ax.scatter(lon, lat, **scatter_kwargs)

    basemap_obj, mpl_ax = _resolve_basemap(ax)
    scatter_kwargs.setdefault("latlon", True)
    scatter_kwargs.setdefault("zorder", 5)
    return _call_basemap_method(ax, basemap_obj, "scatter", lon, lat, **scatter_kwargs)


def add_ticks(
    ax,
    extent,
    proj=None,
    fontsize=13,
    label_left=True,
    label_right=False,
    label_bottom=True,
    label_top=False,
    gridlines=False,
    decimal_degrees=False,
    whole_degree_majors=True,
    engine=None,
):
    """
    Calculate and add nicely formatted ticks to your map

    Args:
        ax (matplotlib.Axis): matplotlib Axis
        extent (tuple or list): extent (x0, x1, y0, y1) of the map.
        proj (cartopy CRS/str, optional): projection for ticks (cartopy engine only).
        fontsize (int, optional): Font size of tick labels. Defaults to 13.
        gridlines (bool, optional): Add gridlines to map. Defaults to False.
        decimal_degrees (bool, optional): Label axes with decimal degrees. Defaults to False.
        whole_degree_majors (bool, optional): keep major ticks on whole degrees even for small
            extents (span <= 3 degrees). Defaults to True. Set to False to allow major ticks at
            15'/30' increments for spans <= 3 degrees, matching pre-1.x behavior.
        engine (str, optional): Override active mapping engine
    """

    engine_name = _get_engine_name(engine, ax=ax)
    backend = _get_backend(engine_name)
    backend.add_ticks(
        ax,
        extent,
        proj=proj,
        fontsize=fontsize,
        label_left=label_left,
        label_right=label_right,
        label_bottom=label_bottom,
        label_top=label_top,
        gridlines=gridlines,
        decimal_degrees=decimal_degrees,
        whole_degree_majors=whole_degree_majors,
    )


def create(
    extent,
    proj=None,
    data_proj=None,
    padding=0.25,
    features=True,
    edgecolor="black",
    landcolor="tan",
    oceancolor=None,
    coast="full",
    ticks=True,
    gridlines=False,
    bathymetry=False,
    isobaths=(-1000, -100),
    bathymetry_method="contour",
    bathymetry_colors=None,
    bathymetry_legend_scale=None,
    bathymetry_file=None,
    xlabel=None,
    ylabel=None,
    tick_label_left=True,
    tick_label_right=False,
    tick_label_bottom=True,
    tick_label_top=False,
    decimal_degrees=False,
    whole_degree_majors=True,
    labelsize=14,
    ax=None,
    figsize=(11, 8),
    zorder=0,
    engine=None,
    basemap_kwargs=None,
    title=None,
    titlesize=14,
):
    """
    Create a map within a certain extent using the selected mapping engine.

    The returned axis is instrumented so that ax.scatter/plot/contour/contourf/pcolormesh/quiver/fill
    accept plain lon/lat data under either engine without passing transform=/latlon= yourself, and so
    that downstream cool_maps calls (add_features, add_bathymetry, ...) infer the engine from `ax`
    automatically.

    Args:
        extent (tuple or list): Extent (x0, x1, y0, y1) of the map in geographic coordinates.
        proj (optional): Projection spec. Accepts Cartopy CRS objects, supported projection strings, or Basemap kwargs.
        data_proj (optional): Data CRS when using cartopy. Accepts Cartopy CRS or supported projection strings.
        padding (float or tuple/list of 2 floats, optional): Degrees to expand the extent outward on each
            side so ticks/data don't land right on the map edge. A single number pads longitude and
            latitude equally; a 2-item sequence is (lon_padding, lat_padding). Defaults to 0.25. Set to 0
            to use `extent` exactly as given.
        features (bool, optional): Add preferred map settings: colors, rivers, lakes, etc. Defaults to True.
        edgecolor (str, optional): Color of edges of polygons. Defaults to "black".
        landcolor (str, optional): Color of land. Defaults to "tan".
        oceancolor (str, optional): Color of the ocean. Defaults to engine default.
        coast (str, optional): Coastline resolution.
        ticks (bool, optional): Calculate appropriately spaced ticks. Defaults to True.
        gridlines (bool, optional): Add gridlines. Defaults to False.
        bathymetry (bool or tuple, optional): Download and plot bathymetry on map. Defaults to False.
        isobaths (tuple or list, optional): Elevation at which to create bathymetric contour lines.
        bathymetry_method (str, optional): Method for plotting bathymetry.
        bathymetry_colors (list, optional): Fill colors, deepest to shallowest, when bathymetry_method="banded"
            (see add_bathymetry's `colors` argument, including its default for the 3-band case). Ignored
            for other methods.
        bathymetry_legend_scale (str, optional): See add_bathymetry's `legend_scale` argument, including its
            per-method defaults ("both" for shadedcontour, "metric" for banded).
        bathymetry_file (str or None): GMRT file to use for bathymetry, None to use ERDDAP.
        xlabel (str, optional): X Axis Label. Defaults to None.
        ylabel (str, optional): Y Axis Label. Defaults to None.
        tick_label_left/right/bottom/top (bool, optional): Control tick labels on each side.
        decimal_degrees (bool, optional): Label axes with decimal degrees instead of DMS.
        whole_degree_majors (bool, optional): keep major ticks on whole degrees even for small
            extents (span <= 3 degrees). Defaults to True. Set to False to allow major ticks at
            15'/30' increments for spans <= 3 degrees, matching pre-1.x behavior.
        labelsize (int, optional): Font size for axis labels. Defaults to 14.
        ax (matplotlib.Axis, optional): Matplotlib axis to use. Created if None.
        figsize (tuple, optional): Figure size if creating a new figure. Defaults to (11, 8).
        zorder (int, optional): Base zorder for artists.
        engine (str, optional): Override active mapping engine ("cartopy" or "basemap").
        basemap_kwargs (dict, optional): Additional kwargs passed to Basemap when using the basemap engine.
        title (str, optional): Title for the map axes. Defaults to None.
        titlesize (int, optional): Font size for the title. Defaults to 14.

    Returns:
        figure: matplotlib figure (if created)
        axis: matplotlib axis
    """

    engine_name = _get_engine_name(engine, ax=ax)
    extent = tuple(float(x) for x in extent)
    if padding:
        extent = pad_extent(extent, padding)
    backend = _get_backend(engine_name)

    ctx = backend.create_axes(extent, proj, data_proj, ax, figsize, coast, basemap_kwargs)
    fig, ax, fig_init = ctx["fig"], ctx["ax"], ctx["fig_init"]
    coast = ctx["coast"]

    _flag_axes(ax, engine_name, extent, basemap_obj=ctx["basemap_obj"])
    _bind_escape_hatch_methods(ax, engine_name, basemap_obj=ctx["basemap_obj"])

    if features:
        add_features(
            ax,
            edgecolor=edgecolor,
            landcolor=landcolor,
            oceancolor=oceancolor,
            coast=coast,
            zorder=zorder,
            engine=engine_name,
        )

    if bathymetry:
        if "contour" in bathymetry_method or bathymetry_method == "banded":
            bathy_zorder_add = 99
        elif "topofull" in bathymetry_method:
            bathy_zorder_add = 20
        else:
            bathy_zorder_add = 5
        bargs = {
            "levels": isobaths,
            "zorder": zorder + bathy_zorder_add,
            "method": bathymetry_method,
            "colors": bathymetry_colors,
            "legend_scale": bathymetry_legend_scale,
            "engine": engine_name,
        }
        if ctx["data_crs"] is not None:
            bargs["transform"] = ctx["data_crs"]
        bathy = get_bathymetry(extent) if bathymetry_file is None else get_bathymetry(extent, source=bathymetry_file)
        add_bathymetry(
            ax,
            bathy["longitude"].data,
            bathy["latitude"].data,
            bathy["z"].data,
            **bargs,
        )

    if ticks:
        tick_dict = {
            "label_left": tick_label_left,
            "label_right": tick_label_right,
            "label_bottom": tick_label_bottom,
            "label_top": tick_label_top,
            "gridlines": gridlines,
            "decimal_degrees": decimal_degrees,
            "whole_degree_majors": whole_degree_majors,
            "engine": engine_name,
        }
        if ctx["data_crs"] is not None:
            tick_dict["proj"] = ctx["data_crs"]
        add_ticks(ax, extent, **tick_dict)
    elif gridlines:
        backend.fallback_gridlines(ax, extent)

    if xlabel:
        ax.set_xlabel(xlabel if isinstance(xlabel, str) else "Longitude", fontsize=labelsize, fontweight="bold")
    if ylabel:
        ax.set_ylabel(ylabel if isinstance(ylabel, str) else "Latitude", fontsize=labelsize, fontweight="bold")
    if title:
        ax.set_title(title, fontsize=titlesize, fontweight="bold")

    if fig_init:
        return fig, ax
    return ax


def export_fig(path, fname, dpi=150, script=None):
    """
    Save figure with minimal whitespace.
    Include script to print the script that created the plot for future ref.

    Args:
        path (str or Path): Path to which you want to export figure
        fname (str): Filename you want to export the figure as
        dpi (int, optional): Dots per inch. Defaults to 150.
        script (str, optional): Print name of script on plot. Defaults to None.
    """

    if isinstance(path, str):
        path = Path(path)

    os.makedirs(path, exist_ok=True)

    if script:
        import datetime as dt

        now = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        plt.figtext(0.98, 0.20, f"{script} {now}", fontsize=10, rotation=90)

    plt.savefig(path / fname, dpi=dpi, bbox_inches="tight", pad_inches=0.1)


def show_figure(fig):
    dummy = plt.figure()
    new_manager = dummy.canvas.manager
    new_manager.canvas.figure = fig
    fig.set_canvas(new_manager.canvas)


def load_fig(figfile):
    """
    Load pickled figure

    Args:
        figdir (path): Full file path to pickled figure

    Note:
        Axes produced by create() carry instance-bound escape-hatch methods
        (see _bind_escape_hatch_methods) and, for the basemap engine, a live
        Basemap object attached as an attribute; neither generally survives a
        pickle round-trip (bound closures aren't stdlib-picklable, and Basemap
        objects have known pyproj/GEOS pickling limitations). Axes reloaded via
        this function should be treated as plain matplotlib axes, not as
        re-instrumented cool_maps axes.

    Returns:
        object: matplotlib figure
    """

    with open(figfile, "rb") as file:
        fig = pickle.load(file)
    show_figure(fig)
    ax = fig.axes
    return fig, ax


def save_fig(fig, figdir, figname):
    """
    Save figure as pickle file

    Args:
        fig (matplotlib.Figure): matplotlib figure
        figdir (path): Path to save pickled figure to
        figname (str): Filename to save pickled figure as

    Note:
        See load_fig() -- engine-specific instrumentation on the figure's axes
        (escape-hatch methods, attached Basemap objects) is not guaranteed to
        survive pickling.
    """
    if isinstance(figdir, str):
        figdir = Path(figdir)

    os.makedirs(figdir, exist_ok=True)

    fullfile = figdir / figname

    with open(fullfile, "wb") as file:
        pickle.dump(fig, file)


if __name__ == "__main__":
    extent = (-90.0, -15.5, 0.0, 48.0)
    fig, ax = create(extent)
    plt.show()
