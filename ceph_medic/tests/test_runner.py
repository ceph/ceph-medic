import pytest
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



class TestReportBasicOutput(object):

    def setup(self):
        # clear metadata
        ceph_medic.metadata = base_metadata
        runner.metadata = base_metadata
        runner.metadata['nodes'] = {}
        runner.Runner().run()

    def test_has_version(self, terminal):
        assert 'Version: ' in terminal.get_output()

    def test_has_cluster_name(self, terminal):
        assert 'Cluster Name: "ceph"' in terminal.get_output()

    def test_has_no_hosts(self, terminal):
        assert 'Total hosts: [0]' in terminal.get_output()

    def test_has_a_header(self, terminal):
        assert '==  Starting remote check session  ==' in terminal.get_output()

    def test_has_no_OSDs(self, terminal):
        assert 'OSDs:    0' in terminal.get_output()

    def test_has_no_MONs(self, terminal):
        assert 'MONs:    0' in terminal.get_output()

    def test_has_no_Clients(self, terminal):
        assert 'Clients:    0' in terminal.get_output()

    def test_has_no_MDSs(self, terminal):
        assert 'MDSs:    0' in terminal.get_output()

    def test_has_no_MGRs(self, terminal):
        assert 'MGRs:       0' in terminal.get_output()

    def test_has_no_RGWs(self, terminal):
        assert 'RGWs:    0' in terminal.get_output()


class TestReportErrors(object):

    def setup(self):
        # clear metadata
        ceph_medic.metadata = base_metadata
        runner.metadata = base_metadata
        runner.metadata['nodes'] = {}

    def test_get_new_lines_in_errors(self, terminal, mon_keyring, data, monkeypatch):
        data_node1 = data()
        data_node2 = data()
        data_node1['paths']['/var/lib/ceph']['files'] = {
            '/var/lib/ceph/mon/ceph-0/keyring': {'contents': mon_keyring()}
        }
        data_node1['paths']['/var/lib/ceph']['dirs'] = {
            '/var/lib/ceph/osd/ceph-10': {},
            '/var/lib/ceph/osd/ceph-11': {},
            '/var/lib/ceph/osd/ceph-12': {},
            '/var/lib/ceph/osd/ceph-13': {},
            '/var/lib/ceph/osd/ceph-0': {},
            '/var/lib/ceph/osd/ceph-1': {},
            '/var/lib/ceph/osd/ceph-2': {},
            '/var/lib/ceph/osd/ceph-3': {},
        }

        data_node2['paths']['/var/lib/ceph']['files'] = {
            '/var/lib/ceph/mon/ceph-1/keyring': {'contents': mon_keyring()},
        }
        data_node2['paths']['/var/lib/ceph']['dirs'] = {
            '/var/lib/ceph/osd/ceph-10': {},
            '/var/lib/ceph/osd/ceph-11': {},
            '/var/lib/ceph/osd/ceph-12': {},
            '/var/lib/ceph/osd/ceph-13': {},
            '/var/lib/ceph/osd/ceph-0': {},
            '/var/lib/ceph/osd/ceph-1': {},
            '/var/lib/ceph/osd/ceph-2': {},
            '/var/lib/ceph/osd/ceph-3': {},
        }

        # set the data everywhere we need it
        ceph_medic.metadata['mons'] = {'node1': data_node1, 'node2': data_node2}
        monkeypatch.setattr(ceph_medic.checks.mons, 'metadata', ceph_medic.metadata)

        runner.Runner().run()
        # Any line that is an error or a warning *must* end with a newline
        for line in terminal.calls:
            if line.lstrip().startswith(('E', 'W')):
                assert line.endswith('\n')
