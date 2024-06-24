from erddapy import ERDDAP
import os
import xarray as xr
import pandas as pd
import numpy as np
from cool_maps.calc import haversine_dist

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


def get_deployment_list(source='rutgers',
                        search_term=None, 
                        extent=None, 
                        t0=None, 
                        t1=None):
    """
    Get list of deployments on ERDDAP matching constraints and search criteria

    Args:
        source (str): server to work with ('rutgers' or 'dac', default rutgers)
        search_term (str): search term (default None)
        extent (tuple, optional): Cartopy bounding box. Defaults to None.
        t0 (str): start time for search bounds
        t1 (str): end time for search bounds
    
    Returns:
        list of deployments on server matching search criteria
    """
    if source.lower()=='rutgers':
        e = ERDDAP(server='http://slocum-data.marine.rutgers.edu/erddap', protocol='tabledap')
    elif source.lower()=='dac':
        e = ERDDAP(server='http://gliders.ioos.us/erddap', protocol='tabledap')
    else:
        print(f'Source {source} not recognized. Please choose from rutgers or dac.')
        return 1
    search_bounds = {}
    if extent:
        search_bounds['min_lon'] = extent[0]
        search_bounds['max_lon'] = extent[1]
        search_bounds['min_lat'] = extent[2]
        search_bounds['max_lat'] = extent[3]
    if t0:
        search_bounds['min_time'] = pd.to_datetime(t0).strftime('%Y-%m-%dT%H:%M:%SZ')
    if t1:
        search_bounds['min_time'] = pd.to_datetime(t1).strftime('%Y-%m-%dT%H:%M:%SZ')
    glider_url = e.get_search_url(search_for=search_term, response='csv', **search_bounds)
    try:
        glider_datasets = pd.read_csv(glider_url)['Dataset ID']
        glider_datasets=pd.DataFrame({'dataset': glider_datasets, 'deployment': pd.Series(dtype='str')})
        if source=='rutgers':
            for i in glider_datasets.index:
                glider_datasets['deployment'][i]='-'.join(glider_datasets['dataset'][i].split('-')[:-3])
        if source=='dac':
            for i in glider_datasets.index:
                glider_datasets['deployment'][i]=glider_datasets['dataset'][i].replace('-delayed','')
        return list(np.unique(glider_datasets['deployment']))
    except:
        print('No matching deployments found.')
        return []


