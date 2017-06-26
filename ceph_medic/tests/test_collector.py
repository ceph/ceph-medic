import py.test

from ceph_medic import collector
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
    tree = dict(
        files=files or ["dir1"],
        dirs=dirs or ["file1.text"],
    )
    return tree


def get_mock_connection(data=None):
    conn = Mock()
    tree = get_tree()
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


class TestCollectPaths(object):

    @py.test.mark.parametrize(
        'path',
        ['/etc/ceph', '/var/lib/ceph', '/var/run/ceph'],
    )
    def test_includes_paths(self, path, monkeypatch):
        def mock_metadata(conn, p, **kw):
            return dict()
        monkeypatch.setattr(collector, 'get_path_metadata', mock_metadata)
        result = collector.collect_paths(Mock())
        assert path in result

