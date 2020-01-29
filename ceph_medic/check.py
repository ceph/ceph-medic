import sys
import ceph_medic
import logging
from ceph_medic import runner, collector
from tambo import Transport

logger = logging.getLogger(__name__)


def as_list(string):
    if not string:
        return []
    string = string.strip(',')

    # split on commas
    string = string.split(',')

    # strip spaces
    return [x.strip() for x in string]


class Check(object):
    help = "Run checks for all the configured nodes in a cluster or hosts file"
    long_help = """
check: Run for all the configured nodes in the configuration

Options:
  --ignore              Comma-separated list of errors and warnings to ignore.


Loaded Config Path: {config_path}

Configured Nodes:
{configured_nodes}
    """

    def __init__(self, argv=None, parse=True):
        self.argv = argv or sys.argv

    @property
    def subcommand_args(self):
        # find where `check` is
        index = self.argv.index('check')
        # slice the args
        return self.argv[index:]

    def _help(self):
        node_section = []
        for daemon, node in ceph_medic.config.nodes.items():
            header = "\n* %s:\n" % daemon
            body = '\n'.join(["    %s" % n for n in ceph_medic.config.nodes[daemon]])
            node_section.append(header+body+'\n')
        return self.long_help.format(
            configured_nodes=''.join(node_section),
            config_path=ceph_medic.config.config_path
        )

    def main(self):
        options = ['--ignore']
        config_ignores = ceph_medic.config.file.get_list('check', '--ignore')
        parser = Transport(
            self.argv, options=options,
            check_version=False
        )
        parser.catch_help = self._help()
        parser.parse_args()
        ignored_codes = as_list(parser.get('--ignore', ''))
        # fallback to the configuration if nothing is defined in the CLI
        if not ignored_codes:
            ignored_codes = config_ignores

        if len(self.argv) < 1:
            return parser.print_help()

        # populate the nodes metadata with the configured nodes
        for daemon in ceph_medic.config.nodes.keys():
            ceph_medic.metadata['nodes'][daemon] = []
        for daemon, nodes in ceph_medic.config.nodes.items():
            for node in nodes:
                node_metadata = {'host': node['host']}
                if 'container' in node:
                    node_metadata['container'] = node['container']
                ceph_medic.metadata['nodes'][daemon].append(node_metadata)

        collector.collect()
        test = runner.Runner()
        test.ignore = ignored_codes
        results = test.run()
        runner.report(results)
        #XXX might want to make this configurable to not bark on warnings for
        # example, setting forcefully for now, but the results object doesn't
        # make a distinction between error and warning (!)
        if results.errors or results.warnings:
            sys.exit(1)
