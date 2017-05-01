import sys
import os

from tambo import Transport
import ceph_doctor
from ceph_doctor import check, generate
from ceph_doctor.decorators import catches
from ceph_doctor.loader import load_config


class Doctor(object):
    _help = """
ceph-doctor: A utility to run system checks on a Ceph cluster.

Version: {version}

Global Options:
--ignore    Comma-separated list of errors and warnings to ignore.

--config    Path to a specific configuration file. Overrides the default:
            $HOME/.cephdoctor.

{sub_help}

Loaded Config Path: {config_path}
    """
    mapper = {
        'check': check.Check,
        'generate': generate.Generate,
    }

    def __init__(self, argv=None, parse=True):
        if argv is None:
            argv = sys.argv
        if parse:
            self.main(argv)

    def help(self, sub_help=None):
        return self._help.format(
            version=ceph_doctor.__version__,
            config_path=self.config_path,
            sub_help=sub_help
        )

    @catches(KeyboardInterrupt)
    def main(self, argv):
        options = ['--ignore', '--config']
        parser = Transport(
            argv, options=options,
            check_help=False,
            check_version=False
        )
        parser.parse_args()
        default_config_path = os.path.expanduser('~/.cephdoctor')
        self.config_path = parser.get('--config', default_config_path)
        parser.catch_version = ceph_doctor.__version__
        parser.mapper = self.mapper
        parser.catch_help = self.help(parser.subhelp())
        if len(argv) <= 1:
            return parser.print_help()
        ceph_doctor.config['config_path'] = self.config_path
        loaded_config = load_config(self.config_path)

        for node_type in ['mon', 'osd', 'mds', 'rgw']:
            ceph_doctor.config['nodes'][node_type] = loaded_config.get(node_type)
        ceph_doctor.config['config_path'] = self.config_path
        parser.dispatch()
        parser.catches_help()
        parser.catches_version()
