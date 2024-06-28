import matplotlib.colors
import matplotlib.pyplot as plt
import numpy as np


def calculate_ticks(extent, direction, decimal_degrees=False):
    """
    Define major and minor tick locations and major tick labels

    Args:
        extent (tuple or list): extent (x0, x1, y0, y1) of the map in the given coordinate system.
        dirs (str): Tell function which bounds to calculate. Must be 'longitude' or 'latitude'.
        decimal_degrees (bool, optional): label ticks in decimal degrees (True) or degree-minute-second (False, default)

    Returns:
        list: minor ticks
        list: major ticks
        list: major tick labels
    """
    # Lowercase the direction variable
    direction = direction.lower()

    # Convert values in extent to floats
    extent = [float(x) for x in extent]

    if direction == 'longitude':
        l0 = extent[0]
        l1 = extent[1]
        o0 = extent[2]
        o1 = extent[3]
    elif direction == 'latitude':
        l0 = extent[2]
        l1 = extent[3]
        o0 = extent[0]
        o1 = extent[1]

    # Calculate distance
    r = np.max([l1 - l0, o1 - o0])

    # Pre-defined tick spacing based off of distance in degrees
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
        major_int = float(1)
    elif r <= 15:
        # <15 degrees: 2d major ticks, 30' minor ticks
        minor_int = 0.5
        major_int = float(2)
    elif r <= 30:
        # <=30 degrees: 3d major ticks, 1d minor ticks
        minor_int = float(1)
        major_int = float(3)
    elif r <=50:
        # <=50 degrees: 5d major ticks, 1d minor ticks
        minor_int = float(1)
        major_int = float(5)
    elif r <=80:
        # <=80 degrees: 10d major ticks, 5d minor ticks
        minor_int = float(5)
        major_int = float(10)
    elif r <=120:
        # <=120 degrees: 15d major ticks, 5d minor ticks
        minor_int = float(5)
        major_int = float(15)
    elif r <=160:
        # <=160 degrees: 20d major ticks, 5d minor ticks
        minor_int = float(5)
        major_int = float(20)
    elif r <=250:
        # <=250 degrees: 30d major ticks, 10d minor ticks
        minor_int = float(10)
        major_int = float(30)
    else:
        # >250 degrees: 45d major ticks, 15d minor ticks
        minor_int = float(15)
        major_int = float(45)

    minor_ticks = np.arange(
        np.ceil(l0 / minor_int) * minor_int, 
        np.ceil(l1 / minor_int) * minor_int + minor_int,
        minor_int)
    minor_ticks = minor_ticks[minor_ticks <= l1]
    
    major_ticks = np.arange(
        np.ceil(l0 / major_int) * major_int, 
        np.ceil(l1 / major_int) * major_int + major_int,
        major_int)
    major_ticks = major_ticks[major_ticks <= l1]

    if decimal_degrees:
        major_tick_labels = major_ticks
    else:
        if major_int < 1:
            d, m, _ = dd2dms(np.array(major_ticks))
            if direction == 'longitude':
                n = 'W' * sum(d < 0)
                p = 'E' * sum(d >= 0)
                dir = n + p
                major_tick_labels = [str(np.abs(int(d[i]))) + u"\N{DEGREE SIGN}" + str(int(m[i])) + "'" + dir[i] for i in
                                    range(len(d))]
            elif direction == 'latitude':
                n = 'S' * sum(d < 0)
                p = 'N' * sum(d >= 0)
                dir = n + p
                major_tick_labels = [str(np.abs(int(d[i]))) + u"\N{DEGREE SIGN}" + str(int(m[i])) + "'" + dir[i] for i in
                                    range(len(d))]
            else:
                major_tick_labels = [str(int(d[i])) + u"\N{DEGREE SIGN}" + str(int(m[i])) + "'" for i in range(len(d))]
        else:
            d = major_ticks
            if direction == 'longitude':
                n = 'W' * sum(d < 0)
                p = 'E' * sum(d >= 0)
                dir = n + p
                major_tick_labels = [str(np.abs(int(d[i]))) + u"\N{DEGREE SIGN}" + dir[i] for i in range(len(d))]
            elif direction == 'latitude':
                n = 'S' * sum(d < 0)
                p = 'N' * sum(d >= 0)
                dir = n + p
                major_tick_labels = [str(np.abs(int(d[i]))) + u"\N{DEGREE SIGN}" + dir[i] for i in range(len(d))]
            else:
                major_tick_labels = [str(int(d[i])) + u"\N{DEGREE SIGN}" for i in range(len(d))]

    return minor_ticks, major_ticks, major_tick_labels


def calculate_colorbar_ticks(vmin, vmax, c0=False):
    """
    Calculate tick locations for colorbar

    Args:
        vmin (float): minimum value of colorbar (should match vmin of object colorbar is mapped to)
        vmax (float): maximum value of colorbar (should match vmax of object colorbar is mapped to)
        c0 (bool): center values around 0 (for anomaly products)

    Returns:
        list: tick locations
    """

    if c0:
        vmax=np.max((np.abs(vmin), np.abs(vmax)))
        vmin=0
        scale = 1
        if vmax-vmin<0:
            scale = 10**(-np.floor(np.log10(vmax-vmin))+1)

        cbticks = np.arange(vmin, np.floor(vmax*scale+.99))
        if len(cbticks)>3:
            cbticks=cbticks[::int(np.floor(len(cbticks)/3))]
        cbticks = cbticks/scale
        i=np.diff(cbticks)[0]
        if cbticks[-1]+i<=vmax:
            cbticks=np.append(cbticks, cbticks[-1]+i)
        i=np.diff(cbticks)[0]
        cbticks=np.append(np.arange(-np.max(cbticks),0,i),cbticks)
        return cbticks
    
    scale = 1
    if vmax-vmin<4:
        scale = 10**(-np.floor(np.log10(vmax-vmin))+1)

    cbticks = np.arange(np.ceil(vmin*scale+.01), np.floor(vmax*scale+.99))
    if len(cbticks)>5:
        cbticks=cbticks[::int(np.floor(len(cbticks)/5))]
    cbticks = cbticks/scale
    i=np.diff(cbticks)[0]
    if cbticks[0]-i>=vmin:
        cbticks=np.append(cbticks[0]-i, cbticks)
    if cbticks[-1]+i<=vmax:
        cbticks=np.append(cbticks, cbticks[-1]+i)
    
    return cbticks


def categorical_cmap(nc, nsc, cmap="tab10", continuous=False):
    """
    Expand your colormap by changing the alpha value (opacity) of each color.
    
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


def dd2dms(vals):
    """
    Convert decimal degrees to degree-minute-second

    Args:
        vals (np.ndarray): Numpy array of decimal degrees

    Returns:
        np.ndarray: degrees
        np.ndarray: minutes
        np.ndarray: seconds

    """
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


def fmt(x):
    """
    Function to format bathymetry labels

    Args:
        x (string): Bathymetry string

    Returns:
        string: Formatted string
    """
    s = f"{x:.1f}"
    if s.endswith("0"):
        s = f"{x:.0f}"
    return rf"{s}"