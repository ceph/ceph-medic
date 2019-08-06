from mock import Mock
from ceph_medic.remote import commands


class TestCephSocketVersion(object):

    def test_gets_socket_version(self, monkeypatch):
        def mock_check(conn, cmd):
            return (['{"version":"12.2.0"}'], [], 0)
        monkeypatch.setattr(commands, 'check', mock_check)
        result = commands.ceph_socket_version(Mock(), '/var/run/ceph/osd.asok')
        assert 'version' in result

    def test_handles_invalid_json(self, monkeypatch):
        def mock_check(conn, cmd):
            return (['version=12.2.0'], [], 0)
        monkeypatch.setattr(commands, 'check', mock_check)
        result = commands.ceph_socket_version(Mock(), '/var/run/ceph/osd.asok')
        assert result == {}

    def test_handles_non_zero_code(self, monkeypatch):
        def mock_check(conn, cmd):
            return (['version=12.2.0'], [], 1)
        monkeypatch.setattr(commands, 'check', mock_check)
        result = commands.ceph_socket_version(Mock(), '/var/run/ceph/osd.asok')
        assert result == {}


class TestCephVersion(object):

    def test_gets_ceph_version(self, stub_check):
        stub_check(
            (['ceph version 14.1.1 (nautilus)', ''], [], 0),
            commands, 'check')
        result = commands.ceph_version(None)
        assert result == 'ceph version 14.1.1 (nautilus)'

    def test_handles_non_zero_status(self, stub_check, conn):
        stub_check(
            (['error mr. robinson', ''], [], 1),
            commands, 'check')
        result = commands.ceph_version(conn)
        assert result is None


class TestDaemonSocketConfig(object):

    def test_loadable_json(self, stub_check, conn):
        stub_check(
            (['{"config": true}'], [], 0),
            commands, 'check')
        result = commands.daemon_socket_config(conn, '/')
        assert result == {'config': True}

    def test_unloadable_json(self, stub_check, conn):
        stub_check(
            (['{config: []}'], [], 0),
            commands, 'check')
        result = commands.daemon_socket_config(conn, '/')
        assert result == {}

