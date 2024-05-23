Usage
=====

.. _installation:

Installation
------------

To use Anlitiq, first install it using pip:

.. code-block:: console

   (.venv) $ pip install analitiq

Creating recipes
----------------

To retrieve a list of random ingredients,
you can use the ``analitiq.get_random_ingredients()`` function:

.. autofunction:: analitiq.get_random_ingredients

The ``kind`` parameter should be either ``"meat"``, ``"fish"``,
or ``"veggies"``. Otherwise, :py:func:`analitiq.get_random_ingredients`
will raise an exception.

.. autoexception:: analitiq.InvalidKindError

For example:

>>> import analitiq
>>> analitiq.get_random_ingredients()
['shells', 'gorgonzola', 'parsley']

