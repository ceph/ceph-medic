from textwrap import dedent
from ceph_medic.checks import osds
from ceph_medic import metadata


class TestOSDS(object):

    def test_fails_check_ceph_fsid(self):
        data = {'paths': {'/var/lib/ceph': {'files': {
            '/var/lib/ceph/osd/ceph-0/ceph_fsid': {'contents': "fsid1"},
            '/var/lib/ceph/osd/ceph-1/ceph_fsid': {'contents': "fsid2"},
        }}}}
        result = osds.check_osd_ceph_fsid(None, data)
        assert "WOSD1" in result

    def test_min_pool_size_fails(self, data):
        metadata['cluster_name'] = 'ceph'
        contents = dedent("""
        [global]
        cluster = foo
        osd_pool_default_min_size = 1
        """)
        osd_data = data()
        osd_data['paths']['/etc/ceph']['files']['/etc/ceph/ceph.conf'] = {'contents': contents}
        code, error = osds.check_min_pool_size(None, osd_data)
        assert error == 'osd default pool size is set to 1, can potentially lose data'

    def test_min_pool_size_is_correct(self, data):
        metadata['cluster_name'] = 'ceph'
        contents = dedent("""
        [global]
        cluster = foo
        osd_pool_default_min_size = 2
        """)
        osd_data = data()
        osd_data['paths']['/etc/ceph']['files']['/etc/ceph/ceph.conf'] = {'contents': contents}
        result = osds.check_min_pool_size(None, osd_data)
        assert result is None


class TestMinOSDS(object):

    def test_min_osd_nodes_is_not_met(self, data):
        metadata['osds'] = {'osd1': []}
        metadata['cluster_name'] = 'ceph'
        osd_data = data()
        contents = dedent("""
        [global]
        cluster = foo
        osd_pool_default_min_size = 2
        """)
        osd_data['paths']['/etc/ceph']['files']['/etc/ceph/ceph.conf'] = {'contents': contents}
        code, error = osds.check_min_osd_nodes(None, osd_data)
        assert code == 'WOSD3'
        assert '6 needed, 1 found' in error

    def test_min_osd_nodes_is_met(self, data):
        metadata['osds'] = dict(('osd%s' % count, []) for count in range(6))
        metadata['cluster_name'] = 'ceph'
        osd_data = data()
        contents = dedent("""
        [global]
        cluster = foo
        osd_pool_default_min_size = 2
        """)
        osd_data['paths']['/etc/ceph']['files']['/etc/ceph/ceph.conf'] = {'contents': contents}
        result = osds.check_min_osd_nodes(None, osd_data)
        assert result is None
