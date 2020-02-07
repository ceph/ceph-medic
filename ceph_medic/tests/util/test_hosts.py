import json
import pytest
from ceph_medic.util import hosts, configuration
import ceph_medic
from textwrap import dedent


def failed_check(raise_=True):
    if raise_:
        raise RuntimeError('command failed')
    else:
        return dict(stdout='', stderr='', code=1)


class TestContainerPlatform(object):

    def test_oc_executable_fails(self, monkeypatch, capsys):
        monkeypatch.setattr(hosts.process, 'check', lambda *a: failed_check())
        hosts.container_platform()
        stdout, stderr = capsys.readouterr()
        assert 'Unable to retrieve the pods using command' in stdout
        assert 'oc --request-timeout=5 get -n rook-ceph pods -o json' in stdout

    def test_kubectl_executable_fails(self, monkeypatch, capsys):
        monkeypatch.setattr(hosts.process, 'check', lambda *a: failed_check())
        hosts.container_platform('kubernetes')
        stdout, stderr = capsys.readouterr()
        assert 'Unable to retrieve the pods using command' in stdout
        assert 'kubectl --request-timeout=5 get -n rook-ceph pods -o json' in stdout

    def test_no_context(self, stub_check):
        check = stub_check((['{"items": {}}'], [], 1))
        hosts.container_platform('kubernetes')
        command = check.calls[0]['args'][1]
        assert command == [
            'kubectl', '--request-timeout=5', 'get', '-n',
            'rook-ceph', 'pods', '-o', 'json'
        ]

    def test_garbage_stdout(self, stub_check, capsys):
        stub_check((['could not contact platform'], [], 1))
        with pytest.raises(SystemExit):
            hosts.container_platform('kubernetes')
        stdout, stderr = capsys.readouterr()
        assert 'Unable to load JSON from stdout' in stdout
        assert 'could not contact platform' in stdout

    def test_garbage_stderr(self, stub_check, capsys):
        stub_check(([], ['could not contact platform'], 1))
        with pytest.raises(SystemExit):
            hosts.container_platform('kubernetes')
        stdout, stderr = capsys.readouterr()
        assert 'Unable to load JSON from stdout' in stdout
        assert 'could not contact platform' in stdout

    def test_kubectl_with_context(self, stub_check):
        contents = dedent("""
        [kubernetes]
        context = 87
        """)
        conf = configuration.load_string(contents)
        ceph_medic.config.file = conf
        check = stub_check((['{"items": {}}'], [], 1))
        hosts.container_platform('kubernetes')
        command = check.calls[0]['args'][1]
        assert command == [
            'kubectl', '--context', '87', '--request-timeout=5', 'get', '-n',
            'rook-ceph', 'pods', '-o', 'json'
        ]

    def test_oc_with_context(self, stub_check):
        contents = dedent("""
        [openshift]
        context = 87
        """)
        conf = configuration.load_string(contents)
        ceph_medic.config.file = conf
        check = stub_check((['{"items": {}}'], [], 1))
        hosts.container_platform()
        command = check.calls[0]['args'][1]
        assert command == [
            'oc', '--context', '87', '--request-timeout=5', 'get', '-n',
            'rook-ceph', 'pods', '-o', 'json'
        ]


class TestBasicContainers(object):
    binaries = ['docker', 'podman']

    @pytest.mark.parametrize('binary', binaries)
    def test_executable_fails(
            self, binary, monkeypatch, make_nodes, capsys):
        monkeypatch.setattr(hosts.config, 'nodes', make_nodes(mgrs=['mgr0']))
        monkeypatch.setattr(
            hosts.ceph_medic.connection, 'get_connection',
            lambda *a, **k: None)
        monkeypatch.setattr(
            hosts.process, 'check', lambda *a: failed_check(False))
        hosts.basic_containers(binary)
        stdout, stderr = capsys.readouterr()
        assert 'Unable to list containers on host mgr0' in stdout

    @pytest.mark.parametrize('binary', binaries)
    def test_inspection(
            self, binary, monkeypatch, make_nodes, stub_check, capsys):
        monkeypatch.setattr(ceph_medic.config, 'cluster_name', 'ceph')
        monkeypatch.setattr(hosts.config, 'nodes', make_nodes(mgrs=['mgr0']))
        monkeypatch.setattr(
            hosts.ceph_medic.connection, 'get_connection',
            lambda *a, **k: None)
        fake_list = json.dumps([{'Names': 'mgr0-container'}])
        fake_mgr = json.dumps([{
            'Name': 'mgr0-container',
            'Config': {
                'Env': [
                    'CLUSTER=ceph',
                    'CEPH_DAEMON=MGR',
                ]
            }
        }])
        stub_check([
            ([fake_mgr], [''], 0),
            ([fake_list], [''], 0),
        ])
        result = hosts.basic_containers(binary)
        assert result['mgrs'][0]['host'] == 'mgr0'
        assert result['mgrs'][0]['container'] == 'mgr0-container'
