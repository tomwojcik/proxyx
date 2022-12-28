==========
Quickstart
==========

************
Installation
************

Using pypi.

.. code-block:: bash

   $ pip install proxyx

Using docker

See # todo:

**********
How to use
**********

Configure how the server operates using environment variables or `.env.server` file. There are not secrets there,
so this file can added to the VCS.

Configure routing using `proxyx.yaml`. Go to `yaml` to read about all the possible configuration fields.
You might want to use `jsonschema.yaml`, which will add hints and show errors in your configuration file.

In other words, if you need a relatively simple proxy app, you need at most 2 configuration files.
