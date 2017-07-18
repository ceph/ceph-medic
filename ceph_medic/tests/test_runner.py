import ceph_medic
from ceph_medic import runner
from ceph_medic.tests import base_metadata


class TestRunner(object):

    def setup(self):
        # clear metadata
        ceph_medic.metadata = base_metadata
        runner.metadata = base_metadata

    def teardown(self):
        # clear metadata
        ceph_medic.metadata = base_metadata
        runner.metadata = base_metadata

    def test_calculate_total_hosts_is_0(self):
        run = runner.Runner()
        assert run.total_hosts == 0

    def test_calculate_hosts_single_daemon_type(self):
        ceph_medic.metadata['nodes']['osds'] = [{'host': 'node1'},{'host': 'node2'}]
        runner.metadata = ceph_medic.metadata
        run = runner.Runner()
        assert run.total_hosts == 2

    def test_count_from_different_daemon_types(self):
        ceph_medic.metadata['nodes']['osds'] = [{'host': 'node1'},{'host': 'node2'}]
        ceph_medic.metadata['nodes']['mons'] = [{'host': 'node3'},{'host': 'node4'}]
        runner.metadata = ceph_medic.metadata
        run = runner.Runner()
        assert run.total_hosts == 4
