=========
cool_maps
=========


.. .. image:: https://img.shields.io/pypi/v/cool_maps.svg
..     :target: https://pypi.python.org/pypi/cool_maps

.. .. image:: https://readthedocs.org/projects/cool_maps/badge/?version=latest
..         :target: https://cool_maps.readthedocs.io/en/latest/?version=latest
..         :alt: Documentation Status
    
.. .. image:: https://github.com/rucool/cool_maps/actions/workflows/python-package.yml/badge.sv



cool_maps is a package containing functions that utilizearound the cartopy for plotting data on maps. 

These functions are written to easily generate maps using pre-defined settings that our lab, Rutgers Center for Ocean Observing Leadership, prefers to use.


* Free software: MIT license


Features
--------

* TODO

============
Installation
============


Stable release
--------------
We recommend using miniconda to manage your Python environments. Download and follow the `Miniconda installation guide`_ for the appropriate
Miniconda installer for your operating system. 

.. _Miniconda installation guide: http://conda.pydata.org/miniconda.html

Install with conda:

.. code-block:: console

    conda install -c conda-forge ioos_qc


From sources
------------

The sources for cool_maps can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/rucool/cool_maps

Or download the `tarball`_:

.. code-block:: console

    $ curl -OJL https://github.com/rucool/cool_maps/tarball/master


=======================
Development and Testing
=======================

Create a conda environment:
---------------------------
.. code-block:: console

    conda create -n cool_maps python=3.9

.. code-block:: console
    
    conda activate cool_maps

.. code-block:: console   

    conda install --file requirements.txt


Run tests:
----------
After setting up your environment, you can run all of the tests, provided you install 'pytest':

.. code-block:: console

    $ pytest

Credits
-------

This package was created with Cookiecutter_ and the `conda/cookiecutter-conda-python`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`conda/cookiecutter-conda-python`: https://github.com/conda/cookiecutter-conda-python
.. _Github repo: https://github.com/rucool/cool_maps
.. _tarball: https://github.com/rucool/cool_maps/tarball/master