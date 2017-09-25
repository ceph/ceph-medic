Common
======
The following checks indiciate general issues with the cluster that are not specific to any daemon type.

Errors
------

.. _ECOM1:

ECOM1
_____
A ceph configuration file can not be found at ``/etc/ceph/$cluster-name.conf``.

.. _ECOM2:

ECOM2
_____
The ``ceph`` executable was not found.

.. _ECOM3:

ECOM3
_____
The ``/var/lib/ceph`` directory does not exist or could not be collected.  

.. _ECOM4:

ECOM4
_____
The ``/var/lib/ceph`` directory was not owned by the ``ceph`` user. 

.. _ECOM5:

ECOM5
_____
The ``fsid`` defined in the configuration differs from other nodes in the cluster. The ``fsid`` must be
the same for all nodes in the cluster.

.. _ECOM6:

ECOM6
_____
The installed version of ``ceph`` is not the same for all nodes in the cluster. The ``ceph`` version should be
the same for all nodes in the cluster.

ECOM7
_____
The installed version of ``ceph`` is not the same reported by a running ceph daemon. The installed ``ceph`` version should be
the same as all running ceph daemons, if they do not match these daemons most likely have not been restarted correctly after
a version change.
