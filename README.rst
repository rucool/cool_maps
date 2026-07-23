=========
cool_maps
=========

.. image:: https://readthedocs.org/projects/cool-maps/badge/?version=latest
    :target: https://cool-maps.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. .. image:: https://img.shields.io/pypi/v/cool_maps.svg
..     :target: https://pypi.python.org/pypi/cool_maps

.. .. image:: https://github.com/rucool/cool_maps/actions/workflows/python-package.yml/badge.svg


``cool_maps`` is a small toolbox of helper functions, built on top of `Cartopy
<https://scitools.org.uk/cartopy/docs/latest/>`_ (and, optionally, `Basemap
<https://matplotlib.org/basemap/>`_), for quickly producing nice-looking oceanographic maps: coastlines,
bathymetry, ocean currents, and your own data overlaid on top. It was written to easily generate maps
using pre-defined settings that our lab, the Rutgers Center for Ocean Observing Leadership, prefers to
use -- but the defaults are general-purpose and the styling is fully customizable.

**Full documentation, including a complete tutorial and API reference, is hosted at**
https://cool-maps.readthedocs.io/en/latest/.


Features
========

* One function, :func:`cplt.create`, to build a complete map from just an ``extent`` -- coastlines, land/
  ocean colors, ticks, and borders included by default.
* Built-in bathymetry download and plotting (contours, shaded contours, or continuous depth shading),
  and ocean current quiver plots from ``xarray`` datasets. Large extents are automatically tiled to stay
  under the server's request-size limits.
* Supported on two interchangeable mapping engines, Cartopy and Basemap -- the same code works under
  either, including plotting your own data directly on the returned axes.
* Nicely spaced, DMS- or decimal-degree-labeled ticks computed automatically from your map extent.


Quickstart
==========

::

    import cool_maps.plot as cplt

    # Gulf of Mexico
    extent = [-99, -79, 18, 31]

    fig, ax = cplt.create(extent, bathymetry=True)

See the `full tutorial <https://cool-maps.readthedocs.io/en/latest/tutorial.html>`_ (also available as a
runnable notebook at ``notebooks/tutorial.ipynb``) for a complete walkthrough covering projections,
coastline resolution, colors, ticks, bathymetry, overlaying your own data, currents, and choosing between
engines.


Selecting a map engine
=======================

The plotting helpers support both Cartopy (the default) and Basemap. Cartopy remains the default engine,
but you can select Basemap after installing it::

    >>> import cool_maps.plot as cplt
    >>> cplt.set_engine('basemap')

You can also set ``COOL_MAPS_ENGINE=basemap`` in your environment before importing :mod:`cool_maps.plot`,
or pass ``engine=`` to any individual call without touching the global default::

    >>> cplt.create(extent, engine="basemap")

When switching engines you can keep using the same Cartopy CRS objects in calls such as
``cplt.create(..., proj=ccrs.Mercator())``. The Basemap backend will translate a handful of common
projections automatically; if a CRS cannot be converted, pass the Basemap projection name or keyword
dictionary instead (for example ``proj={'projection': 'lcc', 'lon_0': -74, 'lat_0': 39}``).

For a Cartopy-free workflow you can use the shared projection keywords provided by cool_maps::

    >>> cplt.create(extent, proj="mercator")

Behind the scenes the string is mapped to the appropriate Cartopy CRS or Basemap projection depending on
the active engine.

Axes returned by ``create()`` remember which engine they were built with, so you never need to pass
``engine=`` to ``add_features``/``add_bathymetry``/``add_currents``/``add_ticks`` yourself -- it's inferred
from the axes. You can also plot directly on the returned axes with ``ax.scatter``/``ax.plot``/``ax.contour``/
``ax.contourf``/``ax.pcolormesh``/``ax.quiver``/``ax.fill`` using plain lon/lat data; cool_maps injects the
right ``transform=`` (Cartopy) or ``latlon=True`` (Basemap) for you, so the exact same plotting code works
under either engine::

    >>> fig, ax = cplt.create(extent, engine="basemap")  # or "cartopy"
    >>> ax.scatter(lon, lat, c=values)  # no transform=/latlon= needed, regardless of engine


Installation
============


Stable release
--------------
We recommend using miniconda to manage your Python environments. Download and follow the `Miniconda installation guide`_ for the appropriate
Miniconda installer for your operating system.

.. _Miniconda installation guide: http://conda.pydata.org/miniconda.html

Install with conda (includes Cartopy; the only required engine):

.. code-block:: console

    $ conda install -c conda-forge cool_maps

To also enable the optional Basemap engine:

.. code-block:: console

    $ conda install -c conda-forge basemap basemap-data-hires

If you're installing with pip instead, the ``basemap`` extra pulls it in for you:

.. code-block:: console

    $ pip install cool_maps[basemap]


From sources
------------

The sources for cool_maps can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/rucool/cool_maps

Or download the `tarball`_:

.. code-block:: console

    $ curl -OJL https://github.com/rucool/cool_maps/tarball/master

Change your directory to the source code of cool_maps

.. code-block:: console

    $ cd ~/cool_maps


Once you are in the correct directory, there are two ways to install from source.

Method 1:

.. code-block:: console

    $ python setup.py install

Method 2:

.. code-block:: console

    $ pip install .


.. _Github repo: https://github.com/rucool/cool_maps
.. _tarball: https://github.com/rucool/cool_maps/tarball/master


Documentation
=============

* Full docs, tutorial, and API reference: https://cool-maps.readthedocs.io/en/latest/
* Runnable tutorial notebook: ``notebooks/tutorial.ipynb``
* Cartopy/Basemap parity deep-dive and performance comparison: ``notebooks/dual_backend_demo.ipynb``


License
=======

MIT license -- see `LICENSE <https://github.com/rucool/cool_maps/blob/main/LICENSE>`_ for details.
