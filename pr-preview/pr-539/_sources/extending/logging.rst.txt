.. include:: ../links.inc

.. _logging_in_extension:

Logging in a ``junifer`` extension
==================================

It is important to have proper logging in your code and ``junifer`` makes it trivial to do so for your extensions.

For DataGrabber:

.. code-block:: python

   from junifer.datagrabber import logger


For Preprocessor:

.. code-block:: python

   from junifer.preprocess import logger


For Marker:

.. code-block:: python

   from junifer.marker import logger


For Storage:

.. code-block:: python

   from junifer.storage import logger


Importing the correct logger will give you a properly set up logger which will fit right in with the rest of ``junifer``\'s log output.
