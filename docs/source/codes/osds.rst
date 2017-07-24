OSDs
====

The following checks indicate issue with OSD nodes.

Warnings
--------


.. _WOSD1:

WOSD1
_____
Multiple ceph_fsid values found in /var/lib/ceph/osd.

This might mean you are hosting OSDs for many clusters on
this node or that some OSDs are misconfigured to join the
clusters you expect.