def get_deployment_path(deployment,
                        nProfiles_rutgers_rt=False,
                        nProfiles_rutgers_delayed=False,
                        nProfiles_rutgers_best=False,
                        nProfiles_dac_rt=False,
                        nProfiles_dac_delayed=False,
                        nProfiles_dac_best=False,
                        distance_flown=False):
    """
    Get full path (lon/lat) for a given deployment. Checks Rutgers ERDDAP and IOOS DAC ERDDAP.
    
    Args:
        - deployment (str): name of deployment, format GLIDER-YYYYMMDDTHHMM
        - nProfiles_rutgers_rt (bool): count number of real-time profiles served on Rutgers ERDDAP (if available, default False)
        - nProfiles_rutgers_delayed (bool): count number of delayed-mode profiles served on Rutgers ERDDAP (if available, default False)
        - nProfiles_rutgers_best (bool): count number of delayed-mode profiles served on Rutgers ERDDAP, or number of real-time profiles if delayed-mode is not available (if available, default False)
        - nProfiles_dac_rt (bool): count number of real-time profiles served on DAC ERDDAP (if available, default False)
        - nProfiles_dac_delayed (bool): count number of delayed-mode profiles served on DAC ERDDAP (if available, default False)
        - nProfiles_dac_best (bool): count number of delayed-mode profiles served on DAC ERDDAP, or number of real-time profiles if delayed-mode is not available (if available, default False)
        - distance_flown (bool): calculate the distance flown based on downloaded path using haversine_dist function
    
    Returns:
        - pandas Dataframe with sorted time, latitude, longitude
        - dictionary with number profiles and distance flown, if calculated
    """
    deployment_info = {'rutgers_rt_profiles': np.nan, 'rutgers_delayed_profiles': np.nan, 
                       'dac_rt_profiles': np.nan, 'dac_delayed_profiles': np.nan, 
                       'km_flown': np.nan}
    rutgers_datasets = []
    dac_datasets = []
    vars = ['time', 'lon', 'lat']

    eru = ERDDAP(server='http://slocum-data.marine.rutgers.edu/erddap', protocol='tabledap')
    glider_url = eru.get_search_url(search_for=deployment, response='csv')
    try:
        rutgers_datasets = list(pd.read_csv(glider_url)['Dataset ID'])
    except:
        rutgers_datasets = []
    if len(rutgers_datasets)==0 or nProfiles_dac_best or nProfiles_dac_delayed or nProfiles_dac_rt:
        edac = ERDDAP(server='http://gliders.ioos.us/erddap', protocol='tabledap')
        glider_url = edac.get_search_url(search_for=deployment, response='csv')
        try:
            dac_datasets = list(pd.read_csv(glider_url)['Dataset ID'])
        except:
            dac_datasets = []
            if len(rutgers_datasets)==0:
                print(f'Unable to find {deployment} on Rutgers or IOOS DAC servers.')
                return 1
            
    glider_traj=pd.DataFrame()
    if 'trajectory' in ','.join(rutgers_datasets):
        if f'{deployment}-trajectory-raw-delayed' in rutgers_datasets:
            eru.dataset_id = f'{deployment}-trajectory-raw-delayed'
        elif f'{deployment}-trajectory-raw-rt' in rutgers_datasets:
            eru.dataset_id = f'{deployment}-trajectory-raw-rt'
        eru.constraints = {'m_gps_lat<': 10000}
        eru.variables = ['time', 'longitude', 'latitude']
        glider_traj = eru.to_pandas()
        for v in vars:
            vi = [i for i in glider_traj.columns if v.lower() in i.lower()]
            if len(vi)==1:
                glider_traj = glider_traj.rename(columns={vi[0]: v})
        glider_traj = glider_traj.rename(columns={'lon': 'longitude', 'lat': 'latitude'})

    if 'profile' in ','.join(rutgers_datasets) and (len(glider_traj)==0 or nProfiles_rutgers_best or nProfiles_rutgers_delayed or nProfiles_rutgers_rt):
        if f'{deployment}-profile-sci-delayed' in rutgers_datasets and (len(glider_traj)==0 or nProfiles_rutgers_best or nProfiles_rutgers_delayed):
            eru.dataset_id = f'{deployment}-profile-sci-delayed'
            eru.constraints = {}
            eru.variables = ['profile_time', 'profile_lon', 'profile_lat']
            data = eru.to_pandas(distinct=True)
            for v in vars:
                vi = [i for i in data.columns if v.lower() in i.lower()]
                if len(vi)==1:
                    data = data.rename(columns={vi[0]: v})
            data = data.rename(columns={'lon': 'longitude', 'lat': 'latitude'})
            if len(glider_traj)==0:
                glider_traj = data.copy()
            deployment_info['rutgers_delayed_profiles'] = len(data)
            nProfiles_rutgers_best = False
        if f'{deployment}-profile-sci-rt' in rutgers_datasets and (len(glider_traj)==0 or nProfiles_rutgers_best or nProfiles_rutgers_rt):
            eru.dataset_id = f'{deployment}-profile-sci-rt'
            eru.constraints = {}
            eru.variables = ['profile_time', 'profile_lon', 'profile_lat']
            data = eru.to_pandas(distinct=True)
            for v in vars:
                vi = [i for i in data.columns if v.lower() in i.lower()]
                if len(vi)==1:
                    data = data.rename(columns={vi[0]: v})
            data = data.rename(columns={'lon': 'longitude', 'lat': 'latitude'})
            if len(glider_traj)==0:
                glider_traj = data.copy()
            deployment_info['rutgers_rt_profiles'] = len(data)

    if len(dac_datasets)>0 and (len(glider_traj)==0 or nProfiles_dac_best or nProfiles_dac_delayed or nProfiles_dac_rt):
        if f'{deployment}-delayed' in dac_datasets and (len(glider_traj)==0 or nProfiles_dac_best or nProfiles_dac_delayed):
            edac.dataset_id = f'{deployment}-delayed'
            edac.constraints = {}
            edac.variables = ['time', 'longitude', 'latitude']
            data = edac.to_pandas(distinct=True)
            for v in vars:
                vi = [i for i in data.columns if v.lower() in i.lower()]
                if len(vi)==1:
                    data = data.rename(columns={vi[0]: v})
            data = data.rename(columns={'lon': 'longitude', 'lat': 'latitude'})
            if len(glider_traj)==0:
                glider_traj = data.copy()
            deployment_info['dac_delayed_profiles'] = len(data)
            nProfiles_dac_best = False
        if deployment in dac_datasets and (len(glider_traj)==0 or nProfiles_dac_best or nProfiles_dac_rt):
            edac.dataset_id = deployment
            edac.constraints = {}
            edac.variables = ['time', 'longitude', 'latitude']
            data = edac.to_pandas(distinct=True)
            for v in vars:
                vi = [i for i in data.columns if v.lower() in i.lower()]
                if len(vi)==1:
                    data = data.rename(columns={vi[0]: v})
            data = data.rename(columns={'lon': 'longitude', 'lat': 'latitude'})
            if len(glider_traj)==0:
                glider_traj = data.copy()
            deployment_info['dac_rt_profiles'] = len(data)

    glider_traj['time'] = pd.to_datetime(glider_traj['time']) #, format='%Y-%m-%dT%H:%M:%S.%fZ')
    glider_traj = glider_traj.sort_values(by='time', ignore_index=True)

    if distance_flown:
        deployment_info['km_flown'] = haversine_dist(glider_traj['longitude'][:-1], glider_traj['latitude'][:-1],
                                                     glider_traj['longitude'][1:], glider_traj['latitude'][1:],
                                                     get_total=True)
        
    return glider_traj, deployment_info
