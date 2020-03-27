import pytest
import ceph_medic.main

from mock import patch


class TestMain(object):
    def test_main(self):
        assert ceph_medic.main

    def test_invalid_ssh_config(self, capsys):
        argv = ["ceph-medic", "--ssh-config", "/does/not/exist"]
        with pytest.raises(SystemExit):
            ceph_medic.main.Medic(argv)
        out, _ = capsys.readouterr()
        assert 'the given ssh config path does not exist' in out

    def test_valid_ssh_config(self, capsys):
        ssh_config = '/etc/ssh/ssh_config'
        argv = ["ceph-medic", "--ssh-config", ssh_config]

        def fake_exists(path):
            if path == ssh_config:
                return True
            if path.endswith('cephmedic.conf'):
                return False
            return True

        with patch.object(ceph_medic.main.os.path, 'exists') as m_exists:
            m_exists.side_effect = fake_exists
            ceph_medic.main.Medic(argv)
        out, _  = capsys.readouterr()
        assert 'ssh config path does not exist' not in out
        assert ssh_config == ceph_medic.main.ceph_medic.config.ssh_config
