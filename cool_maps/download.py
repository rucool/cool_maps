import hashlib
import platform
from pathlib import Path
from typing import Tuple, Optional

import xarray as xr
import pandas as pd
import numpy as np
from erddapy import ERDDAP


def _get_cache_dir() -> Path:
    """Return the path to the cool_maps cache directory."""
    home = Path.home()
    if platform.system() == "Windows":
        cache_dir = home / "AppData" / "Local" / "cool_maps" / "Cache"
    elif platform.system() == "Darwin":
        cache_dir = home / "Library" / "Caches" / "cool_maps"
    # else:
        cache_dir = home / ".cache" / "cool_maps"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _tile_index_slices(coord_values: np.ndarray, chunk_size: Optional[float]) -> list:
    """Split a monotonic coordinate array into contiguous index slices spanning at most chunk_size each."""
    n = coord_values.size
    if chunk_size is None or n == 0:
        return [slice(0, n)]

    span = abs(float(coord_values[-1]) - float(coord_values[0]))
    if span <= chunk_size:
        return [slice(0, n)]

    n_chunks = int(np.ceil(span / chunk_size))
    edges = np.linspace(0, n, n_chunks + 1).astype(int)
    return [slice(edges[i], edges[i + 1]) for i in range(n_chunks) if edges[i] < edges[i + 1]]


def _fetch_bathymetry_tile(
    ds: xr.Dataset,
    lon_var: str,
    lat_var: str,
    elev_var: str,
    lon_slice: slice,
    lat_slice: slice,
    source: str,
    use_cache: bool,
) -> xr.Dataset:
    cache_file = None
    if use_cache and source.startswith("http"):
        lon_vals = ds[lon_var].values[lon_slice]
        lat_vals = ds[lat_var].values[lat_slice]
        hash_str = f"{source}_{lon_vals[0]}_{lon_vals[-1]}_{lat_vals[0]}_{lat_vals[-1]}_{lon_var}_{lat_var}_{elev_var}"
        cache_key = hashlib.md5(hash_str.encode()).hexdigest()
        cache_file = _get_cache_dir() / f"bathy_{cache_key}.nc"

        if cache_file.exists():
            try:
                return xr.open_dataset(cache_file)
            except Exception:
                pass # Proceed to re-download if cache is corrupted

    tile = ds.isel(**{lon_var: lon_slice, lat_var: lat_slice})
    tile = tile.rename({lon_var: 'longitude', lat_var: 'latitude', elev_var: 'z'})

    if cache_file is not None:
        try:
            # Load into memory to save as netCDF
            tile.load().to_netcdf(cache_file)
        except Exception as e:
            print(f"Warning: Failed to cache bathymetry tile: {e}")

    return tile


def get_bathymetry(
    extent: Tuple[float, float, float, float] = (-100, -45, 5, 46),
    source: str = "https://tds.marine.rutgers.edu/thredds/dodsC/other/bathymetry/GEBCO_2023/GEBCO_2023_sub_ice_topo.nc",
    lon_var: str = 'lon',
    lat_var: str = 'lat',
    elev_var: str = 'elevation',
    use_cache: bool = True,
    chunk_size: Optional[float] = 10,
) -> xr.Dataset:
    """
    Retrieves bathymetry data within a specified bounding box, either from a local NetCDF file or an OpenDAP URL.
    Allows specifying custom variable names for longitude, latitude, and elevation. Caches to disk if enabled.

    Large requests against an OpenDAP source are split into tiles no larger than chunk_size
    degrees on a side, fetched and cached individually, and stitched back together. This keeps
    each individual request under server-side response-size limits.

    Args:
        extent (tuple, optional): Bounding box (min_lon, max_lon, min_lat, max_lat). Defaults to (-100, -45, 5, 46).
        source (str, optional): Path to a local NetCDF file or OpenDAP URL. Defaults to the provided OpenDAP URL.
        lon_var (str, optional): Name of the longitude variable in the dataset. Defaults to 'lon'.
        lat_var (str, optional): Name of the latitude variable in the dataset. Defaults to 'lat'.
        elev_var (str, optional): Name of the elevation variable in the dataset. Defaults to 'elevation'.
        use_cache (bool, optional): Whether to cache OpenDAP requests locally. Defaults to True.
        chunk_size (float, optional): Maximum tile width/height in degrees for each OpenDAP request.
            Set to None to disable chunking and request the full extent in one shot. Defaults to 10.

    Returns:
        xarray.Dataset: Dataset containing the requested bathymetry data.
    """
    lons, lats = sorted(extent[:2]), sorted(extent[2:])

    if not source.startswith("http"):
        chunk_size = None # no server request-size limit to worry about for local files

    ds = xr.open_dataset(source).sel(**{lon_var: slice(*lons), lat_var: slice(*lats)})

    lon_slices = _tile_index_slices(ds[lon_var].values, chunk_size)
    lat_slices = _tile_index_slices(ds[lat_var].values, chunk_size)

    tiles = [
        _fetch_bathymetry_tile(ds, lon_var, lat_var, elev_var, lon_slice, lat_slice, source, use_cache)
        for lon_slice in lon_slices
        for lat_slice in lat_slices
    ]

    if len(tiles) == 1:
        return tiles[0]

    return xr.combine_by_coords(tiles)


