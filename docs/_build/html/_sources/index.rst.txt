.. Nagel et al. 2024 replication package documentation master file, created by
   sphinx-quickstart on Mon May  6 10:23:47 2024. You can adapt this file 
   completely to your liking, but it should at least contain the root `toctree`
   directive.

Nagel et al. 2024 Replication Package Documentation
=====================================================

This package produces the content of Nagel et al. (2024). Running the package 
directly will execute `__main__.py`, which simultaneously executes its 
submodules and with it all results:

.. code-block:: console

   $ python src/pfd

The submodules `shape_data.py`, `run_estimation.py`, and 
`create_descriptives.py` can also sequentially be executed individually to 
reproduce only certain parts of the paper because submodules depend on 
previous ones.

The random seed is globally set once for each program in the file 
`conf/config.yaml`, which contains parameters used by all programs. These 
variables can be modified by adding `.yaml files` like 
`conf/general/alt_seed.yaml`, which override the default configurations. 
However, there is no need to change any global variables.

.. warning::
    The current appearance settings of tables and figures may not perfectly 
    fit the output with changed seeds. 

.. toctree::
   :caption: Details:

   main_modules
   list_objects
   logic_subpackages

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
