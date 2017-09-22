from mock import Mock
from ceph_medic.remote import commands


class TestCephSocketVersion(object):

    def test_gets_socket_version(self, monkeypatch):
        def mock_check(conn, cmd):
            return (['{"version":"12.2.0"}'], [], [])
        monkeypatch.setattr(commands, 'check', mock_check)
        result = commands.ceph_socket_version(Mock(), '/var/run/ceph/osd.asok')
        assert 'version' in result

    def test_handles_invalid_json(self, monkeypatch):
        def mock_check(conn, cmd):
            return (['version=12.2.0'], [], [])
        monkeypatch.setattr(commands, 'check', mock_check)
        result = commands.ceph_socket_version(Mock(), '/var/run/ceph/osd.asok')
        assert not result
