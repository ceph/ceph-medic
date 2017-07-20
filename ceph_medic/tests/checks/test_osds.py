from ceph_medic.checks import osds


class TestOSDS(object):

    def test_fails_check_ceph_fsid(self):
        data = {'paths': {'/var/lib/ceph': {'files': {
            '/var/lib/ceph/osd/ceph-0/ceph_fsid': {'contents': "fsid1"},
            '/var/lib/ceph/osd/ceph-1/ceph_fsid': {'contents': "fsid2"},
        }}}}
        result = osds.check_osd_ceph_fsid(None, data)
        assert "WOSD1" in result
