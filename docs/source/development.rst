===========
Development
===========

Create a conda environment:
---------------------------
.. code-block:: console

    conda create -n cool_maps python=3.9    
    conda activate cool_maps
    conda install --file requirements_dev.txt

Make sure to install this library as 'editable':

.. code-block:: console

    $ pip install --no-deps --force-reinstall --ignore-installed -e .

Run tests:
----------
After setting up your environment, you can run all of the tests, provided you install 'pytest':

.. code-block:: console

    $ pytest

The console will display the test results. There should be no failures. Warnings are usually OK.