def get_totals_from_erddap(
    time_start: str, 
    time_end: Optional[str] = None,
    extent: Optional[Tuple[float, float, float, float]] = None,
    server: str = "https://hfr.marine.rutgers.edu/erddap/",
    dataset_id: str = '5MHz_6km_realtime-agg_archive_v00'
) -> xr.Dataset:
    """
    Function to select HFR data within a bounding box.
    This function pulls HFR data from hfr.marine.rutgers.edu 

    Args:
        time_start (str): Start time to read.
        time_end (str, optional): End time to read. Defaults to None/latest.
        extent (tuple, optional): Cartopy bounding box. Defaults to None.
        server (str, optional): ERDDAP server URL.
        dataset_id (str, optional): ERDDAP dataset ID.

    Returns:
        xarray.Dataset: xarray Dataset containing HFR data
    """
    
    if not time_end:
        time_end = time_start

    e = ERDDAP(
        server=server,
        protocol="griddap"
    )

    e.dataset_id = dataset_id
    e.griddap_initialize()

    # Modify constraints
    if extent:
        lons = extent[:2]
        lats = extent[2:]
        e.constraints["latitude<="] = max(lats)
        e.constraints["latitude>="] = min(lats)
        e.constraints["longitude>="] = max(lons)
        e.constraints["longitude<="] = min(lons)

    e.constraints["time<="] = time_start
    e.constraints["time>="] = time_end
        
    return e.to_xarray()


def get_glider_bathymetry(
    deployment: str,
    time_start: Optional[str] = None,
    time_end: Optional[str] = None
) -> Optional[pd.DataFrame]:
    """
    Function to select bathymetry associated with a glider deployment.
    This function pulls glider-measured bathymetry data from slocum-data.marine.rutgers.edu and removes spikes.

    Args:
        deployment (str): Name of deployment to get bathymetry for (glider-yyyymmddTHHMM).
        time_start (str, optional): Start time. Defaults to None/beginning of deployment.
        time_end (str, optional): End time. Defaults to None/end of deployment.

    Returns:
        pandas.DataFrame: pandas DataFrame containing bathymetry data, or None if failed.
    """
    
    ru_erddap = ERDDAP(server='http://slocum-data.marine.rutgers.edu/erddap', protocol='tabledap')
    glider_url = ru_erddap.get_search_url(search_for=f'{deployment}-trajectory', response='csv')
    
    try:
        glider_datasets = pd.read_csv(glider_url)['Dataset ID']
        if glider_datasets.empty:
            raise ValueError(f"No datasets found matching '{deployment}'.")
    except Exception as e:
        raise ValueError(f"Unable to access deployment {deployment}. Error: {e}")

    ru_erddap.dataset_id = glider_datasets[0]
    ru_erddap.constraints = {'m_water_depth>': 2}
    if time_start:
        ru_erddap.constraints["time<="] = time_start
    if time_end:
        ru_erddap.constraints["time>="] = time_end
    ru_erddap.variables = ['time', 'm_water_depth']
    
    try:
        glider_bathy = ru_erddap.to_pandas()
    except Exception as e:
        raise RuntimeError(f"Failed to download glider bathymetry: {e}")
        
    glider_bathy.columns = ['time', 'water_depth']
    glider_bathy['time'] = pd.to_datetime(glider_bathy['time'])
    glider_bathy = glider_bathy.sort_values(by='time').reset_index(drop=True)
    
    # Vectorized spike removal
    time_diff_sec = glider_bathy['time'].diff().dt.total_seconds()
    depth_diff = glider_bathy['water_depth'].diff()
    
    # Backward and forward derivatives
    d1 = depth_diff / time_diff_sec
    d2 = depth_diff.shift(-1) / time_diff_sec.shift(-1)
    
    # Max absolute derivative
    d_max = np.maximum(d1.abs(), d2.abs())
    
    # Filter spikes where derivative is smaller than 0.2
    glider_bathy = glider_bathy[d_max < 0.2][['time', 'water_depth']].reset_index(drop=True)
    
    return glider_bathy
