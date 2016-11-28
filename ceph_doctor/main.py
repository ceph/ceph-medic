import sys

from tambo import Transport
import delgado
from ceph_doctor.decorators import catches


class Doctor(object):
    _help = """
ceph-doctor: A utility to run system checks on a Ceph cluster.

Version: %s

Global Options:
--ignore    Comma-separated list of errors and warnings to ignore.

--config    Path to a specific configuration file. Overrides the default:
            $HOME/.ceph_doctor.

    """

    def __init__(self, argv=None, parse=True):
        if argv is None:
            argv = sys.argv
        if parse:
            self.main(argv)

    def help(self):
        return self._help % (delgado.__version__, self.plugin_help)

    @catches(KeyboardInterrupt)
    def main(self, argv):
        options = ['--ignore', '--config']
        parser = Transport(argv, mapper=self.mapper,
                           options=options, check_help=False,
                           check_version=False)
        parser.parse_args()
        parser.catch_help = self.help()
        parser.catch_version = delgado.__version__
        parser.mapper = self.mapper
        if len(argv) <= 1:
            return parser.print_help()
        parser.dispatch()
        parser.catches_help()
        parser.catches_version()
