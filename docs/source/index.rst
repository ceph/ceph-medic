.. ceph-medic documentation master file, created by
   sphinx-quickstart on Tue Jun 27 14:32:23 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=================================================
Introduction
=================================================

``ceph-medic`` is a very simple tool that runs against a Ceph cluster to detect
common issues that might prevent correct functionality. It requires
non-interactive SSH access to accounts that can ``sudo`` without a password
prompt.

Usage
=====

The basic usage of ``ceph-medic`` is to perform checks against a ceph cluster
to identify potential issues with its installation or configuration. To do
this, run the following command::

    ceph-medic --inventory /path/to/hosts --ssh-config /path/to/ssh_config check

Inventory
---------
``ceph-medic`` needs to know the nodes that exist in your ceph cluster before
it can perform checks. The inventory (or ``hosts`` file) is a typical Ansible
inventory file and will be used to inform ``ceph-medic`` of the nodes in your
cluster and their respective roles.  The following standard host groups are
supported by ``ceph-medic``: ``mons``, ``osds``, ``rgws``, ``mdss``, ``mgrs``
and ``clients``.  An example ``hosts`` file would look like::

    [mons]
    mon0
    mon1

    [osds]
    osd0

    [mgrs]
    mgr0

The location of the ``hosts`` file can be passed into ``ceph-medic`` by using
the ``--inventory`` cli option (e.g ``ceph-medic --inventory /path/to/hosts``).

If the ``--inventory`` option is not defined, ``ceph-medic`` will first look in
the current working directory for a file named ``hosts``. If the file does not
exist, it will look for ``/etc/ansible/hosts`` to be used as the inventory.

.. note:: Defining the inventory location is also possible via the config file
          under the ``[global]`` section.


Inventory for Containers
------------------------
Containers are usually deployed under *baremetal* hosts, so it is possible to
define the hosts like a regular inventory, and ceph-medic will connect to
the containers existing in the host to produce a meaningful report.


Inventory for Container Platforms
---------------------------------
Both ``kubernetes`` and ``openshift`` platforms can host containers remotely
but do allow to connect and retrieve information from a central location. To
configure ceph-medic to connect to a platform the glocal section of the
configuration needs to define ``deployment_type`` to either ``kubernetes`` or
``openshift``. For example::

    [global]

    deployment_type = openshift


When using ``openshift`` or ``kubernetes`` as a deployment type, there is no
requirement to define a ``hosts`` file. The hosts are generated dynamically by
calling out to the platform and retrieving the pods. When the pods are
identified, they are grouped by deamon type (osd, mgr, rgw, mon, etc...).

SSH Config
----------

All nodes in your ``hosts`` file must be configured to provide non-interactive
SSH access to accounts that can ``sudo`` without a password prompt.

.. note::
   This is the same ssh config required by ansible. If you've used ``ceph-ansible`` to deploy your
   cluster then your nodes are most likely already configured for this type of ssh access. If that
   is the case, using the same user that performed the initial deployment would be easiest.

To provide your ssh config you must use the ``--ssh-config`` flag and give it
a path to a file that defines your ssh configuration. For example, a file like
this is used to connect with a cluster comprised of vagrant vms::

    Host mon0
      HostName 127.0.0.1
      User vagrant
      Port 2200
      UserKnownHostsFile /dev/null
      StrictHostKeyChecking no
      PasswordAuthentication no
      IdentityFile /Users/andrewschoen/.vagrant.d/insecure_private_key
      IdentitiesOnly yes
      LogLevel FATAL

    Host osd0
      HostName 127.0.0.1
      User vagrant
      Port 2201
      UserKnownHostsFile /dev/null
      StrictHostKeyChecking no
      PasswordAuthentication no
      IdentityFile /Users/andrewschoen/.vagrant.d/insecure_private_key
      IdentitiesOnly yes
      LogLevel FATAL


.. note:: SSH configuration is not needed when using ``kubernetes`` or
          ``openshift``


Logging
-------

By default ``ceph-medic`` sends complete logs to the current working directory.
This log file is more verbose than the output displayed on the terminal. To
change where these logs are created, modify the default value for ``--log-path``
in ``~/.cephmedic.conf``.

Running checks
--------------

To perform checks against your cluster use the ``check`` subcommand. This will
perform a series of general checks, as well as checks specific to each daemon.
Sample output from this command will look like::

    ceph-medic --ssh-config vagrant_ssh_config check
    Host: mgr0                  connection: [connected  ]
    Host: mon0                  connection: [connected  ]
    Host: osd0                  connection: [connected  ]
    Collection completed!

    =======================  Starting remote check session  ========================
    Version: 0.0.1    Cluster Name: "test"
    Total hosts: [3]
    OSDs:    1    MONs:    1     Clients:    0
    MDSs:    0    RGWs:    0     MGRs:       1

    ================================================================================

    ---------- managers ----------
     mgr0

    ------------ osds ------------
     osd0

    ------------ mons ------------
     mon0

    17 passed, 0 errors, on 4 hosts


The logging can also be configured in the ``cephmedic.conf`` file in the global
section::

    [global]
    --log-path = .
