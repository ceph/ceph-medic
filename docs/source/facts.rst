Cluster node facts
==================
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
detected, the ``exception`` key is set populated with all information regarding to the error generated when trying to execute the call.
For example a failure on a call to ``stat`` on a path might be::

    'osd': {
        'node1': {
            'paths': {
                '/var/lib/osd': {
                    'exception': {
                        'traceback': "Traceback (most recent call last):\n File "remote.py", line 3, in <module>\n os.stat('/var/lib/osd')\n OSError: [Errno 2] No such file or directory: '/var/lib/osd'\n",
                        'name': 'OSError',
                        'repr': "[Errno 2] No such file or directory: '/root'"
                        'attributes': {
                            args : "(2, 'No such file or directory')",
                            errno : 2,
                            filename :  '/var/lib/ceph' ,
                            message : '',
                            strerror :  'No such file or directory'
                        }
                }
            }
        }
    }

Note that objects will not get pickled, so data structures and objects will be
sent back as plain text.

Path contents are optionally enabled by the fact engine and it will contain the
raw representation of the full file contents. Here is an example of what
a ``ceph.conf`` file would be in a monitor node::


     'mon': {
         'node3': {
             'paths': {
                 '/etc/ceph/': {
                    'dirs': [],
                    'files': {
                        '/etc/ceph/ceph.conf': {
                            'contents': "[global]\nfsid = f05294bd-6e9d-4883-9819-c2800d4d7962\nmon_initial_members = node3\nmon_host = 192.168.111.102\nauth_cluster_required = cephx\nauth_service_required = cephx\nauth_client_required = cephx\n",
                            'owner': 'ceph',
                            'group': 'ceph',
                            'n_fields' : 19 ,
                            'n_sequence_fields' : 10 ,
                            'n_unnamed_fields' : 3 ,
                            'st_atime' : 1490714187.0 ,
                            'st_birthtime' : 1463607160.0 ,
                            'st_blksize' : 4096 ,
                            'st_blocks' : 0 ,
                            'st_ctime' : 1490295294.0 ,
                            'st_dev' : 16777220 ,
                            'st_flags' : 1048576 ,
                            'st_gen' : 0 ,
                            'st_gid' : 0 ,
                            'st_ino' : 62858421 ,
                            'st_mode' : 16877 ,
                            'st_mtime' : 1490295294.0 ,
                            'st_nlink' : 26 ,
                            'st_rdev' : 0 ,
                            'st_size' : 884 ,
                            'st_uid' : 0 ,
                            'exception': {},
                         }
                     }
                 }
             }
         }
     }
