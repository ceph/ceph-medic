from ceph_medic.checks import cluster
from ceph_medic import metadata


class TestCheckOSDs(object):

    def setup(self):
        metadata['cluster_name'] = 'ceph'
        metadata['osds'] = {}

    def teardown(self):
        metadata['osds'] = {}

    def test_no_osds(self):
        assert cluster.check_osds_exist() == ('ECLS1', 'There are no OSDs available')

    def test_osds_are_found(self):
        metadata['osds'] = {'osd1': {}}
        assert cluster.check_osds_exist() is None
