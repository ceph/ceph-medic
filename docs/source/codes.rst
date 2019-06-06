===========
Error Codes
===========

When performing checks, ``ceph-medic`` will return an error code and message for any that failed. These checks
can either be a ``warning`` or ``error``, and will pertain to common issues or daemon specific issues. Any error
code starting with ``E`` is an error, and any starting with ``W`` is a warning.

Below you'll find a list of checks that are performed with the ``check`` subcommand.


.. toctree::
   :maxdepth: 2

   codes/common.rst
   codes/mons.rst
   codes/osds.rst
   codes/cluster.rst
