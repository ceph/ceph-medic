from ceph_medic import metadata
from ceph_medic.checks import mons


class TestGetSecret(object):

    def setup(self):
        self.data = {
            'paths': {
                '/var/lib/ceph': {
                    'files': {
                        '/var/lib/ceph/mon/ceph-mon-0/keyring': {
                            'contents': '',
                        }
                    }
                }
            }
        }

    def set_contents(self, string, file_path=None):
        file_path = file_path or '/var/lib/ceph/mon/ceph-mon-0/keyring'
        self.data['paths']['/var/lib/ceph']['files'][file_path]['contents'] = string

    def test_get_secret(self):
        contents = """
        [mon.]
               key = AQBvaBFZAAAAABAA9VHgwCg3rWn8fMaX8KL01A==
               caps mon = "allow *"
        """
        self.set_contents(contents)
        result = mons.get_secret(self.data)
        assert result == 'AQBvaBFZAAAAABAA9VHgwCg3rWn8fMaX8KL01A=='

    def test_get_no_secret_empty_file(self):
        result = mons.get_secret(self.data)
        assert result == ''

    def test_get_no_secret_wrong_file(self):
        contents = """
        [mon.]
               caps mon = "allow *"
        """
        self.set_contents(contents)
        result = mons.get_secret(self.data)
        assert result == ''


class TestGetMonitorDirs(object):

    def test_get_monitor_dirs(self):
        result = mons.get_monitor_dirs([
            '/var/lib/ceph/mon/ceph-mon-1',
            '/var/lib/ceph/something'])

        assert result == set(['ceph-mon-1'])

    def test_cannot_get_monitor_dirs(self):
        result = mons.get_monitor_dirs([
            '/var/lib/ceph/osd/ceph-osd-1',
            '/var/lib/ceph/something'])
        assert result == set([])

    def test_get_monitor_dirs_multiple(self):
        result = mons.get_monitor_dirs([
            '/var/lib/ceph/mon/ceph-mon-1',
            '/var/lib/ceph/mon/ceph-mon-3',
            '/var/lib/ceph/mon/ceph-mon-2',
            '/var/lib/ceph/something'])

        assert result == set(['ceph-mon-1', 'ceph-mon-2', 'ceph-mon-3'])

    def test_get_monitor_dirs_nested_multiple(self):
        result = mons.get_monitor_dirs([
            '/var/lib/ceph/mon/ceph-mon-1',
            '/var/lib/ceph/mon/ceph-mon-1/nested/dir/',
            '/var/lib/ceph/mon/ceph-mon-1/other/nested',
            '/var/lib/ceph/mon/ceph-mon-2',
            '/var/lib/ceph/something'])

        assert result == set(['ceph-mon-1', 'ceph-mon-2'])


class TestOsdDirs(object):

    def test_get_osd_dirs_nested_multiple(self):
        result = mons.get_osd_dirs([
            '/var/lib/ceph/osd/ceph-1',
            '/var/lib/ceph/osd/ceph-1/nested/dir/',
            '/var/lib/ceph/osd/ceph-1/other/nested',
            '/var/lib/ceph/osd/ceph-2',
            '/var/lib/ceph/something'])

        assert result == set(['ceph-1', 'ceph-2'])


class TestMonRecommendedCount(object):

    def test_recommended_count_is_met(self, data):
        metadata['mons'] = dict(('mon%s' % count, []) for count in range(6))
        metadata['cluster_name'] = 'ceph'
        osd_data = data()
        result = mons.check_mon_recommended_count(None, osd_data)
        assert result is None

    def test_recommended_count_is_unmet(self, data):
        metadata['mons'] = dict(('mon%s' % count, []) for count in range(1))
        metadata['cluster_name'] = 'ceph'
        osd_data = data()
        code, message = mons.check_mon_recommended_count(None, osd_data)
        assert code == 'WMON3'
        assert message == 'Recommended number of MONs (3) not met: 1'


class TestMonCountIsOdd(object):

    def test_count_is_odd(self, data):
        metadata['mons'] = dict(('mon%s' % count, []) for count in range(3))
        metadata['cluster_name'] = 'ceph'
        osd_data = data()
        result = mons.check_mon_count_is_odd(None, osd_data)
        assert result is None

    def test_recommended_count_is_unmet(self, data):
        metadata['mons'] = dict(('mon%s' % count, []) for count in range(2))
        metadata['cluster_name'] = 'ceph'
        osd_data = data()
        code, message = mons.check_mon_count_is_odd(None, osd_data)
        assert code == 'WMON4'
        assert message == 'Number of MONs is not an odd number: 2'


class TestSingleMon(object):

    def test_is_single(self, data):
        metadata['mons'] = {'mon.0': []}
        metadata['cluster_name'] = 'ceph'
        code, message = mons.check_for_single_mon(None, data())
        assert code == 'WMON5'
        assert message == 'A single monitor was detected: mon.0'

    def test_is_not_single(self, data):
        metadata['mons'] = dict(('mon%s' % count, []) for count in range(2))
        metadata['cluster_name'] = 'ceph'
        result = mons.check_for_single_mon(None, data())
        assert result is None
