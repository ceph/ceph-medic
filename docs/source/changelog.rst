1.0.6
-----
* Docker, podman container support
* Fix broken SSH config option

1.0.5
-----
27-Jun-2019

* Add check for minimum OSD node count
* Add check for minimum MON node count
* Remove reporting of nodes that can't connect, report them separetely
* Kubernetes, Openshift, container support
* Fix unidentifiable user/group ID issues
* Rook support
* Report on failed nodes
* When there are errors, set a non-zero exit status
* Add separate "cluster wide" checks, which run once
* Be able to retrieve socket configuration
* Fix issue with trying to run ``whoami`` to test remote connections, use
  ``true`` instead
* Add check for missing FSID
* Skip OSD validation when there isn't any ceph.conf
* Skip tmp directories in /var/lib/ceph scanning to prevent blowing up
* Detect collocated daemons
* Allow overriding ignores in the CLI, fallback to the config file
* Break documentation up to have installation away from getting started


1.0.4
-----
20-Aug-2018

* Add checks for parity between installed and socket versions
* Fix issues with loading configuration with whitespace
* Add check for min_pool_size
* Collect versions from running daemons
