import matplotlib.colors
import matplotlib.pyplot as plt
import numpy as np
from typing import Tuple, List, Union


def calculate_ticks(
    extent: Union[Tuple[float, ...], List[float]],
    direction: str,
    decimal_degrees: bool = False,
    whole_degree_majors: bool = True,
) -> Tuple[np.ndarray, np.ndarray, Union[np.ndarray, List[str]]]:
    """
    Define major and minor tick locations and major tick labels

    Args:
        extent (tuple or list): extent (x0, x1, y0, y1) of the map in the given coordinate system.
        direction (str): Tell function which bounds to calculate. Must be 'longitude' or 'latitude'.
        decimal_degrees (bool, optional): label ticks in decimal degrees (True) or degree-minute-second (False, default)
        whole_degree_majors (bool, optional): keep major ticks on whole degrees even for small extents
            (span <= 3 degrees), with minutes only ever shown on minor ticks. Defaults to True. Set to False
            to allow major ticks at 15'/30' increments for spans <= 3 degrees, matching pre-1.x behavior.

    Returns:
        np.ndarray: minor ticks
        np.ndarray: major ticks
        Union[np.ndarray, List[str]]: major tick labels
    """
    # Lowercase the direction variable
    direction = direction.lower()

    # Convert values in extent to floats
    extent = [float(x) for x in extent]

    if direction == 'longitude':
        l0, l1 = extent[0], extent[1]
    elif direction == 'latitude':
        l0, l1 = extent[2], extent[3]
    else:
        raise ValueError("direction must be 'longitude' or 'latitude'")

    # Calculate distance
    r = l1 - l0

    # Pre-defined tick spacing based off of distance in degrees
    if not whole_degree_majors and r <= 1.5:
        # <1.5 degrees: 15' major ticks, 5' minor ticks
        minor_int = 1.0 / 12.0
        major_int = 1.0 / 4.0
    elif not whole_degree_majors and r <= 3.0:
        # <3 degrees: 30' major ticks, 10' minor ticks
        minor_int = 1.0 / 6.0
        major_int = 0.5
    elif r <= 7.0:
        # <=7 degrees: 1d major ticks, 15' minor ticks
        minor_int = 0.25
        major_int = 1.0
    elif r <= 10:
        # <=10 degrees: 2d major ticks, 30' minor ticks
        minor_int = 0.5
        major_int = 2.0
    elif r <= 50:
        # <=50 degrees: 5d major ticks, 1d minor ticks
        minor_int = 1.0
        major_int = 5.0
    elif r <= 80:
        # <=80 degrees: 10d major ticks, 5d minor ticks
        minor_int = 5.0
        major_int = 10.0
    elif r <= 120:
        # <=120 degrees: 15d major ticks, 5d minor ticks
        minor_int = 5.0
        major_int = 15.0
    elif r <= 160:
        # <=160 degrees: 20d major ticks, 5d minor ticks
        minor_int = 5.0
        major_int = 20.0
    elif r <= 250:
        # <=250 degrees: 30d major ticks, 10d minor ticks
        minor_int = 10.0
        major_int = 30.0
    else:
        # >250 degrees: 45d major ticks, 15d minor ticks
        minor_int = 15.0
        major_int = 45.0

    minor_ticks = np.arange(
        np.ceil(l0 / minor_int) * minor_int, 
        np.ceil(l1 / minor_int) * minor_int + minor_int,
        minor_int
    )
    minor_ticks = minor_ticks[minor_ticks <= l1]
    
    major_ticks = np.arange(
        np.ceil(l0 / major_int) * major_int, 
        np.ceil(l1 / major_int) * major_int + major_int,
        major_int
    )
    major_ticks = major_ticks[major_ticks <= l1]

    label_int = major_int
    if major_ticks.size == 0:
        # Extent is narrower than one major interval and doesn't straddle a
        # major tick value (e.g. a very tight zoom); fall back to minor ticks
        # so the map is never left with zero labeled ticks.
        major_ticks = minor_ticks
        label_int = minor_int

    if decimal_degrees:
        major_tick_labels = major_ticks
    else:
        if label_int < 1:
            d, m, _ = dd2dms(np.array(major_ticks))
            if direction == 'longitude':
                dirs = np.where(d < 0, 'W', 'E')
                major_tick_labels = [f"{int(abs(d[i]))}\N{DEGREE SIGN}{int(m[i])}'{dirs[i]}" for i in range(len(d))]
            elif direction == 'latitude':
                dirs = np.where(d < 0, 'S', 'N')
                major_tick_labels = [f"{int(abs(d[i]))}\N{DEGREE SIGN}{int(m[i])}'{dirs[i]}" for i in range(len(d))]
            else:
                major_tick_labels = [f"{int(d[i])}\N{DEGREE SIGN}{int(m[i])}'" for i in range(len(d))]
        else:
            d = major_ticks
            if direction == 'longitude':
                dirs = np.where(d < 0, 'W', 'E')
                major_tick_labels = [f"{int(abs(d[i]))}\N{DEGREE SIGN}{dirs[i]}" for i in range(len(d))]
            elif direction == 'latitude':
                dirs = np.where(d < 0, 'S', 'N')
                major_tick_labels = [f"{int(abs(d[i]))}\N{DEGREE SIGN}{dirs[i]}" for i in range(len(d))]
            else:
                major_tick_labels = [f"{int(d[i])}\N{DEGREE SIGN}" for i in range(len(d))]

    return minor_ticks, major_ticks, major_tick_labels


