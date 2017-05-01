import sys
import ceph_doctor
from ceph_doctor.connection import get_connection
from ceph_doctor import remote
from ceph_doctor.remote import util
from tambo import Transport


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

    def _help(self, ):
        configured_nodes = str(ceph_doctor.config.keys())
        skip_internal = ['__file__', 'config_path', 'verbosity']
        node_section = []
        for daemon, node in ceph_doctor.config['nodes'].items():
            if daemon in skip_internal or not node:
                continue
            header = "\n* %s:\n" % daemon
            body = '\n'.join(["    %s" % n for n in ceph_doctor.config['nodes'][daemon].keys()])
            node_section.append(header+body+'\n')
        return self.long_help.format(
            configured_nodes=''.join(node_section),
            config_path=ceph_doctor.config['config_path']
        )

    def main(self):
        options = ['--ignore', '--config']
        parser = Transport(
            self.argv, options=options,
            check_version=False
        )
        parser.catch_help = self.help()

        parser.parse_args()

        if len(self.argv) < 1:
            return parser.print_help()

        module_map = {
            #'mds': remote.mds,
            'mon': remote.mon,
            'osd': remote.osd,
            #'rgw': remote.rgw,
        }

        configured_nodes = ceph_doctor.config['nodes']
        for daemon in configured_nodes:
            configured_node = configured_nodes[daemon] or {}
            for node in configured_node.keys():
                conn = get_connection(node)
                # import common first
                conn.import_module(remote.common)
                callables = [i for i in dir(conn.remote_module.module) if i.startswith('check_')]
                print
                print " %s" % node
                for function in callables:
                    try:
                        result = getattr(conn.remote_module, function)()
                        if result:
                            if isinstance(result, list):
                                for i in result:
                                    print "    %s" % i
                            else:
                                print "    %s" % result
                    except Exception as err:
                        print node, err
                conn.import_module(module_map[daemon])
                callables = [i for i in dir(conn.remote_module.module) if i.startswith('check_')]
                for function in callables:
                    try:
                        result = getattr(conn.remote_module, function)()
                        if result:
                            if isinstance(result, list):
                                for i in result:
                                    print "    %s" % i
                            else:
                                print "    %s" % result
                    except Exception as err:
                        print node, err
                        raise

                conn.exit()
