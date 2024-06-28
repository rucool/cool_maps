from erddapy import ERDDAP
import os
import xarray as xr
import pandas as pd
import numpy as np

def get_bathymetry(extent=(-100, -45, 5, 46),
                   server="https://hfr.marine.rutgers.edu/erddap/",
                   dataset_id="bathymetry_srtm15_v24",
                   file=None
                   ):
    """
    Function to select bathymetry within a bounding box.
    This function pulls GEBCO 2014 bathy data from hfr.marine.rutgers.edu 
    OR from multi-source elevation/bathy data from CF compliant NetCDF file downloaded from https://www.gmrt.org/GMRTMapTool/

    Args:
        extent (tuple, optional): Cartopy bounding box. Defaults to (-100, -45, 5, 46).
        file (str filename, optional): CF Compliant NetCDF file containing GMRT bathymetry
                                       if None (default) or if file is not found, will default to ERDDAP

    Returns:
        xarray.Dataset: xarray Dataset containing bathymetry data
    """
    lons = extent[:2]
    lats = extent[2:]

    if file and os.path.isfile(file):
        bathy = xr.open_dataset(file)
        bathy = bathy.sel(lon=slice(min(lons), max(lons)))
        bathy = bathy.sel(lat=slice(min(lats), max(lats)))
        bathy = bathy.rename({'lon':'longitude','lat':'latitude','altitude':'z'})
        return bathy

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

def get_totals_from_erddap(time_start, 
                           time_end=None,
                           extent=None,
                           server="https://hfr.marine.rutgers.edu/erddap/",
                           dataset_id='5MHz_6km_realtime-agg_archive_v00'):
    """
    Function to select HFR data within a bounding box.
    This function pulls GEBCO 2014 bathy data from hfr.marine.rutgers.edu 

    Args:
        time_start (str): Start time to read.
        time_end (str, optional): End time to read. Defaults to None/latest.
        extent (tuple, optional): Cartopy bounding box. Defaults to None.

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
        # e.constraints["time="] = time

    # if time_end:
    e.constraints["time<="] = time_start
    e.constraints["time>="] = time_end
        
    # return xarray dataset
    return e.to_xarray()

def get_glider_bathymetry(deployment,
                          time_start=None,
                          time_end=None):
    """
    Function to select bathymetry associated with a glider deployment.
    This function pulls glider-measured bathymetry data from slocum-data.marine.rutgers.edu and removes spikes

    Args:
        deployment (str): Name of deployment to get bathymetry for (glider-yyyymmddTHHMM)
        time_start (str, optional): Start time. Defaults to None/beginning of deployment
        time_end (str, optional): End time. Defaults to None/end of deployment

    Returns:
        pandas.DataFrame: pandas DataFrame containing bathymetry data
    """
    
    ru_erddap = ERDDAP(server='http://slocum-data.marine.rutgers.edu/erddap', protocol='tabledap')
    glider_url = ru_erddap.get_search_url(search_for=f'{deployment}-trajectory', response='csv')
    try:
        glider_datasets = pd.read_csv(glider_url)['Dataset ID']
    except:
        print(f'Unable to access deployment {deployment}. Check for typos.')
        return None

    ru_erddap.dataset_id = glider_datasets[0]
    ru_erddap.constraints = {'m_water_depth>': 2}
    if time_start:
        ru_erddap.constraints["time<="] = time_start
    if time_end:
        ru_erddap.constraints["time>="] = time_end
    ru_erddap.variables = ['time', 'm_water_depth']
    glider_bathy = ru_erddap.to_pandas()
    glider_bathy.columns=['time', 'water_depth']
    glider_bathy['time']=pd.to_datetime(glider_bathy['time'])
    glider_bathy = glider_bathy.sort_values(by='time')
    glider_bathy['d1']=np.nan
    glider_bathy['d2']=np.nan
    glider_bathy.loc[:,'d1']=np.append(np.divide((np.array(glider_bathy['water_depth'][1:]) - np.array(glider_bathy['water_depth'][:len(glider_bathy)-1])), (np.array(glider_bathy['time'][1:].astype('int64')//1e9) - np.array(glider_bathy['time'][:len(glider_bathy)-1].astype('int64')//1e9))), np.nan)
    glider_bathy.loc[1:,'d2']=np.divide((np.array(glider_bathy['water_depth'][1:]) - np.array(glider_bathy['water_depth'][:len(glider_bathy)-1])), np.array(glider_bathy['time'][1:].astype('int64')//1e9) - np.array(glider_bathy['time'][:len(glider_bathy)-1].astype('int64')//1e9))
    glider_bathy['d']=np.max(np.abs(glider_bathy[['d1','d2']]), axis=1)
    glider_bathy=glider_bathy[glider_bathy['d']<.2][['time','water_depth']]
    
    return glider_bathy
