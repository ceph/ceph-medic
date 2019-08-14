OSDs
====

The following checks indicate issues with OSD nodes.

Warnings
--------


.. _WOSD1:

WOSD1
^^^^^
Multiple ceph_fsid values found in /var/lib/ceph/osd.

This might mean you are hosting OSDs for many clusters on
this node or that some OSDs are misconfigured to join the
clusters you expect.

.. _WOSD2:

WOSD2
^^^^^
Setting ``osd pool default min size = 1`` can lead to data loss because if the
minimum is not met, Ceph will not acknowledge the write to the client.

.. _WOSD3:

WOSD3
^^^^^
The default value of 3 OSD nodes for a healthy cluster must be met. If
``ceph.conf`` is configured to a different number, that setting will take
precedence. The number of OSD nodes is calculated by adding
``osd_pool_default_size`` and ``osd_pool_default_min_size`` + 1. By default,
this adds to 3.

.. _WOSD4:

WOSD4
^^^^^
If ratios have been modified from its defaults, a warning is raised pointing to
any ratio that diverges. The ratios observed with their defaults are:

* ``backfillfull_ratio``: 0.9
* ``nearfull_ratio``: 0.85
* ``full_ratio``: 0.95

