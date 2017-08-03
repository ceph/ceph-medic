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


class FakeWriter(object):

    def __init__(self):
        self.calls = []

    def raw(self, string):
        self.calls.append(string)


class TestReport(object):

    def setup(self):
        # clear metadata
        ceph_medic.metadata = base_metadata
        runner.metadata = base_metadata
        runner.metadata['nodes'] = {}
        self.results = runner.Runner()

    def teardown(self):
        # clear metadata
        ceph_medic.metadata = base_metadata
        runner.metadata = base_metadata
        runner.metadata['nodes'] = {}

    def test_reports_errors(self, monkeypatch):
        fake_writer = FakeWriter()
        monkeypatch.setattr(runner.terminal, 'write', fake_writer)
        self.results.errors = ['I am an error']
        runner.report(self.results)
        assert 'While running checks, ceph-medic had unhandled errors' in fake_writer.calls[-1]

    def test_reports_no_errors(self, monkeypatch):
        fake_writer = FakeWriter()
        monkeypatch.setattr(runner.terminal, 'write', fake_writer)
        runner.report(self.results)
        assert fake_writer.calls[0] == '\n0 passed, on 0 hosts'
