import os
import pickle
import warnings
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cmocean
import matplotlib.colors
import matplotlib.pyplot as plt
import numpy as np
from erddapy import ERDDAP
from oceans.ocfis import spdir2uv, uv2spdir

# Suppresing warnings for a "pretty output."
warnings.simplefilter("ignore")

# Default projection information in case user does not pass
proj = dict(
    map=ccrs.Mercator(), # the projection that you want the map to be in
    data=ccrs.PlateCarree() # the projection that the data is. 
    )

def add_bathymetry(ax, lon, lat, elevation,
                   levels=(-1000),
                   zorder=5,
                   transform=proj['data'], 
                   transform_first=False):
    """
    Plot bathymetry lines on map

    Args:
        ax (matplotlib.axes): matplotlib axes
        lon (array-like): bathymetry longitudes
        lat (array-like): bathymetry latitudes
        elevation (array-like): bathymetry elevation data
        levels (tuple, optional): 
            Determines the number and positions of the contour lines / regions. Defaults to (-1000).
        zorder (int, optional): Drawing order for this function on the axes. Defaults to 5.
        transform (_type_, optional): Tells Cartopy what coordinate system your data are defined in. Defaults to crs.PlateCarree().
        transform_first (bool, optional): 
            Indicate that Cartopy points should be transformed before calling the contouring algorithm, which can have a significant impact on speed (it is much faster to transform points than it is to transform patches). Defaults to False.
    """
    lons, lats = np.meshgrid(lon, lat)
    h = ax.contour(lons, lats, elevation, levels, 
                    linewidths=.75, alpha=.5, colors='k', 
                    transform=transform, 
                    transform_first=transform_first, # May speed plotting up
                    zorder=zorder)
    ax.clabel(h, levels, inline=True, fontsize=6, fmt=fmt)


def add_currents(ax, ds, 
                 coarsen=2,
                 scale=90, 
                 headwidth=2.75, 
                 headlength=2.75, 
                 headaxislength=2.5):
    """
    Plot currents on map

    Args:
        ax (matplotlib.axes): matplotlib axes
        ds (xarray.Dataset): xarray dataset containing lon, lat, u, and v data.
        coarsen (bool, optional): Coarsen object (downsampling). Defaults to 2.
        scale (float, optional): Number of data units per arrow length unit, e.g., m/s per plot width; a smaller scale parameter makes the arrow longer.. Defaults to 90.
        headwidth (float, optional): Head width as multiple of shaft width. Defaults to 2.75.
        headlength (float, optional): Head length as multiple of shaft width. Defaults to 2.75.
        headaxislength (float, optional): Head length at shaft intersection. Defaults to 2.5.

    Returns:
        object: Quiver
    """

    try:
        qds = ds.coarsen(lon=coarsen, boundary='pad').mean().coarsen(lat=coarsen, boundary='pad').mean()
        mesh = True
    except ValueError:
        qds = ds.coarsen(x=coarsen, boundary='pad').mean().coarsen(y=coarsen, boundary='pad').mean()
        mesh = False

    angle, speed = uv2spdir(qds['u'], qds['v'])  # convert u/v to angle and speed
    u, v = spdir2uv(  # convert angle and speed back to u/v, normalizing the arrow sizes
        np.ones_like(speed),
        angle,
        deg=True
    )

    qargs = {}
    qargs['scale'] = scale
    qargs['headwidth'] = headwidth
    qargs['headlength'] = headlength
    qargs['headaxislength'] = headaxislength
    qargs['transform'] = ccrs.PlateCarree()

    if mesh:
        lons, lats = np.meshgrid(qds['lon'], qds['lat'])
        q = ax.quiver(lons, lats, u, v, **qargs)
    else:
        q = ax.quiver(qds.lon.squeeze().data, qds.lat.squeeze().data, u.squeeze(), v.squeeze(), **qargs)
    return q


def add_features(ax, extent, 
                 edgecolor="black", 
                 landcolor="tan",
                 oceancolor=cfeature.COLORS['water'],
                 zorder=0):
    """
    Automatically add the following features to make the map nicer looking.
    
    Adjust axis limits to extent.
    Set land color.
    Add rivers, lakes, state lines, and other borders.

    Args:
        ax (matplotlib.Axis): matplotlib axis
        extent (tuple or list): extent (x0, x1, y0, y1) of the map in the given coordinate system.
        edgecolor (str, optional): Color of edges of polygons. Defaults to "black".
        landcolor (str, optional): Color of land. Defaults to "tan".
        zorder (int, optional): Drawing order for this function on the axes. Defaults to 0.
    """
    state_lines = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='50m',
        facecolor='none'
    )

    LAND = cfeature.GSHHSFeature(scale='full')

    # Axes properties and features
    ax.set_extent(extent)
    # ax.add_feature(cfeature.OCEAN, zorder=zorder) #cfeature.OCEAN has a major performance hit
    ax.set_facecolor(oceancolor) # way faster than adding the ocean feature above
    ax.add_feature(LAND, 
                   edgecolor=edgecolor, 
                   facecolor=landcolor,
                   zorder=zorder+10)
    ax.add_feature(cfeature.RIVERS, zorder=zorder+10.2)
    ax.add_feature(cfeature.LAKES, zorder=zorder+10.2, alpha=0.5)
    ax.add_feature(state_lines, edgecolor=edgecolor, zorder=zorder+10.3)
    ax.add_feature(cfeature.BORDERS, linestyle='--', zorder=zorder+10.3)


