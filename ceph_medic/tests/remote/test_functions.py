import os

from ceph_medic.remote import functions


def make_test_file(filename, contents=None):
    contents = contents or "foo"
    with open(filename, 'w') as f:
        f.write(contents)


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
        assert result
