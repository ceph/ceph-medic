import pytest

from ceph_medic import collector, metadata
from mock import Mock


class FakeConnRemoteModule(object):
    """
    A fake remote_module class to be used
    with Mocked connection objects.

    This class contains stubbed methods for functions
    in ceph_medic.remote.functions which get their return
    value from the class attribute return_values.

    When creating an instance pass a dictionary that maps
    function names to their return values.
    """

    def __init__(self, return_values):
        self.return_values = return_values

    def stat_path(self, *args, **kwargs):
        return self.return_values.get('stat_path', {})

    def path_tree(self, *args, **kwargs):
        return self.return_values.get('path_tree', {})


def get_tree(files=None, dirs=None):
    if files is None:
        files = ["file1.txt"]
    if dirs is None:
        dirs = ["dir1"]
    tree = dict(
        files=files,
        dirs=dirs,
    )
    return tree


def get_mock_connection(data=None, files=None, dirs=None):
    conn = Mock()
    tree = get_tree(files=files, dirs=dirs)
    default_data = dict(
        path_tree=tree
    )
    data = data or default_data
    conn.remote_module = FakeConnRemoteModule(data)
    return conn


class TestCollectPathMetadata(object):

    def test_metadata_includes_dirs(self):
        conn = get_mock_connection()
        result = collector.get_path_metadata(conn, "/some/path")
        assert "dirs" in result

    def test_metadata_includes_files(self):
        conn = get_mock_connection()
        result = collector.get_path_metadata(conn, "/some/path")
        assert "dirs" in result

    def test_metadata_includes_root_path(self):
        conn = get_mock_connection()
        result = collector.get_path_metadata(conn, "/some/path")
        assert "/some/path" in result["dirs"]

    def test_collects_root_path_when_no_files_or_dirs(self):
        conn = get_mock_connection(files=[], dirs=[])
        result = collector.get_path_metadata(conn, "/some/path")
        assert "/some/path" in result["dirs"]


class TestCollectPaths(object):

    @pytest.mark.parametrize(
        'path',
        ['/etc/ceph', '/var/lib/ceph', '/var/run/ceph'],
    )
    def test_includes_paths(self, path, monkeypatch):
        def mock_metadata(conn, p, **kw):
            return dict()
        monkeypatch.setattr(collector, 'get_path_metadata', mock_metadata)
        result = collector.collect_paths(Mock())
        assert path in result


class TestCollectSocketInfo(object):

    def tests_collects_sockets(self, monkeypatch):
        monkeypatch.setattr(collector.remote.commands, 'ceph_socket_version', lambda conn, socket: dict())
        monkeypatch.setattr(collector.remote.commands, 'daemon_socket_config', lambda conn, socket: dict())
        metadata = {
            'paths': {
                '/var/run/ceph': {'files': ['/var/run/ceph/osd.asok']},
            },
        }
        result = collector.collect_socket_info(Mock(), metadata)
        assert '/var/run/ceph/osd.asok' in result

    def test_ignores_unknown_files(self, monkeypatch):
        monkeypatch.setattr(collector.remote.commands, 'ceph_socket_version', lambda conn, socket: dict())
        monkeypatch.setattr(collector.remote.commands, 'daemon_socket_config', lambda conn, socket: dict())
        metadata = {
            'paths': {
                '/var/run/ceph': {'files': ['/var/run/ceph/osd.asok', '/var/run/ceph/osd.log']},
            },
        }
        result = collector.collect_socket_info(Mock(), metadata)
        assert '/var/run/ceph/osd.log' not in result


class TestCollect(object):

    def test_ignores_unknown_group(self):
        metadata["nodes"] = dict(test=[])
        # raises a RuntimeError because all nodes fail to connect
        with pytest.raises(RuntimeError):
            collector.collect()

    def test_collects_node_metadata(self, monkeypatch):
        metadata["nodes"] = {
            "mons": [{"host": "mon0"}],
            "osds": [{"host": "osd0"}],
        }
        metadata["cluster_name"] = "ceph"
        def mock_metadata(conn, hostname, cluster_nodes):
            return dict(meta="data")
        monkeypatch.setattr(collector, "get_connection",
                            lambda host, container=None: Mock())
        monkeypatch.setattr(collector, "get_node_metadata", mock_metadata)
        monkeypatch.setattr(collector, "collect_cluster", lambda x: {})
        collector.collect()
        assert "mon0" in metadata["mons"]
        assert "meta" in metadata["mons"]["mon0"]


class TestGetNodeMetadata(object):

    @pytest.mark.parametrize(
        'key',
        ['ceph', 'devices', 'paths', 'network',],
    )
    def test_collects_metadata(self, key, monkeypatch):
        def mock_metadata(*args, **kwargs):
            return dict(meta="data")
        monkeypatch.setattr(collector, "collect_devices", mock_metadata)
        monkeypatch.setattr(collector, "collect_paths", mock_metadata)
        monkeypatch.setattr(collector, "collect_network", mock_metadata)
        monkeypatch.setattr(collector, "collect_ceph_info", mock_metadata)
        monkeypatch.setattr(collector, "collect_socket_info", mock_metadata)
        monkeypatch.setattr(collector, "collect_ceph_osd_info", mock_metadata)
        result = collector.get_node_metadata(Mock(), "mon0", [])
        assert key in result
