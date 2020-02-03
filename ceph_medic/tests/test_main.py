import pytest
import ceph_medic.main


class TestMain(object):
    def test_main(self):
        assert ceph_medic.main

    def test_invalid_ssh_config(self, capsys):
        argv = ["ceph-medic", "--ssh-config", "/does/not/exist"]
        with pytest.raises(SystemExit):
            ceph_medic.main.Medic(argv)
        out = capsys.readouterr()
        assert 'the given ssh config path does not exist' in out.out

    def test_valid_ssh_config(self, capsys):
        ssh_config = '/etc/ssh/ssh_config'
        argv = ["ceph-medic", "--ssh-config", ssh_config]
        ceph_medic.main.Medic(argv)
        out = capsys.readouterr()
        assert out.out == ''
        assert ssh_config == ceph_medic.main.ceph_medic.config.ssh_config
