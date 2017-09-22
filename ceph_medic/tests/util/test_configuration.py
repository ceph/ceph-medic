import os
import pytest
from textwrap import dedent
from ceph_medic.util import configuration


def make_hosts_file(filename, contents=None):
    contents = contents or "[mons]\nmon0\n[osds]\nosd0\n"
    with open(filename, 'w') as f:
        f.write(contents)


class TestFlatInventory(object):

    def test_parses_both_sections(self, tmpdir):
        filename = os.path.join(str(tmpdir), 'hosts')
        make_hosts_file(filename)
        result = configuration.AnsibleInventoryParser(filename)
        assert sorted(result.nodes.keys()) == sorted(['mons', 'osds'])

    def test_populates_hosts(self, tmpdir):
        filename = os.path.join(str(tmpdir), 'hosts')
        make_hosts_file(filename)
        result = configuration.AnsibleInventoryParser(filename).nodes
        assert result['mons'][0]['host'] == 'mon0'
        assert result['osds'][0]['host'] == 'osd0'

    def test_hosts_do_not_get_mixed(self, tmpdir):
        filename = os.path.join(str(tmpdir), 'hosts')
        make_hosts_file(filename)
        result = configuration.AnsibleInventoryParser(filename).nodes
        assert len(result['mons']) == 1
        assert len(result['osds']) == 1

    def test_ignores_unknown_groups(self, tmpdir):
        filename = os.path.join(str(tmpdir), 'hosts')
        contents = """
        [mons]
        mon0

        [test]
        node1
        """
        make_hosts_file(filename, contents)
        result = configuration.AnsibleInventoryParser(filename).nodes
        assert 'test' not in result

    def test_hosts_file_does_not_exist(self):
        with pytest.raises(SystemExit):
            configuration.load_hosts(_path="/fake/path")


class TestNestedInventory(object):

    def test_nested_one_level(self, tmpdir):
        filename = os.path.join(str(tmpdir), 'hosts')
        contents = """
        [mons:children]
        atlanta

        [atlanta]
        mon0
        """
        make_hosts_file(filename, contents)
        result = configuration.AnsibleInventoryParser(filename).nodes
        assert result['mons'][0]['host'] == 'mon0'

    def test_nested_one_level_populates_other_groups(self, tmpdir):
        filename = os.path.join(str(tmpdir), 'hosts')
        contents = """
        [mons:children]
        atlanta

        [atlanta]
        mon0
        """
        make_hosts_file(filename, contents)
        result = configuration.AnsibleInventoryParser(filename).nodes
        assert result['mons'][0]['host'] == 'mon0'

    def test_nested_levels_populates(self, tmpdir):
        filename = os.path.join(str(tmpdir), 'hosts')
        contents = """
        [mons:children]
        us

        [atlanta]
        mon0

        [us:children]
        atlanta
        """
        make_hosts_file(filename, contents)
        result = configuration.AnsibleInventoryParser(filename).nodes
        assert result['mons'][0]['host'] == 'mon0'


class TestLoadString(object):

    def test_loads_valid_ceph_key(self):
        contents = dedent("""
        [global]
        cluster = ceph
        """)
        conf = configuration.load_string(contents)
        assert conf.get_safe('global', 'cluster') == 'ceph'

    def test_loads_key_with_spaces_converted(self):
        contents = dedent("""
        [global]
        some key here = ceph
        """)
        conf = configuration.load_string(contents)
        assert conf.get_safe('global', 'some_key_here') == 'ceph'