def add_legend(ax):
    """
    Add legend to your map.

    Args:
        ax (matplotlib.Axis): matplotlib Axis

    Returns:
        object: legend handle
    """
    # Shrink current axis by 20%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    leg = ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    return leg


def add_ticks(ax, extent, fontsize=13):
    """
    Calculate and add nicely formatted ticks to your map

    Args:
        ax (matplotlib.Axis): matplotlib Axis
        extent (tuple or list): extent (x0, x1, y0, y1) of the map in the given coordinate system.
        fontsize (int, optional): Font size of tick labels. Defaults to 13.
    """
    xl = [extent[0], extent[1]]
    yl = [extent[2], extent[3]]

    tick0x, tick1, ticklab = get_ticks(xl, 'we', yl)
    ax.set_xticks(tick0x, minor=True, crs=ccrs.PlateCarree())
    ax.set_xticks(tick1, crs=ccrs.PlateCarree())
    ax.set_xticklabels(ticklab, fontsize=fontsize)

    # get and add latitude ticks/labels
    tick0y, tick1, ticklab = get_ticks(yl, 'sn', xl)
    ax.set_yticks(tick0y, minor=True, crs=ccrs.PlateCarree())
    ax.set_yticks(tick1, crs=ccrs.PlateCarree())
    ax.set_yticklabels(ticklab, fontsize=fontsize)

    # gl = ax.gridlines(draw_labels=False, linewidth=.5, color='gray', alpha=0.75, linestyle='--', crs=ccrs.PlateCarree())
    # gl.xlocator = mticker.FixedLocator(tick0x)
    # gl.ylocator = mticker.FixedLocator(tick0y)

    ax.tick_params(which='major',
                   direction='out',
                   bottom=True, top=True,
                   labelbottom=True, labeltop=False,
                   left=True, right=True,
                   labelleft=True, labelright=False,
                   length=5, width=2)

    ax.tick_params(which='minor',
                   direction='out',
                   bottom=True, top=True,
                   labelbottom=True, labeltop=False,
                   left=True, right=True,
                   labelleft=True, labelright=False,
                   width=1)


def categorical_cmap(nc, nsc, cmap="tab10", continuous=False):
    """
    Expand your colormap by changing the alpha value of each color.
    
    Returns a colormap with nc*nsc different colors, 
    where for each category there are nsc colors of same hue.
    
    
    From ImportanceOfBeingErnest
    https://stackoverflow.com/a/47232942/2643708
    
    Args:
        nc (int): number of categories (colors)
        nsc (int): number of subcategories (shades for each color)
        cmap (str, optional): matplotlib colormap. Defaults to "tab10".
        continuous (bool, optional): _description_. Defaults to False.

    Raises:
        ValueError: Too many categories for colormap

    Returns:
        object: matplotlib colormap
    """

    if nc > plt.get_cmap(cmap).N:
        raise ValueError("Too many categories for colormap.")
    if continuous:
        ccolors = plt.get_cmap(cmap)(np.linspace(0,1,nc))
    else:
        ccolors = plt.get_cmap(cmap)(np.arange(nc, dtype=int))
    cols = np.zeros((nc*nsc, 3))
    for i, c in enumerate(ccolors):
        chsv = matplotlib.colors.rgb_to_hsv(c[:3])
        arhsv = np.tile(chsv,nsc).reshape(nsc,3)
        arhsv[:,1] = np.linspace(chsv[1],0.25,nsc)
        arhsv[:,2] = np.linspace(chsv[2],1,nsc)
        rgb = matplotlib.colors.hsv_to_rgb(arhsv)
        cols[i*nsc:(i+1)*nsc,:] = rgb
    cmap = matplotlib.colors.ListedColormap(cols)
    return cmap


