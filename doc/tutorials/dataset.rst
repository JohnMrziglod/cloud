How To Use typhon.spareice.datasets.Dataset?
============================================

What is the idea?
-----------------

Imagine you have a big dataset consisting of many files containing observations (e.g. images or satellite data). Each
file covers a certain time period and is located in folders which names contain information about the time. See

.. figure:: _data/.png
   :scale: 50 %
   :alt: map to buried treasure

   This is the caption of the figure (a simple paragraph).

Quick Start
-----------


Iterating over files in a period
--------------------------------

When you add a new function or class, you also have to add its name the
corresponing rst file in the doc/ folder.

Via .find_files(...)
++++++++++++++++++++

All code documentation in `Typhon` should follow the Google Style Python
Docstrings format. Below you can find various example on how the docstrings
should look like. The example is taken from
http://sphinxcontrib-napoleon.readthedocs.org/en/latest/example_google.html

Download: :download:`example_google.py <example_google.py>`

.. literalinclude:: example_google.py
   :language: python

Via .read_period(...)
+++++++++++++++++++++



Via .map(...) or .map_content(...)
++++++++++++++++++++++++++++++++++

All documentation for properties should be attached to the getter function
(@property). No information should be put in the setter function of the
property. Because all access occurs through the property name and never by
calling the setter function explicitly, documentation put there will never be
visible. Neither in the ipython interactive help nor in Sphinx.

Via magic indexing
++++++++++++++++++



File handler objects
--------------------

FileHandler.get_info(...)
+++++++++++++++++++++++++

FileHandler.read(...)
+++++++++++++++++++++

FileHandler.write(...)
++++++++++++++++++++++

Get the time coverage by filename or content
--------------------------------------------

File path placeholders
++++++++++++++++++++++

Find overlapping files between two datasets
-------------------------------------------
