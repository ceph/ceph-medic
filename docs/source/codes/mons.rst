Monitors
========

The following checks indicate issues with monitor nodes.

Errors
------

.. _EMON1:

EMON1
_____
The secret key used in the keyring differs from other nodes in the cluster.

Warnings
--------


.. _WMON1:

WMON1
_____
Multiple monitor directories are found on the same host.

.. _WMON2:

WMON2
_____
Collocated OSDs in monitor nodes were found on the same host.

.. _WMON3:

WMON3
_____
The recommended number of Monitor nodes is 3 for a high availability setup.

.. _WMON4:

WMON4
_____
It is recommended to have an odd number of monitors so that failures can be
tolerated.


.. _WMON5:

WMON5
_____
Having a single monitor is not recommneded, as a failure would cause data loss.
For high availability, at least 3 monitors is recommended.
