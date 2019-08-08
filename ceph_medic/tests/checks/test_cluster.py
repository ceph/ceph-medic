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

class TestNearfull(object):

    def setup(self):
        metadata['cluster'] = {}

    def teardown(self):
        metadata['cluster'] = {}

    def test_key_error_is_ignored(self):
        assert cluster.check_nearfull() is None
    def test_osd_map_is_nearfull(self):
        metadata['cluster'] = {'status': {'osdmap': {'osdmap': {'nearfull': True}}}}
        assert cluster.check_nearfull() == ('ECLS2', 'Cluster is nearfull')
    def test_osd_map_is_not_nearfull(self):
        metadata['cluster'] = {'status': {'osdmap': {'osdmap': {'nearfull': False}}}}
    