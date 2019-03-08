import pytest
from ceph_medic.util import hosts, configuration
import ceph_medic
from textwrap import dedent


def failed_check():
    raise RuntimeError('command failed')


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
        with pytest.raises(Exception):
            hosts.container_platform('kubernetes')
        stdout, stderr = capsys.readouterr()
        assert 'Invalid JSON on stdout' in stdout

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
