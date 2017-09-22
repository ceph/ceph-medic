OSDs
====

The following checks indicate issue with OSD nodes.

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
Setting ``osd pool default min size = 1`` can lead to data loss because if
minimum is not met, Ceph will not acknowledge the write to the client.

