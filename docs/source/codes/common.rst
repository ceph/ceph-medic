Common
======
The following checks indiciate general issues with the cluster that are not specific to any daemon type.

Warnings
--------

.. _WCOM1:

WCOM1
^^^^^
A running OSD and MON daemon were detected in the same node. Colocating OSDs and MONs is highly discouraged.


Errors
------

.. _ECOM1:

ECOM1
^^^^^
A ceph configuration file cannot be found at ``/etc/ceph/$cluster-name.conf``.

.. _ECOM2:

ECOM2
^^^^^
The ``ceph`` executable was not found.

.. _ECOM3:

ECOM3
^^^^^
The ``/var/lib/ceph`` directory does not exist or could not be collected.

.. _ECOM4:

ECOM4
^^^^^
The ``/var/lib/ceph`` directory was not owned by the ``ceph`` user.

.. _ECOM5:

ECOM5
^^^^^
The ``fsid`` defined in the configuration differs from other nodes in the cluster. The ``fsid`` must be
the same for all nodes in the cluster.

.. _ECOM6:

ECOM6
^^^^^
The installed version of ``ceph`` is not the same for all nodes in the cluster. The ``ceph`` version should be
the same for all nodes in the cluster.

.. _ECOM7:

ECOM7
^^^^^
The installed version of ``ceph`` is not the same as the one of a running ceph daemon. The installed ``ceph`` version should be the same as all running ceph daemons. If they do not match, the daemons most likely have not been restarted correctly after a version change.

.. _ECOM8:

ECOM8
^^^^^
The ``fsid`` field must exist in the configuration for each node.


.. _ECOM9:

ECOM9
^^^^^
A cluster should not have running daemons with a cluster ``fsid`` that is different from the rest of the daemons in a cluster. This potentially means that different cluster identifiers are being used, and that should not be the case.


.. _ECOM10:

ECOM10
^^^^^^
Only a single monitor daemon shuld be running per host, having more than one monitor running on the same host reduces a cluster's resilience if the node goes down.
