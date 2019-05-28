Installation
============

``ceph-medic`` supports a few different installation methods, including system
packages for RPM distros via EPEL. For PyPI, it can be installed with::

    pip install ceph-medic


official upstream repos
-----------------------

Download official releases of ``ceph-medic`` at https://download.ceph.com/ceph-medic

Currently, only rpm repos built for centos 7 are supported.

``ceph-medic`` has dependencies on packages found in EPEL, so EPEL will need to be enabled.

Follow these steps to install a centos 7 repo from download.ceph.com:

- Install the latest rpm repo from download.ceph.com::

      wget http://download.ceph.com/ceph-medic/latest/rpm/el7/ceph-medic.repo -O /etc/yum.repos.d/ceph-medic.repo

- Install ``epel-release``::


      yum install epel-release

- Install the gpg key for ``ceph-medic``::

      wget https://download.ceph.com/keys/release.asc
      rpm --import release.asc

- Install ``ceph-medic``::

      yum install ceph-medic

- Verify your install::

      ceph-medic --help

shaman repos
------------

Every branch pushed to ceph-medic.git gets a rpm repo created and stored in
shaman.ceph.com. Currently, only rpm repos built for centos 7 are supported.

Browse https://shaman.ceph.com/repos/ceph-medic to find the available repos.

.. note::
   Shaman repos are only available for 2 weeks before they are automatically deleted.
   However, there should always be a repo available for the master branch of ``ceph-medic``.

``ceph-medic`` has dependencies on packages found in EPEL, so EPEL will need to be enabled.

Follow these steps to install a centos 7 repo from shaman.ceph.com:

- Install the latest master shaman repo::

      wget https://shaman.ceph.com/api/repos/ceph-medic/master/latest/centos/7/repo -O /etc/yum.repos.d/ceph-medic.repo

- Install ``epel-release``::

      yum install epel-release

- Install ``ceph-medic``::

      yum install ceph-medic

- Verify your install::

      ceph-medic --help

github
------
You can install directly from the source on github by following these steps:

- Clone the repository::

      git clone https://github.com/ceph/ceph-medic.git


- Change to the ``ceph-medic`` directory::

      cd ceph-medic

- Create and activate a python virtual environment::

      virtualenv venv
      source venv/bin/activate

- Install ceph-medic into the virtual environment::

      python setup.py install

``ceph-medic`` should now be installed and available in the virtualenv you just
created.  Check your installation by running: ``ceph-medic --help``
