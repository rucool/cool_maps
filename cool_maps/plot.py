import os
import pickle
import warnings
from itertools import cycle

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cmocean
import matplotlib.colors
import matplotlib.pyplot as plt
import numpy as np
from oceans.ocfis import spdir2uv, uv2spdir

# Suppresing warnings for a "pretty output."
warnings.simplefilter("ignore")


def add_argo(ax, df, transform):
    tdf = df.reset_index()
    most_recent = tdf.loc[tdf.groupby('argo')['time'].idxmax()]

    if most_recent.shape[0] > 50:
        custom_cmap = 'black'
        marker = cycle(['o'])
    else:
        custom_cmap = categorical_cmap(10, 5, cmap="tab10")
        marker = cycle(['o', 'h', 'p'])

    n = 0
    for float in most_recent.itertuples():
        ax.plot(float.lon, float.lat, marker=next(marker), markersize=7, markeredgecolor='black', color=custom_cmap.colors[n],
                label=float.argo,
                transform=transform)
        # map_add_legend(ax)
        n = n + 1


def add_all_argo(ax, df, transform):
    grouped = df.groupby(['longitude (degrees_east)', 'latitude (degrees_north)'])
    for i, x in grouped:
        ax.plot(i[0], i[1], marker='o', markersize=7, markeredgecolor='black', color='green', transform=transform)


def add_bathymetry(ax, lon, lat, elevation, levels=(-1000), zorder=5):
    # lon = ds.variables['longitude'][:]
    # lat = ds.variables['latitude'][:]
    # elevation = ds.variables['elevation'][:]

    h = ax.contour(lon, lat, elevation, levels, 
                    linewidths=.75, alpha=.5, colors='k', 
                    transform=ccrs.PlateCarree(), zorder=zorder)
    ax.clabel(h, levels, inline=True, fontsize=6, fmt=fmt)
    return ax


def add_currents(ax, ds, coarsen=None, scale=None, headwidth=None, headlength=None, headaxislength=None):
    """
    Add currents to map
    :param dsd: dataset
    :param sub: amount to downsample by
    :return:
    """
    scale = scale or 90
    headwidth = headwidth or 2.75
    headlength = headlength or 2.75
    headaxislength = headaxislength or 2.5
    coarsen = coarsen or 2

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


def add_features(ax, extent, edgecolor="black", landcolor="tan", zorder=0):

    state_lines = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='50m',
        facecolor='none'
    )

    LAND = cfeature.GSHHSFeature(scale='full')

    # Axes properties and features
    ax.set_extent(extent)
    ax.add_feature(cfeature.OCEAN, zorder=zorder)
    ax.add_feature(LAND, 
                   edgecolor=edgecolor, 
                   facecolor=landcolor,
                   zorder=zorder+10)
    ax.add_feature(cfeature.RIVERS, zorder=zorder+10.2)
    ax.add_feature(cfeature.LAKES, zorder=zorder+10.2)
    ax.add_feature(state_lines, edgecolor=edgecolor, zorder=zorder+10.3)
    ax.add_feature(cfeature.BORDERS, zorder=zorder+10.3)


def add_gliders(ax, df, transform):
    for g, new_df in df.groupby(level=0):
        q = new_df.iloc[-1]
        ax.plot(new_df['longitude'], new_df['latitude'], color='black',
                linewidth=1.5, transform=ccrs.PlateCarree())
        ax.plot(q['longitude'], q['latitude'], marker='^', markeredgecolor='black',
                markersize=8.5, label=g, transform=transform)
        # map_add_legend(ax)


def add_legend(ax):
    # Shrink current axis by 20%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 0.8, box.height])
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))


def add_ticks(ax, extent, fontsize=13):
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

    # if grid:
        # ax.grid(color='k', linestyle='--', zorder=zorder)
    return ax


def add_transects(ax, transects, projection):
    ax.plot(transects['lon'], transects['lat'], 'r-', transform=projection)


def categorical_cmap(nc, nsc, cmap="tab10", continuous=False):
    """
    From ImportanceOfBeingErnest
    https://stackoverflow.com/a/47232942/2643708
    :param nc: number of categories (colors)
    :param nsc: number of subcategories (shades for each color)
    :param cmap: matplotlib colormap
    :param continuous:
    :return:
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
           features=True, edgecolor="black", landcolor="tan",
           ax=None, figsize=(11,8)):
    """Create a cartopy map within a certain extent. 

    Args:
        extent (tuple or list): Extent (x0, x1, y0, y1) of the map in the given coordinate system.
        proj (cartopy.crs class, optional): Define a projected coordinate system with flat topology and Euclidean distance.
            Defaults to ccrs.Mercator().
        features (bool, optional): Add preferred map settings. 
            Defaults to True.
        ax (_type_, optional): Pass matplotlib axis to function. Not necessary if plotting to subplot. 
            Defaults to None.
        figsize (tuple, optional): (width, height) of the figure. Defaults to (11, 8).

    Returns:
        _type_: _description_
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
            }
        add_features(ax, extent, **fargs)

    # # Add bathymetry
    # if bathy:
    #     bargs = {
    #         "isobaths": isobaths,
    #         "zorder": 1.5      
    #     }
    #     map_add_bathymetry(ax, bathy, proj, **bargs)

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
        path (str or Path): Full file name including path
        script (str, optional): Print name of script on plot. Defaults to None.
        dpi (int, optional): Dots per inch. Defaults to 150.
    """
    os.makedirs(path, exist_ok=True)
    
    if script:
        import datetime as dt
        now = dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        plt.figtext(.98, 0.20, f"{script} {now}",  fontsize=10, rotation=90)
        
    plt.savefig(path / fname, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
    # plt.clf()

    
def fmt(x):
    s = f"{x:.1f}"
    if s.endswith("0"):
        s = f"{x:.0f}"
    return rf"{s}"


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

def load(figdir):
    with open(figdir, "rb") as file:
        fig = pickle.load(file)
    return fig


def save(fig, figdir):
    with open(figdir, 'wb') as file:
        pickle.dump(fig, file)
