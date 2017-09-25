from ceph_medic.checks import common
from ceph_medic import metadata


class TestGetFsid(object):

    def setup(self):
        metadata['cluster_name'] = 'ceph'

    def teardown(self):
        metadata.pop('cluster_name')

    def make_metadata(self, contents=None):
        contents = contents or ''
        data = {'paths': {'/etc/ceph':{'files':{'/etc/ceph/ceph.conf':{'contents': contents}}}}}
        data['cluster_name'] = 'ceph'
        return data

    def test_fails_to_find_an_fsid(self):
        data = self.make_metadata("[global]\nkey=value\n\n[mdss]\ndisabled=true\n")
        fsid = common.get_fsid(data)
        assert fsid == ''

    def test_empty_conf_returns_empty_string(self):
        data = self.make_metadata()
        fsid = common.get_fsid(data)
        assert fsid == ''

    def test_find_an_actual_fsid(self):
        data = self.make_metadata("[global]\nfsid = 1234-lkjh\n\n[mdss]\ndisabled=true\n")
        fsid = common.get_fsid(data)
        assert fsid == '1234-lkjh'

    def test_spaces_on_fsid_are_trimmed(self):
        data = self.make_metadata("[global]\nfsid = 1234-lkjh   \n\n[mdss]\ndisabled=true\n")
        fsid = common.get_fsid(data)
        assert fsid == '1234-lkjh'


class TestCephVersionParity(object):

    def setup(self):
        metadata['cluster_name'] = 'ceph'

    def teardown(self):
        metadata.pop('cluster_name')

    def test_finds_a_mismatch_of_versions(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1', 'node2'])
        node1_data = make_data()
        metadata['mons']['node1'] = node1_data
        metadata['mons']['node2'] = make_data({'ceph': {'version': '13'}})
        result = common.check_ceph_version_parity('node1', node1_data)
        assert 'Ceph version "12.2.1" is different' in str(result)

    def test_versions_have_parity(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1', 'node2'])
        node1_data = make_data()
        metadata['mons']['node1'] = node1_data
        metadata['mons']['node2'] = make_data()
        result = common.check_ceph_version_parity('node1', node1_data)
        assert result is None


class TestCephSocketAndInstalledVersionParity(object):

    def setup(self):
        metadata['cluster_name'] = 'ceph'

    def teardown(self):
        metadata.pop('cluster_name')

    def test_finds_a_mismatch_of_versions(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1'])
        node1_data = make_data(
            {'ceph': {
                "sockets": {
                    "/var/run/ceph/osd.asok": {"version": "13.2.0"},
                },
                "installed": True,
                "version": "12.2.1",
            }}
        )
        metadata['mons']['node1'] = node1_data
        result = common.check_ceph_socket_and_installed_version_parity('node1', node1_data)
        assert 'Ceph version "12.2.1" is different' in str(result)

    def test_versions_have_parity(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1'])
        node1_data = make_data(
            {'ceph': {
                "sockets": {
                    "/var/run/ceph/osd.asok": {"version": "12.2.1"},
                },
                "installed": True,
                "version": "12.2.1",
            }}
        )
        metadata['mons']['node1'] = node1_data
        result = common.check_ceph_socket_and_installed_version_parity('node1', node1_data)
        assert result is None
