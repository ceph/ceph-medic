.. ceph-medic documentation master file, created by
   sphinx-quickstart on Tue Jun 27 14:32:23 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

=================================================
ceph-medic -- Find common issues in Ceph clusters
=================================================


``ceph-medic`` is a very simple tool to run against a Ceph cluster to detect
common issues that might prevent correct functionality. It requires
non-interactive SSH access to accounts that can ``sudo`` without a password
prompt.

Installation
============

``ceph-medic`` supports a couple different installation methods:

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

``ceph-medic`` should now be installed and available in the virtualenv you just created.
Check your installation by running: ``ceph-medic --help``

shaman repos
------------

Every branch pushed to ceph-medic.git gets a rpm repo created and stored in
shaman.ceph.com. Currently, only rpm repos built for centos 7 are supported.

Browse https://shaman.ceph.com/repos/ceph-medic to find the available repos.

.. note::
   Shaman repos are only available for 2 weeks before they are automatically deleted.
   However, there should always be a repo available for the master branch of ``ceph-medic``.

``ceph-medic`` has dependancies on packages found in EPEL, so EPEL will need to be enabled.
There is also a dependancy on ``python-tambo`` which is not available in EPEL.

Follow these steps to install a centos 7 repo from shaman.ceph.com:

- Install the latest master shaman repo::

      wget https://shaman.ceph.com/api/repos/ceph-medic/master/latest/centos/7/repo -O /etc/yum.repos.d/ceph-medic.repo

- Install ``epel-release``::

      yum install epel-release

- Download and install a ``python-tambo`` rpm for version ``2.0``, one can be found here: https://copr-be.cloud.fedoraproject.org/results/ktdreyer/ceph-installer/epel-7-x86_64/00488036-python-tambo/ ::

      wget https://copr-be.cloud.fedoraproject.org/results/ktdreyer/ceph-installer/epel-7-x86_64/00488036-python-tambo/python-tambo-0.2.0-5.el7.centos.noarch.rpm
      rpm -ivh python-tambo-0.2.0-5.el7.centos.noarch.rpm``

- Install ``ceph-medic``::

      yum install ceph-medic

- Verify your install::

      ceph-medic --help