def calculate_colorbar_ticks(vmin: float, vmax: float, c0: bool = False) -> np.ndarray:
    """
    Calculate tick locations for colorbar

    Args:
        vmin (float): minimum value of colorbar (should match vmin of object colorbar is mapped to)
        vmax (float): maximum value of colorbar (should match vmax of object colorbar is mapped to)
        c0 (bool): center values around 0 (for anomaly products)

    Returns:
        np.ndarray: tick locations
    """

    if c0:
        vmax = np.max((np.abs(vmin), np.abs(vmax)))
        vmin = 0
        scale = 1.0
        if vmax - vmin < 0:
            scale = 10**(-np.floor(np.log10(vmax - vmin)) + 1)

        cbticks = np.arange(vmin, np.floor(vmax * scale + .99))
        if len(cbticks) > 3:
            cbticks = cbticks[::int(np.floor(len(cbticks) / 3))]
        cbticks = cbticks / scale
        i = np.diff(cbticks)[0]
        if cbticks[-1] + i <= vmax:
            cbticks = np.append(cbticks, cbticks[-1] + i)
        i = np.diff(cbticks)[0]
        cbticks = np.append(np.arange(-np.max(cbticks), 0, i), cbticks)
        return cbticks
    
    scale = 1.0
    if vmax - vmin < 4:
        scale = 10**(-np.floor(np.log10(vmax - vmin)) + 1)

    cbticks = np.arange(np.ceil(vmin * scale + .01), np.floor(vmax * scale + .99))
    if len(cbticks) > 5:
        cbticks = cbticks[::int(np.floor(len(cbticks) / 5))]
    cbticks = cbticks / scale
    i = np.diff(cbticks)[0]
    if cbticks[0] - i >= vmin:
        cbticks = np.append(cbticks[0] - i, cbticks)
    if cbticks[-1] + i <= vmax:
        cbticks = np.append(cbticks, cbticks[-1] + i)
    
    return cbticks


def dd2dms(vals: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Convert decimal degrees to degree-minute-second

    Args:
        vals (np.ndarray): Numpy array of decimal degrees

    Returns:
        np.ndarray: degrees
        np.ndarray: minutes
        np.ndarray: seconds
    """
    n = vals < 0
    vals_abs = np.abs(vals)
    d = np.floor(vals_abs)
    rem = (vals_abs - d) * 60.0
    m = np.floor(rem)
    rem -= m
    s = np.round(rem * 60.0)
    
    # Apply sign back to degrees
    d[n] = -d[n]
    return d, m, s


def fmt(x: float) -> str:
    """
    Function to format bathymetry labels

    Args:
        x (float): Bathymetry float value

    Returns:
        str: Formatted string
    """
    s = f"{x:.1f}"
    if s.endswith("0"):
        s = f"{x:.0f}"
    return rf"{s}"