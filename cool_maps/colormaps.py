import cmocean
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

"""
Modified colormaps: colormaps with defined breakpoints; categorical colormaps

Functions to modify colormaps with defined breakpoints.
Mostly for oxygen, but who knows where this will take us.
Individual colors can be removed from any version

Based on our best research (Fed and NJ) so far, 
and concentration/saturation equivalents based on summer 2023 ru28 and ru40 deployments
(concentration to saturation conversions are variable so these should be used with a grain of salt):

hypoxia = < 3 mg/L, = 93.75 umol/L, approx = 40% saturation
low DO = < 5 mg/L, = 156.25 umol/L, approx = 65% saturation
supersaturation = > 100% saturation, approx = 7.5 mg/L, = 234.375

    cm_oxy_mod: original cmocean colormap red to gray to yellow
    cm_rygg: red to yellow to gray to green
    cm_rogg: red to orange to gray to green (gray shading reversed from original oxy)
    cm_partialturbo_r: red to orange/yellow to gray to blue

Function to define categorical colormaps based on defined number of categories

    cm_categorical: categorical colormaps

"""

def cm_oxy_mod(vmin=2, vmax=9, breaks=[3,7.5], red=True, gray=True, yellow=True):
    """
    Modify cmocean oxy colormap with defined break points
    red (dark to less dark) to gray (dark to light) to yellow (light to dark-ish)

    Args:
        vmin (float): colormap minimum
        vmax (float): colormap maximum
        breaks (list of floats): break-points within colormap to transition to new color
        red, gray, yellow (bool): whether to include each color in new colormap (default True for all)

    Raises:
        ValueError: nans or not-numbers provided for vmin, vmax, or breaks
        ValueError: values do not increase from vmin -> breaks -> vmax
        ValueError: number of breakpoints does not match with number of colors in new map

    Returns:
        object: matplotlib colormap
    """
    all_nums = np.append(np.append(vmin,breaks),vmax)
    # check that all values are real numbers
    if not np.all(np.isreal(all_nums)) or np.any(np.isnan(all_nums)):
        raise ValueError('All values must be real numbers.')
    # check that all values increase in the right order
    if np.any(np.diff(all_nums)<0):
        raise ValueError('All values must be increasing from vmin -> breaks -> vmax')
    # check that number of break values works with number of colors
    if red+gray+yellow != len(breaks)+1:
        raise ValueError(f'Number of breakpoints ({len(breaks)}) must be one less than number of colors ({red+gray+yellow})')
    # define interval
    ni = (vmax-vmin)/100
    
    b=1
    if red:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = cmocean.cm.oxy(np.linspace(0,.19,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    if gray:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = cmocean.cm.oxy(np.linspace(.2,.79,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    if yellow:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = cmocean.cm.oxy(np.linspace(.8,1,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    newmap = mcolors.LinearSegmentedColormap.from_list('my_colormap',cmfull)
    return newmap


def cm_rygg(vmin=2, vmax=9, breaks=[3,5,7.5], red=True, yellow=True, gray=True, green=True):
    """
    Modify cmocean oxy colormap with defined break points
    red (dark to less dark) to yellow (light to dark-ish)to gray (dark to light) to green (light to mid)
    
    Args:
        vmin (float): colormap minimum
        vmax (float): colormap maximum
        breaks (list of floats): break-points within colormap to transition to new color
        red, yellow, gray, green (bool): whether to include each color in new colormap (default True for all)
        
    Raises:
        ValueError: nans or not-numbers provided for vmin, vmax, or breaks
        ValueError: values do not increase from vmin -> breaks -> vmax
        ValueError: number of breakpoints does not match with number of colors in new map

    Returns:
        object: matplotlib colormap
    """
    all_nums = np.append(np.append(vmin,breaks),vmax)
    # check that all values are real numbers
    if not np.all(np.isreal(all_nums)) or np.any(np.isnan(all_nums)):
        raise ValueError('All values must be real numbers.')
    # check that all values increase in the right order
    if np.any(np.diff(all_nums)<0):
        raise ValueError('All values must be increasing from vmin -> breaks -> vmax')
    # check that number of break values works with number of colors
    if red+yellow+gray+green != len(breaks)+1:
        raise ValueError(f'Number of breakpoints ({len(breaks)}) must be one less than number of colors ({red+yellow+gray+green})')
    # define interval
    ni = (vmax-vmin)/100
    
    b=1
    if red:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = cmocean.cm.oxy(np.linspace(0,.19,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    if yellow:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = cmocean.cm.oxy(np.linspace(.8,1,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    if gray:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = cmocean.cm.oxy(np.linspace(.2,.79,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    if green:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = cmocean.cm.algae(np.linspace(0,.5,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    
    newmap = mcolors.LinearSegmentedColormap.from_list('my_colormap',cmfull)
    return newmap

def cm_rogg(vmin=2, vmax=9, breaks=[3,5,7.5], red=True, orange=True, gray=True, green=True):
    """
    Modify cmocean oxy colormap with defined break points
    red (dark to less dark) to orange (dark-ish to light)to gray (light to dark) to green (mid to light)

    Args:
        vmin (float): colormap minimum
        vmax (float): colormap maximum
        breaks (list of floats): break-points within colormap to transition to new color
        red, orange, gray, green (bool): whether to include each color in new colormap (default True for all)
        
    Raises:
        ValueError: nans or not-numbers provided for vmin, vmax, or breaks
        ValueError: values do not increase from vmin -> breaks -> vmax
        ValueError: number of breakpoints does not match with number of colors in new map

    Returns:
        object: matplotlib colormap
    """
    all_nums = np.append(np.append(vmin,breaks),vmax)
    # check that all values are real numbers
    if not np.all(np.isreal(all_nums)) or np.any(np.isnan(all_nums)):
        raise ValueError('All values must be real numbers.')
    # check that all values increase in the right order
    if np.any(np.diff(all_nums)<0):
        raise ValueError('All values must be increasing from vmin -> breaks -> vmax')
    # check that number of break values works with number of colors
    if red+orange+gray+green != len(breaks)+1:
        raise ValueError(f'Number of breakpoints ({len(breaks)}) must be one less than number of colors ({red+orange+gray+green})')
    # define interval
    ni = (vmax-vmin)/100
    
    b=1
    if red:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = cmocean.cm.oxy(np.linspace(0,.19,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    if orange:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = plt.cm.Oranges(np.linspace(.8,.4,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    if gray:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = cmocean.cm.oxy(np.linspace(.7,.2,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    if green:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = plt.cm.Oranges(np.linspace(.8,.4,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    
    newmap = mcolors.LinearSegmentedColormap.from_list('my_colormap',cmfull)
    return newmap

def cm_partialturbo_r(vmin=2, vmax=9, breaks=[3,5,7.5], red=True, orange=True, gray=True, blue=True):
    """
    Modify cmocean oxy colormap with defined break points
    red (dark to bright) to orange/yellow (orangey orange to orangey yellow)to gray (dark to light) to blue (cyan to bright)
    
    Args:
        vmin (float): colormap minimum
        vmax (float): colormap maximum
        breaks (list of floats): break-points within colormap to transition to new color
        red, orange, gray, blue (bool): whether to include each color in new colormap (default True for all)
        
    Raises:
        ValueError: nans or not-numbers provided for vmin, vmax, or breaks
        ValueError: values do not increase from vmin -> breaks -> vmax
        ValueError: number of breakpoints does not match with number of colors in new map

    Returns:
        object: matplotlib colormap
    """
    all_nums = np.append(np.append(vmin,breaks),vmax)
    # check that all values are real numbers
    if not np.all(np.isreal(all_nums)) or np.any(np.isnan(all_nums)):
        raise ValueError('All values must be real numbers.')
    # check that all values increase in the right order
    if np.any(np.diff(all_nums)<0):
        raise ValueError('All values must be increasing from vmin -> breaks -> vmax')
    # check that number of break values works with number of colors
    if red+orange+gray+blue != len(breaks)+1:
        raise ValueError(f'Number of breakpoints ({len(breaks)}) must be one less than number of colors ({red+orange+gray+blue})')
    # define interval
    ni = (vmax-vmin)/100
    
    b=1
    if red:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = plt.cm.turbo(np.linspace(1,.85,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    if orange:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = plt.cm.turbo(np.linspace(.75,.6,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    if gray:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = cmocean.cm.oxy(np.linspace(.3,.79,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    if blue:
        nints = int(np.floor((all_nums[b]-all_nums[b-1])/ni))
        cm0 = plt.cm.turbo(np.linspace(.3,.1,nints))
        if b==1:
            cmfull = cm0
        else:
            cmfull = np.vstack((cmfull,cm0))
        b+=1
    
    newmap = mcolors.LinearSegmentedColormap.from_list('my_colormap',cmfull)
    return newmap


def cm_categorical(N, listvals=True):
    """
    Define categorical colormap.
    For 8 or fewer categories uses colorblind-friendly colormap defined by mpetroff (https://mpetroff.net/2018/03/color-cycle-picker/)
    For 9-10 categories uses tab10
    For 10-100 categories uses tab10 modified with multiple shades from ImportanceOfBeingErnest (https://stackoverflow.com/a/47232942/2643708)
    For >100 categories no colormap defined
    
    Args:
        N (int): number of categories to include in colorbar
        listvals (bool): return array of rgb or hex values instead of colormap object
        
    Raises:
        ValueError: Too many categories for colormap

    Returns:
        object: matplotlib colormap
    """
    if N > 100:
        raise ValueError("Too many categories for colormap.")
    
    if N <= 8:
        # unicorn colormap from mpetroff
        newmap = np.array(['#7b85d4','#f37738','#83c995','#d7369e','#c4c9d8','#859795','#e9d043','#ad5b50'])
    else:
        # modified tab10 from ImportanceOfBeingErnest
        # if N<=10, equivalent to original tab10
        nc = 10
        nsc = int(np.ceil(N/nc))
        ccolors = plt.cm.tab10(np.arange(nc, dtype=int))
        for i, c in enumerate(ccolors):
            chsv = mcolors.rgb_to_hsv(c[:3])
            arhsv = np.tile(chsv,nsc).reshape(nsc,3)
            arhsv[:,1] = np.linspace(chsv[1],0.25,nsc)
            arhsv[:,2] = np.linspace(chsv[2],1,nsc)
            rgb = mcolors.hsv_to_rgb(arhsv)
            if i==0:
                newmap = rgb
            else:
                newmap = np.vstack((newmap,rgb))
            if i==np.mod(N,nc):
                nsc-=1

    newmap = newmap[:N]

    if not listvals:
        newmap = matplotlib.colors.ListedColormap(newmap)
    
    return newmap
