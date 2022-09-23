# Import from standard Python libraries
import os
import pickle
import warnings
from pathlib import Path

# Imports from required packages
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from oceans.ocfis import spdir2uv, uv2spdir

# Imports from cool_maps
from cool_maps.calc import calculate_ticks, dd2dms, fmt
from cool_maps.download import get_bathymetry


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
        lon (array-like): Longitudes of bathymetry
        lat (array-like): Latitudes of bathymetry
        elevation (array-like): Elevation of bathymetry
        levels (tuple, optional): Determines the number and positions of the contour lines. Defaults to (-1000).
        zorder (int, optional): Drawing order for this function on the axes. Defaults to 5.
        transform (_type_, optional): Coordinate system data is defined in. Defaults to crs.PlateCarree.
        transform_first (bool, optional): Indicate that Cartopy points should be transformed before calling the contouring algorithm, which can have a significant impact on speed (it is much faster to transform points than it is to transform patches). Defaults to False.
    """
    lons, lats = np.meshgrid(lon, lat)
    h = ax.contour(lons, lats, elevation, levels, 
                    linewidths=.75, alpha=.5, colors='k', 
                    transform=transform, 
                    transform_first=transform_first, # May speed plotting up
                    zorder=zorder)
    ax.clabel(h, levels, inline=True, fontsize=6, fmt=fmt)
    return h


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


def add_features(ax, 
                 edgecolor="black", 
                 landcolor="tan",
                 oceancolor=cfeature.COLORS['water'],
                 coast = 'full',
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

    # Add state lines
    state_lines = cfeature.NaturalEarthFeature(
        category='cultural',
        name='admin_1_states_provinces_lines',
        scale='50m',
        facecolor='none'
    )

    # Select coastline resolution 
    if coast == 'full':
        LAND = cfeature.GSHHSFeature(scale='full')
    elif coast == 'high':
        LAND = cfeature.NaturalEarthFeature('physical', 'land', '10m')
    elif coast == 'mid':
        LAND = cfeature.NaturalEarthFeature('physical', 'land', '50m')
    elif coast == "low":
        LAND = cfeature.NaturalEarthFeature('physical', 'land', '110m')

    # Add features to axes
    ax.set_facecolor(oceancolor) # way faster than adding the ocean feature above
    ax.add_feature(LAND, 
                   edgecolor=edgecolor, 
                   facecolor=landcolor,
                   zorder=zorder+10)
    ax.add_feature(cfeature.RIVERS, zorder=zorder+10.2)
    ax.add_feature(cfeature.LAKES, zorder=zorder+10.2, alpha=0.5)
    ax.add_feature(state_lines, edgecolor=edgecolor, zorder=zorder+10.3)
    ax.add_feature(cfeature.BORDERS, linestyle='--', zorder=zorder+10.3)


def add_ticks(ax, extent,
              proj=proj['data'], 
              fontsize=13, 
              label_left=True,
              label_right=False,
              label_bottom=True, 
              label_top=False, 
              gridlines=False):
    """
    Calculate and add nicely formatted ticks to your map

    Args:
        ax (matplotlib.Axis): matplotlib Axis
        extent (tuple or list): extent (x0, x1, y0, y1) of the map in the given coordinate system.
        proj (cartopy.crs class, optional): Define a projected coordinate system for ticks. Defaults to ccrs.PlateCarree().
        fontsize (int, optional): Font size of tick labels. Defaults to 13.
        gridlines (bool, optional): Add gridlines to map. Defaults to False.
    """
    # Calculate Longitude ticks
    tick0x, tick1, ticklab = calculate_ticks(extent, 'longitude')
    ax.set_xticks(tick0x, minor=True, crs=proj)
    ax.set_xticks(tick1, crs=proj)
    ax.set_xticklabels(ticklab, fontsize=fontsize)

    # Calculate Latitude Ticks
    tick0y, tick1, ticklab = calculate_ticks(extent, 'latitude')
    ax.set_yticks(tick0y, minor=True, crs=proj)
    ax.set_yticks(tick1, crs=proj)
    ax.set_yticklabels(ticklab, fontsize=fontsize)

    # Adjust major ticks
    ax.tick_params(which='major',
                   direction='out',
                   bottom=True, top=True,
                   labelbottom=label_bottom, labeltop=label_top,
                   left=True, right=True,
                   labelleft=label_left, labelright=label_right,
                   length=5, width=2)

    # Adjust minor ticks
    ax.tick_params(which='minor',
                   direction='out',
                   bottom=True, top=True,
                #    labelbottom=True, labeltop=False,
                   left=True, right=True,
                #    labelleft=True, labelright=False,
                   width=1)
    
    # Add gridlines 
    if gridlines:
        gl = ax.gridlines(draw_labels=False, linewidth=.5, color='black',
                        alpha=0.5, linestyle='--', crs=proj, zorder=100)
        gl.xlocator = mticker.FixedLocator(tick0x)
        gl.ylocator = mticker.FixedLocator(tick0y)


def create(extent, 
           proj=proj['map'],
           features=True, 
           edgecolor="black", 
           landcolor="tan",
           oceancolor=cfeature.COLORS['water'],
           ticks=True,
           gridlines=False,
           bathymetry=False,
           isobaths=(-1000, -100),
           xlabel=None,
           ylabel=None,
           tick_label_left=True,
           tick_label_right=False,
           tick_label_bottom=True,
           tick_label_top=False,
           labelsize=14,
           ax=None,
           figsize=(11,8),
           zorder=0):
    """
    Create a cartopy map within a certain extent. 

    Args:
        extent (tuple or list): Extent (x0, x1, y0, y1) of the map in the given coordinate system.
        proj (cartopy.crs class, optional): Define a projected coordinate system with flat topology and Euclidean distance. Defaults to ccrs.Mercator().
        features (bool, optional): Add preferred map settings: colors, rivers, lakes, etc.. Defaults to True.
        edgecolor (str, optional): Color of edges of polygons. Defaults to "black".
        landcolor (str, optional): Color of land. Defaults to "tan".
        oceancolor (str, optional): Color of the ocean. Defaults to cartopy default water color
        ticks (bool, optional): Calculate appropriately spaced ticks. Defaults to True.
        gridlines (bool, optional): Add gridlines. Defaults to False
        bathymetry (bool or tuple, optional): Download and plot bathymetry on map. Defaults to False.
        isobaths (tuple or list, optional): Elevation at which to create bathymetric contour lines. Defaults to (-1000, -100)
        xlabel (str, optional): X Axis Label. Defaults to None
        ylabel (str, optional): Y Axis Label. Defaults to None
        tick_label_left (bool, optional): Add tick labels to left side of plot. Defaults to True.
        tick_label_right (bool, optional): Add tick labels to right side of plot. Defaults to False.
        tick_label_bottom (bool, optional): Add tick labels to bottom side of plot. Defaults to True.
        tick_label_top (bool, optional): Add tick labels to top side of plot. Defaults to False.
        labelsize (int, optional): Font size for axis labels. Defaults to 14.
        ax (matplotlib.Axis, optional): Pass matplotlib axis to function. Not necessary if plotting to subplot. Defaults to None.
        figsize (tuple, optional): (width, height) of the figure. Defaults to (11,8).
        zorder (int, optional): Set the starting zorder for the artists. Artists with lower zorder values are drawn first.

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
        # Set extent before we 'add features.' This is necessary because 
        # add_features adds land, coastlines, rivers, lakes, etc. based off 
        # of the current extent of the window.
        ax.set_extent(extent)

        # Create dictionary for feature arguments
        fargs = {
            "edgecolor": edgecolor,
            "landcolor": landcolor,
            "oceancolor": oceancolor,
            "zorder": zorder,
            }
        
        add_features(ax, **fargs)

    # Add bathymetry
    if bathymetry:
        bargs = {
            "levels": isobaths,
            "zorder": zorder+99,
        }
        bathy = get_bathymetry(extent)
        add_bathymetry(ax, bathy['longitude'], bathy['latitude'], bathy['z'], **bargs)

    # Add ticks using custom functions
    if ticks:
        tick_dict = {}
        tick_dict['label_left'] = tick_label_left
        tick_dict['label_right'] = tick_label_right
        tick_dict['label_bottom'] = tick_label_bottom
        tick_dict['label_top'] = tick_label_top
        tick_dict['gridlines'] = gridlines
        add_ticks(ax, extent, **tick_dict)
    else:
        # Add gridlines using built-in cartopy gridliner, provided we didn't
        # add any when we created the ticks
        if gridlines:
            ax.gridlines()

    # Add axis labels
    if xlabel:
        ax.set_xlabel('Longitude', fontsize=labelsize, fontweight='bold')
    if ylabel:
        ax.set_ylabel('Latitude', fontsize=labelsize, fontweight='bold')

    # If we generate a figure in this function, we have to return the figure
    # and axis to the calling function.
    if fig_init:
        return fig, ax


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

    # Check if path is a string or a Path object. If it's a string, 
    # convert it to a Path object
    if isinstance(path, str):
        path = Path(path)
    
    os.makedirs(path, exist_ok=True)
    
    if script:
        import datetime as dt
        now = dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        plt.figtext(.98, 0.20, f"{script} {now}",  fontsize=10, rotation=90)
        
    plt.savefig(path / fname, dpi=dpi, bbox_inches='tight', pad_inches=0.1)


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


if __name__ == "__main__":
    extent = (-90.0, -15.5, 0.0, 48.0)
    fig, ax = create(extent)
    plt.show()
