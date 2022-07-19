=========
cool_maps
=========


.. .. image:: https://img.shields.io/pypi/v/cool_maps.svg
..     :target: https://pypi.python.org/pypi/cool_maps

.. .. image:: https://readthedocs.org/projects/cool_maps/badge/?version=latest
..         :target: https://cool_maps.readthedocs.io/en/latest/?version=latest
..         :alt: Documentation Status
    
.. .. image:: https://github.com/rucool/cool_maps/actions/workflows/python-package.yml/badge.sv



Wrapper functions around the cartopy for plotting data on maps. 
These functions are written to easily generate maps using some pre-defined settings that our lab, Rutgers Center for Ocean Observing Leadership, prefers to use.


* Free software: MIT license


Features
--------

* TODO

============
Installation
============
conda create -n cool_maps python=3.9
conda activate cool_maps
conda install --file requirements.txt

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

Once you have a copy of the source, you can should create a new conda/virtual environment following the Installation instructions above.


Running tests
-------------
After setting up your environment, you can run all of the tests, provided you install 'pytest':

.. code-block:: console

    $ pytest


.. _Github repo: https://github.com/rucool/cool_maps
.. _tarball: https://github.com/rucool/cool_maps/tarball/master

Credits
-------

This package was created with Cookiecutter_ and the `conda/cookiecutter-conda-python`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`conda/cookiecutter-conda-python`: https://github.com/conda/cookiecutter-conda-python