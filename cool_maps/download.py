from erddapy import ERDDAP

def get_bathymetry(extent=(-100, -45, 5, 46),
                   server="https://hfr.marine.rutgers.edu/erddap/",
                   dataset_id="bathymetry_srtm15_v24"
                   ):
    """
    Function to select bathymetry within a bounding box.
    This function pulls GEBCO 2014 bathy data from hfr.marine.rutgers.edu 

    Args:
        extent (tuple, optional): Cartopy bounding box. Defaults to (-100, -45, 5, 46).

    Returns:
        xarray.Dataset: xarray Dataset containing bathymetry data
    """
    lons = extent[:2]
    lats = extent[2:]

    e = ERDDAP(
        server=server,
        protocol="griddap"
    )

    e.dataset_id = dataset_id

    e.griddap_initialize()

    # Modify constraints
    e.constraints["latitude<="] = max(lats)
    e.constraints["latitude>="] = min(lats)
    e.constraints["longitude>="] = max(lons)
    e.constraints["longitude<="] = min(lons)

    # return xarray dataset
    return e.to_xarray()