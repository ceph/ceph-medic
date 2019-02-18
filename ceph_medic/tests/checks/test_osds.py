from textwrap import dedent
from ceph_medic.checks import osds
from ceph_medic import metadata


class TestOSDS(object):

    def setup(self):
        metadata['cluster_name'] = 'ceph'

    def teardown(self):
        metadata.pop('cluster_name', None)

    def test_fails_check_ceph_fsid(self):
        data = {'paths': {'/var/lib/ceph': {'files': {
            '/var/lib/ceph/osd/ceph-0/ceph_fsid': {'contents': "fsid1"},
            '/var/lib/ceph/osd/ceph-1/ceph_fsid': {'contents': "fsid2"},
        }}}}
        result = osds.check_osd_ceph_fsid(None, data)
        assert "WOSD1" in result

    def test_min_pool_size_fails(self, data):
        contents = dedent("""
        [global]
        cluster = foo
        osd_pool_default_min_size = 1
        """)
        osd_data = data()
        osd_data['paths']['/etc/ceph']['files']['/etc/ceph/ceph.conf'] = {'contents': contents}
        code, error = osds.check_min_pool_size(None, osd_data)
        assert error == 'osd default pool min_size is set to 1, can potentially lose data'

    def test_min_pool_size_is_correct(self, data):
        contents = dedent("""
        [global]
        cluster = foo
        osd_pool_default_min_size = 2
        """)
        osd_data = data()
        osd_data['paths']['/etc/ceph']['files']['/etc/ceph/ceph.conf'] = {'contents': contents}
        result = osds.check_min_pool_size(None, osd_data)
        assert result is None
