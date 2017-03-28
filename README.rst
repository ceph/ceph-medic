===================================================
 ceph-doctor -- Find common issues in Ceph clusters
===================================================

``ceph-doctor`` is a very simple tool to run against a Ceph cluster to detect
common issues that might prevent correct functionality. It requires
non-interactive SSH access to accounts that can ``sudo`` without a password
prompt.


Cluster node facts
------------------
Fact collection happens per node and creates a mapping of hosts and data
gathered. Each daemon 'type' is the primary key::

    ...
    'osd': {
        'node1': {...},
        'node2': {...},
    }
    'mon': {
        'node3': {...},
    }


There are other top-level keys that make it easier to deal with fact metadata,
like for example a full list of all hosts discovered::

    'hosts': ['node1', 'node2', 'node3'],
    'osds': ['node1', 'node2'],
    'mons': ['node3']


Each host has distinct metadata that gets collected. If any errors are
detected, the ``failed`` key is set to ``True``, a brief summary of the error is placed on the ``error`` key and full
traceback information is available on the ``__debug__`` key. For example
a failure on a call to ``stat`` on a path might be::

    'osd': {
        'node1': {
            'paths': {
                '/var/lib/osd': {
                    'error': 'No such file or directory',
                    'failed': True,
                    '__debug__': "Traceback (most recent call last):\n File "remote.py", line 3, in <module>\n os.stat('/var/lib/osd')\n OSError: [Errno 2] No such file or directory: '/var/lib/osd'\n",
                }
            }
        }
    }

Path contents are optionally enabled by the fact engine and it will contain the
raw representation of the full file contents. Here is an example of what
a ``ceph.conf`` file would be in a monitor node::


     'mon': {
         'node3': {
             'paths': {
                 '/etc/ceph/ceph.conf':
                     'contents': "[global]\nfsid = f05294bd-6e9d-4883-9819-c2800d4d7962\nmon_initial_members = node3\nmon_host = 192.168.111.102\nauth_cluster_required = cephx\nauth_service_required = cephx\nauth_client_required = cephx\n",
                     'failed': False,
                     'error': None,
                     '__debug__': None

                }
            }
        }


