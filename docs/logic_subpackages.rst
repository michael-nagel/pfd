Logic of Subpackages
--------------------

Subpackages are documented for transparency. We assign modules to one of the
following packages on the basis of the following criteria.

`data`

- Scripts to download or generate data.

`features`

- Scripts to turn raw data into features for modeling.

`models`

- Scripts to train models and then use trained models to make predictions.

`visualization`

- Scripts to create exploratory and results oriented visualizations.

`helpers`

- Depend on other parts and/or external libraries
- Rather support specific parts of the package
- E.g., validation functions, data formatting classes, ...

  → Architectural snippets

`utils`

- Independent of other parts (no internal imports)
- Used generally
- E.g., string manipulations, math libraries, ...

  → Snippets to build bigger units

.. note::
    Note that we use `_` as prefix for modules and methods that are not 
    imported in the directory of the main file. Modules/methods starting with 
    `_` are excluded from this documentation.