===========
Error Codes
===========

When performing checks ``ceph-medic`` will return an error code and message for any failed checks. These checks
can either be a ``warning`` or ``error`` and will pertain to common issues or daemon specific issues. Any error
code that starts with ``E`` is an error and any that start with ``W`` is a warning.

Below you'll find a list of checks that are performed with the ``check`` subcommand.


.. toctree::
   :maxdepth: 2

   codes/common.rst
   codes/mons.rst
