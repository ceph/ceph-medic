import os
import pytest
from ceph_medic.util import configuration
from ceph_medic import log
import logging


class TestLogSetup(object):

    def teardown(self):
        logger = logging.getLogger()
        logger.handlers = []

    def test_barf_when_config_path_does_not_exist(self, tmpdir):
        location = os.path.join(str(tmpdir), 'ceph-medic.conf')
        with open(location, 'w') as _f:
            _f.write("""\n[global]\n--log-path=/bogus/path""")
        config = configuration.load(location)
        with pytest.raises(RuntimeError) as error:
            log.setup(config)
        assert 'value does not exist' in str(error.value)

    def test_create_log_config_correctly(self, tmpdir):
        tmp_log_path = str(tmpdir)
        location = os.path.join(tmp_log_path, 'ceph-medic.conf')
        with open(location, 'w') as _f:
            _f.write("""\n[global]\n--log-path=%s""" % tmp_log_path)
        config = configuration.load(location)
        log.setup(config)
        logger = logging.getLogger()
        # tox has its own logger now, we need to make sure we are talking about the
        # actual configured ones by ceph-medic
        ceph_medic_loggers = [
            i for i in logger.handlers if 'ceph-medic' in getattr(i, 'baseFilename', '')
        ]
        assert len(ceph_medic_loggers) == 1