def cmaps(variable):
    """
    Pre-defined colormaps for oceanographic variables utilizing cmocean.

    Args:
        variable (str): variable you are plotting

    Returns:
        object: matplotlib colormap
    """
    if variable == 'salinity':
        cmap = cmocean.cm.haline
    elif variable == 'temperature':
        cmap = cmocean.cm.thermal
    elif variable == 'sea_surface_height':
        cmap = cmocean.cm.balance
    return cmap


def create(extent, 
           proj=ccrs.Mercator(),
           labelsize=14,
           ticks=True,
           features=True, 
           edgecolor="black", 
           landcolor="tan",
           oceancolor=cfeature.COLORS['water'],
           bathymetry=False,
           isobaths=(-1000, -100),
           ax=None,
           figsize=(11,8)):
    """
    Create a cartopy map within a certain extent. 

    Args:
        extent (tuple or list): Extent (x0, x1, y0, y1) of the map in the given coordinate system.
        proj (cartopy.crs class, optional): Define a projected coordinate system with flat topology and Euclidean distance. Defaults to ccrs.Mercator().
        labelsize (int, optional): Font size for axis labels. Defaults to 14.
        ticks (bool, optional): Calculate appropriately spaced ticks. Defaults to True.
        features (bool, optional): Add preferred map settings: colors, rivers, lakes, etc.. Defaults to True.
        edgecolor (str, optional): Color of edges of polygons. Defaults to "black".
        landcolor (str, optional): Color of land. Defaults to "tan".
        bathymetry (bool, optional): Download and plot bathymetry on map. Defaults to False.
        isobaths (tuple or list, optional): Elevation at which to create bathymetric contour lines. Defaults to (-1000, -100)
        ax (matplotlib.Axis, optional): Pass matplotlib axis to function. Not necessary if plotting to subplot.. Defaults to None.
        figsize (tuple, optional): (width, height) of the figure. Defaults to (11,8).

    Returns:
        figure: matplotlib figure
        axis: matplotlib axis
    """

    # If a matplotlib axis is not passed, create a new cartopy/mpl figure
    if not ax:
        fig_init = True
        fig, ax = plt.subplots(
            figsize=figsize, #12,9
            subplot_kw=dict(projection=proj)
        )

    # Make the map pretty
    if features:
        fargs = {
            "edgecolor": edgecolor,
            "landcolor": landcolor,
            "oceancolor": oceancolor
            }
        add_features(ax, extent, **fargs)
    else:
        # Axes properties and features
        ax.set_extent(extent)

    # Add bathymetry
    if bathymetry:
        bargs = {
            "levels": isobaths,
            "zorder": 1.5,
        }
        bathy = get_bathymetry(extent)
        add_bathymetry(ax, bathy['longitude'], bathy['latitude'], bathy['elevation'], **bargs)

    # Add ticks
    if ticks:
        add_ticks(ax, extent)

    # Set labels
    ax.set_xlabel('Longitude', fontsize=labelsize, fontweight='bold')
    ax.set_ylabel('Latitude', fontsize=labelsize, fontweight='bold')

    # If we generate a figure in this function, we have to return the figure
    # and axis to the calling function.
    if fig_init:
        return fig, ax


# decimal degrees to degree-minute-second converter
def dd2dms(vals):
    n = np.empty(np.shape(vals))
    n[:] = False
    n[vals < 0] = True
    vals[n == True] = -vals[n == True]
    d = np.floor(vals)
    rem = vals - d
    rem = rem * 60
    m = np.floor(rem)
    rem -= m
    s = np.round(rem * 60)
    d[n == True] = -d[n == True]
    return d, m, s


def export_fig(path, fname, script=None, dpi=150):
    """
    Helper function to save a figure with some nice formatting.
    Include script to print the script that created the plot for future ref.

    Args:
        path (str or Path): Path to which you want to export figure
        fname (str): Filename you want to export the figure as
        script (str, optional): Print name of script on plot. Defaults to None.
        dpi (int, optional): Dots per inch. Defaults to 150.
    """
    
    if isinstance(path, str):
        path = Path(path)
    
    os.makedirs(path, exist_ok=True)
    
    if script:
        import datetime as dt
        now = dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        plt.figtext(.98, 0.20, f"{script} {now}",  fontsize=10, rotation=90)
        
    plt.savefig(path / fname, dpi=dpi, bbox_inches='tight', pad_inches=0.1)

    
def fmt(x):
    s = f"{x:.1f}"
    if s.endswith("0"):
        s = f"{x:.0f}"
    return rf"{s}"


