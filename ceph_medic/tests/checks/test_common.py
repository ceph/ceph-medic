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


class TestGetCommonFSID(object):

    def setup(self):
        metadata['cluster_name'] = 'ceph'
        metadata['mons'] = {}

    def teardown(self):
        metadata['mons'] = {}

    def test_get_common_fsid_fails(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1', 'node2'])
        node1_data = make_data({'ceph': {'sockets': {'/var/run/ceph/osd.socket': {'config': {}}}}})
        metadata['mons']['node1'] = node1_data
        assert common.get_common_fsid() == ''

    def test_multiple_fsids_get_one_result(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1', 'node2', 'node3'])
        node1_data = make_data(
            {'ceph': {'sockets': {'/var/run/ceph/osd.socket': {'config': {'fsid': 'aaaa'}}}}}
        )
        node2_data = make_data(
            {'ceph': {'sockets': {'/var/run/ceph/osd.socket': {'config': {'fsid': 'bbbb'}}}}}
        )
        metadata['mons']['node1'] = node1_data
        metadata['mons']['node2'] = node2_data
        metadata['mons']['node3'] = node1_data
        assert common.get_common_fsid() == 'aaaa'

    def test_common_fsid_is_found(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1', 'node2'])
        node1_data = make_data(
            {'ceph': {'sockets': {'/var/run/ceph/osd.socket': {'config': {'fsid': 'bbbb'}}}}}
        )
        node2_data = make_data(
            {'ceph': {'sockets': {'/var/run/ceph/osd.socket': {'config': {'fsid': 'bbbb'}}}}}
        )
        metadata['mons']['node1'] = node1_data
        metadata['mons']['node2'] = node2_data
        assert common.get_common_fsid() == 'bbbb'


class TestCheckFSIDPerDaemon(object):

    def setup(self):
        metadata['cluster_name'] = 'ceph'
        metadata['mons'] = {}

    def test_no_different_fsids_found(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1', 'node2'])
        node1_data = make_data(
            {'ceph': {'sockets': {'/var/run/ceph/osd.socket': {'config': {'fsid': 'bbbb'}}}}}
        )
        node2_data = make_data(
            {'ceph': {'sockets': {'/var/run/ceph/osd.socket': {'config': {'fsid': 'bbbb'}}}}}
        )
        metadata['mons']['node1'] = node1_data
        metadata['mons']['node2'] = node2_data
        assert common.check_fsid_per_daemon('node1', node1_data) is None

    def test_single_different_fsid_found(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1', 'node2', 'node3'])
        node1_data = make_data(
            {'ceph': {'sockets': {'/var/run/ceph/osd.socket': {'config': {'fsid': 'aaaa'}}}}}
        )
        node2_data = make_data(
            {'ceph': {'sockets': {'/var/run/ceph/osd.socket': {'config': {'fsid': 'bbbb'}}}}}
        )
        metadata['mons']['node1'] = node1_data
        metadata['mons']['node2'] = node2_data
        metadata['mons']['node3'] = node1_data
        code, msg = common.check_fsid_per_daemon('node2', node2_data)
        assert 'Found cluster FSIDs from running sockets different than: aaaa' in msg
        assert 'osd.socket : bbbb' in msg

    def test_multiple_different_fsid_found(self, make_nodes, make_data):
        metadata['nodes'] = make_nodes(mons=['node1', 'node2'])
        node1_data = make_data(
            {'ceph': {'sockets': {'/var/run/ceph/osd.socket': {'config': {'fsid': 'bbbb'}}}}}
        )
        node2_data = make_data(
            {'ceph': {'sockets': {
                '/var/run/ceph/osd1.socket': {'config': {'fsid': 'dddd'}},
                '/var/run/ceph/osd3.socket': {'config': {'fsid': 'bbbb'}},
                '/var/run/ceph/osd2.socket': {'config': {'fsid': 'cccc'}},
                }
            }}
        )
        metadata['mons']['node1'] = node1_data
        metadata['mons']['node2'] = node2_data
        code, msg = common.check_fsid_per_daemon('node2', node2_data)
        assert 'Found cluster FSIDs from running sockets different than: bbbb' in msg
        assert 'osd1.socket : dddd' in msg
        assert 'osd2.socket : cccc' in msg


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


class TestMultipleRunningMons(object):

    def test_no_multiple_mons_found(self, data):
        result = common.check_multiple_running_mons(None, data())
        assert result is None

    def test_multiple_mons_found(self, data):
        fake_data = data()
        fake_data['ceph']['sockets'] = {
            '/var/lib/ceph/ceph-mon.0.asok': {},
            '/var/lib/ceph/ceph-mon.1.asok': {},
            '/var/lib/ceph/ceph-mon.2.asok': {},
        }

        code, message = common.check_multiple_running_mons(None, fake_data)
        assert code == 'ECOM10'
        assert 'mon.0' in message
        assert 'mon.1' in message
        assert 'mon.2' in message


class TestColocatedMonsOSDs(object):

    def test_no_colocation_found(self, data):
        result = common.check_colocated_running_mons_osds(None, data())
        assert result is None

    def test_no_osds_found(self, data):
        fake_data = data()
        fake_data['ceph']['sockets'] = {
            '/var/lib/ceph/ceph-mon.0.asok': {},
            '/var/lib/ceph/ceph-mon.1.asok': {},
            '/var/lib/ceph/ceph-mon.2.asok': {},
        }

        result = common.check_colocated_running_mons_osds(None, fake_data)
        assert result is None

    def test_multiple_mons_found(self, data):
        fake_data = data()
        fake_data['ceph']['sockets'] = {
            '/var/lib/ceph/ceph-mon.0.asok': {},
            '/var/lib/ceph/ceph-mon.1.asok': {},
            '/var/lib/ceph/ceph-osd.2.asok': {},
        }

        code, message = common.check_colocated_running_mons_osds(None, fake_data)
        assert code == 'WCOM1'
        assert 'osd.2' in message
        assert 'mon.1' not in message
        assert 'mon.2' not in message

