from ceph_medic.checks import common
from ceph_medic import metadata


class TestGetFsid(object):

    def setup(self):
        metadata['cluster_name'] = 'ceph'

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

    def test_fsids_have_parity(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1', 'node2'])
        node1_data = make_data()
        data = self.make_metadata("[global]\nfsid = 1234-lkjh   \n\n[mdss]\ndisabled=true\n")
        node1_data["paths"] = data["paths"]
        metadata['mons']['node1'] = node1_data
        metadata['mons']['node2'] = node1_data
        result = common.check_cluster_fsid('node1', node1_data)
        assert result is None

    def test_fsid_does_not_exist(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1'])
        node1_data = make_data()
        data = self.make_metadata("[global]\nfoo = 1234-lkjh   \n\n[mdss]\ndisabled=true\n")
        node1_data["paths"] = data["paths"]
        metadata['mons']['node1'] = node1_data
        result = common.check_fsid_exists('node1', node1_data)
        assert "'fsid' is missing" in str(result)

    def test_fsid_does_exist(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1'])
        node1_data = make_data()
        data = self.make_metadata("[global]\nfsid = 1234-lkjh   \n\n[mdss]\ndisabled=true\n")
        node1_data["paths"] = data["paths"]
        metadata['mons']['node1'] = node1_data
        result = common.check_fsid_exists('node1', node1_data)
        assert result is None

    def test_ignores_empty_fsid_during_cluster_fsid_check(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1', 'node2'])
        node1_data = make_data()
        node2_data = make_data()
        data = self.make_metadata("[global]\nfsid = 1234-lkjh   \n\n[mdss]\ndisabled=true\n")
        node1_data["paths"] = data["paths"]
        data = self.make_metadata("[global]\nfoo = 1234-lkjh   \n\n[mdss]\ndisabled=true\n")
        node2_data["paths"] = data["paths"]
        metadata['mons']['node1'] = node1_data
        metadata['mons']['node2'] = node2_data
        result = common.check_cluster_fsid('node1', node1_data)
        assert result is None


class TestCephVersionParity(object):

    def setup(self):
        metadata['cluster_name'] = 'ceph'

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

    def test_finds_a_mismatch_of_versions(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1'])
        node1_data = make_data(
            {'ceph': {
                "sockets": {
                    "/var/run/ceph/osd.asok": {"version": {"version": "13.2.0"}},
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
                    "/var/run/ceph/osd.asok": {"version": {"version": "12.2.0"}},
                },
                "installed": True,
                "version": "ceph version 12.2.0 (32ce2a3ae5239ee33d6150705cdb24d43bab910c) luminous (rc)",
            }}
        )
        metadata['mons']['node1'] = node1_data
        result = common.check_ceph_socket_and_installed_version_parity('node1', node1_data)
        assert result is None

    def test_socket_version_is_none(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1'])
        node1_data = make_data(
            {'ceph': {
                "sockets": {
                    "/var/run/ceph/osd.asok": {"version": {}, "config": {}},
                },
                "installed": True,
                "version": "12.2.1",
            }}
        )
        metadata['mons']['node1'] = node1_data
        result = common.check_ceph_socket_and_installed_version_parity('node1', node1_data)
        assert result is None


class TestRgwNumRadosHandles(object):

    def test_value_is_larger_than_accepted(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1'])
        node1_data = make_data(
            {'ceph': {
                "sockets": {
                    "/var/run/ceph/osd.asok": {'version': {}, 'config': {'rgw_num_rados_handles': 3}},
                },
                "installed": True,
                "version": "12.2.1",
            }}
        )
        metadata['mons']['node1'] = node1_data
        result = common.check_rgw_num_rados_handles('node1', node1_data)
        assert result == (
            'WCOM7',
            "rgw_num_rados_handles shouldn't be larger than 1, can lead to memory leaks: osd.asok"
        )

    def test_value_within_range(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1'])
        node1_data = make_data(
            {'ceph': {
                "sockets": {
                    "/var/run/ceph/osd.asok": {'version': {}, 'config': {'rgw_num_rados_handles': 1}},
                },
                "installed": True,
                "version": "12.2.1",
            }}
        )
        metadata['mons']['node1'] = node1_data
        result = common.check_rgw_num_rados_handles('node1', node1_data)
        assert result is None

    def test_multiple_value_is_larger_than_accepted(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1'])
        node1_data = make_data(
            {'ceph': {
                "sockets": {
                    "/var/run/ceph/osd1.asok": {'version': {}, 'config': {'rgw_num_rados_handles': 2}},
                    "/var/run/ceph/osd3.asok": {'version': {}, 'config': {'rgw_num_rados_handles': 3}},
                },
                "installed": True,
                "version": "12.2.1",
            }}
        )
        metadata['mons']['node1'] = node1_data
        result = common.check_rgw_num_rados_handles('node1', node1_data)
        assert 'osd1.asok' in str(result)
        assert 'osd3.asok' in str(result)