def get_bathymetry(extent=(-100, -45, 5, 46)):
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
        server="https://hfr.marine.rutgers.edu/erddap/",
        protocol="griddap"
    )

    e.dataset_id = "bathymetry_gebco_2014_grid"

    e.griddap_initialize()

    # Modify constraints
    e.constraints["latitude<="] = max(lats)
    e.constraints["latitude>="] = min(lats)
    e.constraints["longitude>="] = max(lons)
    e.constraints["longitude<="] = min(lons)

    # return xarray dataset
    return e.to_xarray()


# function to define major and minor tick locations and major tick labels
def get_ticks(bounds, dirs, otherbounds):
    dirs = dirs.lower()
    l0 = np.float(bounds[0])
    l1 = np.float(bounds[1])
    r = np.max([l1 - l0, np.float(otherbounds[1]) - np.float(otherbounds[0])])
    if r <= 1.5:
        # <1.5 degrees: 15' major ticks, 5' minor ticks
        minor_int = 1.0 / 12.0
        major_int = 1.0 / 4.0
    elif r <= 3.0:
        # <3 degrees: 30' major ticks, 10' minor ticks
        minor_int = 1.0 / 6.0
        major_int = 0.5
    elif r <= 7.0:
        # <7 degrees: 1d major ticks, 15' minor ticks
        minor_int = 0.25
        major_int = np.float(1)
    elif r <= 15:
        # <15 degrees: 2d major ticks, 30' minor ticks
        minor_int = 0.5
        major_int = np.float(2)
    elif r <= 30:
        # <30 degrees: 3d major ticks, 1d minor ticks
        minor_int = np.float(1)
        major_int = np.float(3)
    else:
        # >=30 degrees: 5d major ticks, 1d minor ticks
        minor_int = np.float(1)
        major_int = np.float(5)

    minor_ticks = np.arange(np.ceil(l0 / minor_int) * minor_int, np.ceil(l1 / minor_int) * minor_int + minor_int,
                            minor_int)
    minor_ticks = minor_ticks[minor_ticks <= l1]
    major_ticks = np.arange(np.ceil(l0 / major_int) * major_int, np.ceil(l1 / major_int) * major_int + major_int,
                            major_int)
    major_ticks = major_ticks[major_ticks <= l1]

    if major_int < 1:
        d, m, s = dd2dms(np.array(major_ticks))
        if dirs == 'we' or dirs == 'ew' or dirs == 'lon' or dirs == 'long' or dirs == 'longitude':
            n = 'W' * sum(d < 0)
            p = 'E' * sum(d >= 0)
            dir = n + p
            major_tick_labels = [str(np.abs(int(d[i]))) + u"\N{DEGREE SIGN}" + str(int(m[i])) + "'" + dir[i] for i in
                                 range(len(d))]
        elif dirs == 'sn' or dirs == 'ns' or dirs == 'lat' or dirs == 'latitude':
            n = 'S' * sum(d < 0)
            p = 'N' * sum(d >= 0)
            dir = n + p
            major_tick_labels = [str(np.abs(int(d[i]))) + u"\N{DEGREE SIGN}" + str(int(m[i])) + "'" + dir[i] for i in
                                 range(len(d))]
        else:
            major_tick_labels = [str(int(d[i])) + u"\N{DEGREE SIGN}" + str(int(m[i])) + "'" for i in range(len(d))]
    else:
        d = major_ticks
        if dirs == 'we' or dirs == 'ew' or dirs == 'lon' or dirs == 'long' or dirs == 'longitude':
            n = 'W' * sum(d < 0)
            p = 'E' * sum(d >= 0)
            dir = n + p
            major_tick_labels = [str(np.abs(int(d[i]))) + u"\N{DEGREE SIGN}" + dir[i] for i in range(len(d))]
        elif dirs == 'sn' or dirs == 'ns' or dirs == 'lat' or dirs == 'latitude':
            n = 'S' * sum(d < 0)
            p = 'N' * sum(d >= 0)
            dir = n + p
            major_tick_labels = [str(np.abs(int(d[i]))) + u"\N{DEGREE SIGN}" + dir[i] for i in range(len(d))]
        else:
            major_tick_labels = [str(int(d[i])) + u"\N{DEGREE SIGN}" for i in range(len(d))]

    return minor_ticks, major_ticks, major_tick_labels


def show_figure(fig):

    # create a dummy figure and use its
    # manager to display "fig"  
    dummy = plt.figure()
    new_manager = dummy.canvas.manager
    new_manager.canvas.figure = fig
    fig.set_canvas(new_manager.canvas)
    

def load_fig(figfile):
    """
    Load pickled figure

    Args:
        figdir (path): Full file path to pickled figure 
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
    """
    if isinstance(figdir, str):
        figdir = Path(figdir)

    os.makedirs(figdir, exist_ok=True)

    fullfile = figdir / figname
    
    with open(fullfile, 'wb') as file:
        pickle.dump(fig, file)
