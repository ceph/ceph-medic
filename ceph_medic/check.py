import sys
import ceph_medic
from ceph_medic.connection import get_connection
from ceph_medic import remote, runner, terminal
from ceph_medic.util import mon, net
from ceph_medic.checks import common
from tambo import Transport
from remoto import process
from execnet.gateway_bootstrap import HostNotFound


class Check(object):
    help = "Run checks for all the configured nodes in a cluster or hosts file"
    long_help = """
check: Run for all the configured nodes in the configuration

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
        configured_nodes = str(ceph_medic.config.keys())
        skip_internal = ['__file__', 'config_path', 'verbosity']
        node_section = []
        for daemon, node in ceph_medic.config['nodes'].items():
            if daemon in skip_internal or not node:
                continue
            header = "\n* %s:\n" % daemon
            body = '\n'.join(["    %s" % n for n in ceph_medic.config['nodes'][daemon].keys()])
            node_section.append(header+body+'\n')
        return self.long_help.format(
            configured_nodes=''.join(node_section),
            config_path=ceph_medic.config['config_path']
        )

    def cluster_nodes(self, monitor):
        configured_nodes = ceph_medic.config['nodes']
        configured_mon = ceph_medic.config.get('monitor')
        if self.argv > 1: # we probably are getting a monitor as an argument
            configured_mon = self.argv[-1]
        conn = get_connection(monitor)
        nodes = mon.get_cluster_nodes(conn)
        conn.exit()
        return nodes

    def main(self):
        options = ['--ignore', '--config']
        parser = Transport(
            self.argv, options=options,
            check_version=False
        )
        parser.catch_help = self._help()

        parser.parse_args()
        if len(self.argv) < 1:
            return parser.print_help()

        module_map = {
            # XXX is there anything we can validate on mds nodes?
            #'mds': remote.mds,
            'mon': remote.mon,
            'osd': remote.osd,
            # XXX we can't get rgw nodes via the mons, they are always separate
            # this would need to rely on pre-configured nodes to check, maybe
            # with the hosts file (ceph-ansible style)
            #'rgw': remote.rgw,
        }

        # TODO: allow to consume a hosts file from ansible for pre-configured
        # nodes to check instead of going with the monitor always
        monitor = ceph_medic.config.get('monitor')
        if len(self.subcommand_args) > 1: # we probably are getting a monitor as an argument
            monitor = self.argv[-1]
            terminal.info(
                'will connect to monitor %s to gather information about nodes in the cluster' % monitor
            )

            cluster_nodes = self.cluster_nodes(monitor)
            ceph_medic.metadata['nodes'] = cluster_nodes
        import collector
        collector.collect()
        runner.full_run()
