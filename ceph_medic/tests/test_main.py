import pytest
import ceph_medic.main


class TestMain(object):
    def test_main(self):
        assert ceph_medic.main

    def test_invalid_ssh_config(self):
        argv = ["ceph-medic", "--ssh-config", "/does/not/exist"]
        with pytest.raises(SystemExit):
            ceph_medic.main.Medic(argv)
