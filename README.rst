=========
cool_maps
=========


.. .. image:: https://img.shields.io/pypi/v/hfradarpy.svg
..     :target: https://pypi.python.org/pypi/hfradarpy

.. .. image:: https://readthedocs.org/projects/hfradarpy/badge/?version=latest
..         :target: https://hfradarpy.readthedocs.io/en/latest/?version=latest
..         :alt: Documentation Status
    
.. .. image:: https://github.com/<rucool>/hfradarpy/actions/workflows/<WORKFLOW_FILE>/badge.sv

.. .. .. image:: https://circleci.com/gh/rucool/HFRadarPy/tree/master.svg?style=svg
.. ..    :target: https://circleci.com/gh/rucool/HFRadarPy/tree/master

.. .. image:: https://codecov.io/gh/rucool/hfradarpy/branch/master/graph/badge.svg
..    :target: https://codecov.io/gh/rucool/hfradarpy




Helper functions around the Python toolboxes matplotlib for plotting data, and cartopy for plotting data on maps. These functions are written to easily generate maps using some pre-defined settings that our lab prefers to use.


* Free software: MIT license
* Documentation: https://hfradarpy.readthedocs.io.


Features
--------

* TODO

============
Installation
============


Stable release
--------------

To install cool_maps, run this command in your terminal:

.. code-block:: console

    $ pip install cool_maps

This is the preferred method to install cool_maps, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


We also recommend using miniconda to manage your Python environments. Download and follow the `Miniconda installation guide`_ for the appropriate
Miniconda installer for your operating system. 

.. _Miniconda installation guide: http://conda.pydata.org/miniconda.html

Make sure to add the channel, `conda-forge`_, to your .condarc. You can
find out more about conda-forge from their website:

.. _conda-forge: https://conda-forge.org/

You can do this with the following command:

.. code-block:: console

        conda config --add channels conda-forge

From sources
------------

The sources for cool_maps can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/rucool/cool_maps

Or download the `tarball`_:

.. code-block:: console

    $ curl -OJL https://github.com/rucool/cool_maps/tarball/master

Once you have a copy of the source, you can should create a new conda/virtual environment:

Create environment
------------------

Change your current working directory to the location that you
downloaded cool_maps to.

.. code-block:: console

        $ cd ~/Downloads/cool_maps/

Create conda environment from the included environment_dev.yml file:

.. code-block:: console

        $ conda env create -f environment_dev.yml

Once the environment is done building, you can activate the environment
by typing:

.. code-block:: console

        $ conda activate cool_maps # OSX/Unix

Once the environment is your active environment. You can install the toolbox to that environment.

.. code-block:: console

    $ python setup.py install

You can also change directory into the root cool_maps directory and install with the following:

.. code-block:: console

    $ pip install .

Or if you are developing new code in the toolbox, you should install this library as 'editable':

.. code-block:: console

    $ pip install --no-deps --force-reinstall --ignore-installed -e .

