import sys
import ceph_medic
from ceph_medic.connection import get_connection
from ceph_medic import runner, collector
from ceph_medic.util import mon
from tambo import Transport


class Check(object):
    help = "Run checks for all the configured nodes in a cluster or hosts file"
    long_help = """
check: Run for all the configured nodes in the configuration

Options:
  --ignore              Comma-separated list of errors and warnings to ignore.
  --monitor             Instead of connecting to hosts with an inventory file
                        connect to a monitor


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
        for daemon, node in ceph_medic.config['nodes'].items():
            header = "\n* %s:\n" % daemon
            body = '\n'.join(["    %s" % n for n in ceph_medic.config['nodes'][daemon]])
            node_section.append(header+body+'\n')
        return self.long_help.format(
            configured_nodes=''.join(node_section),
            config_path=ceph_medic.config['config_path']
        )

    def cluster_nodes(self, monitor):
        # XXX this doesn't make sense to configure. Might want to require
        # a hosts file always for a better/accurate representation of what
        # nodes are (or should be) part of a cluster
        # configured_mon = ceph_medic.config.get('monitor')
        conn = get_connection(monitor)
        nodes = mon.get_cluster_nodes(conn)
        conn.exit()
        return nodes

    def main(self):
        options = ['--ignore', '--monitor']
        parser = Transport(
            self.argv, options=options,
            check_version=False
        )
        parser.catch_help = self._help()

        parser.parse_args()
        if len(self.argv) < 1:
            return parser.print_help()

        configured_monitor = ceph_medic.config.get('--monitor')
        cli_monitor = parser.get('--monitor')
        hosts_file = ceph_medic.config['hosts_file']
        # Always prefer an inventory file even if a monitor is pre-configured
        # (if both are present we need to pick one)
        # If we are getting an explicit CLI flag to consume a monitor then go with that
        # regardless of what the config says.
        if cli_monitor or (configured_monitor and not hosts_file):
            monitor = cli_monitor or configured_monitor
            logger.info(
                'will connect to monitor %s to gather information about nodes in the cluster' % monitor
            )

            cluster_nodes = self.cluster_nodes(monitor)
            ceph_medic.metadata['nodes'] = cluster_nodes
        else:
            # populate the nodes metadata with the configured nodes
            for daemon in ceph_medic.config['nodes'].keys():
                ceph_medic.metadata['nodes'][daemon] = []
            for daemon, nodes in ceph_medic.config['nodes'].items():
                for node in nodes:
                    ceph_medic.metadata['nodes'][daemon].append({'host': node['host']})
        collector.collect()
        test = runner.Runner()
        results = test.run()
        runner.report(results)
