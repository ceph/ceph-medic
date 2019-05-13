import os

from ceph_medic.remote import functions


def make_test_file(filename, contents=None):
    contents = contents or "foo"
    with open(filename, 'w') as f:
        f.write(contents)


def make_test_tree(path, contents=None, tree=None):
    file1 = os.path.join(path, "file1.txt")
    dir1 = os.path.join(path, "dir1")
    file2 = os.path.join(path, "dir1/file2.txt")
    make_test_file(file1)
    os.mkdir(dir1)
    make_test_file(file2)


class TestStatPath(object):

    def test_stat_file_includes_owner(self, tmpdir):
        filename = os.path.join(str(tmpdir), 'file')
        make_test_file(filename)

        result = functions.stat_path(filename)
        assert "owner" in result

    def test_stat_file_includes_group(self, tmpdir):
        filename = os.path.join(str(tmpdir), 'file')
        make_test_file(filename)

        result = functions.stat_path(filename)
        assert "group" in result

    def test_includes_file_content(self, tmpdir):
        filename = os.path.join(str(tmpdir), 'file')
        make_test_file(filename, contents="foo")

        result = functions.stat_path(filename, get_contents=True)
        assert result["contents"] == "foo"

    def test_exception_is_empty_on_success(self, tmpdir):
        filename = os.path.join(str(tmpdir), 'file')
        make_test_file(filename)

        result = functions.stat_path(filename)
        assert not result["exception"]

    def test_stat_dir(self, tmpdir):
        result = functions.stat_path(str(tmpdir))
        assert result != {}

    def test_no_callables(self, tmpdir):
        result = functions.stat_path(str(tmpdir))
        for value in result.values():
            assert callable(value) is False


class TestStatPathErrors(object):

    def test_captures_exceptions(self):
        result = functions.stat_path('/does/not/exist')
        assert result['exception']['attributes']['errno'] == '2'
        assert result['exception']['name'] in ['FileNotFoundError', 'OSError']


class AttributeLandMine(object):

    @property
    def explode(self):
        raise ValueError('Raising on attribute access')


class TestCaptureException(object):

    def test_exceptions_in_errors_are_ignored(self):
        result = functions.capture_exception(AttributeLandMine())
        assert result['attributes'] == {'explode': None}

    def test_unserializable_attributes(self, factory):
        error = factory(unserial=lambda: True)
        result = functions.capture_exception(error)
        assert '<function ' in result['attributes']['unserial']


class TestPathTree(object):

    def test_skip_dirs(self, tmpdir):
        path = str(tmpdir)
        make_test_tree(path)
        result = functions.path_tree(path, skip_dirs=['dir1'])
        assert "dir1" not in result["dirs"]

    def test_skip_files(self, tmpdir):
        path = str(tmpdir)
        make_test_tree(path)
        result = functions.path_tree(path, skip_files=['file1.txt'])
        assert "file1.txt" not in result["files"]

    def test_includes_path(self, tmpdir):
        path = str(tmpdir)
        make_test_tree(path)
        result = functions.path_tree(path)
        assert result["path"] == path

    def test_includes_files(self, tmpdir):
        path = str(tmpdir)
        make_test_tree(path)
        result = functions.path_tree(path)
        assert "files" in result
        assert os.path.join(path, "file1.txt") in result["files"]

    def test_includes_dirs(self, tmpdir):
        path = str(tmpdir)
        make_test_tree(path)
        result = functions.path_tree(path)
        assert "dirs" in result
        assert os.path.join(path, "dir1") in result["dirs"]
