from ceph_medic import check, log
import json
import sys
import os
from textwrap import dedent
from tambo import Transport
import remoto
from execnet.gateway_bootstrap import HostNotFound
import ceph_medic
from ceph_medic.decorators import catches
from ceph_medic.generate import generate_inventory
from ceph_medic.util import configuration
from ceph_medic import terminal


class Medic(object):
    _help = """
ceph-medic: A utility to run system checks on a Ceph cluster.

Version: {version}

Global Options:
  --config              Path to a specific configuration file. Overrides the default:
                        $HOME/.cephmedic.conf.
  --cluster             Use a specific cluster name (defaults to 'ceph'). Alternatively,
                        this is inferred from a conf file name in /etc/ceph/
  --ssh-config          Specify an alternate configuration for SSH
  --version, version    Shows the current installed version
  --inventory           Prefer a ceph-ansible inventory (hosts) file instead of default
                        (cwd, /etc/ansible/hosts) locations

{sub_help}

{config_path_header}: {config_path}
{hosts_file_header}: {hosts_file}
{configured_nodes}
    """
    mapper = {
        'check': check.Check,
        # TODO: this needs a bit more work, disabling for now
        #'generate': generate.Generate,
    }

    def __init__(self, argv=None, parse=True):
        if argv is None:
            argv = sys.argv
        if parse:
            self.main(argv)

    def help(self, sub_help=None):
        if self.hosts_file is None:
            hosts_file_header = terminal.red('Loaded Inventory Hosts file')
            hosts_file = 'No hosts file found in cwd, /etc/ansible/, or configured'
        else:
            hosts_file_header = terminal.green('Loaded Inventory Hosts file')
            hosts_file = self.hosts_file
        return self._help.format(
            version=ceph_medic.__version__,
            config_path=self.config_path,
            config_path_header=terminal.green('Loaded Config Path'),
            hosts_file=hosts_file,
            hosts_file_header=hosts_file_header,
            sub_help=sub_help,
            configured_nodes=self.configured_nodes
        )

    @property
    def configured_nodes(self):
        _help = dedent("""
            Configured nodes (loaded from inventory hosts file):
              OSDs: {osd_node_count}
              MONs: {mon_node_count}
              MGRs: {mgr_node_count}
              MDSs: {mds_node_count}
              RGWs: {rgw_node_count}""")
        if self.hosts_file:  # we have nodes that have been loaded
            nodes = ceph_medic.config['nodes']
            return _help.format(
                osd_node_count=len(nodes.get('osds', [])),
                mon_node_count=len(nodes.get('mons', [])),
                mds_node_count=len(nodes.get('mdss', [])),
                mgr_node_count=len(nodes.get('mgrs', [])),
                rgw_node_count=len(nodes.get('rgws', []))
            )
        return ''

    @catches((RuntimeError, KeyboardInterrupt, HostNotFound))
    def main(self, argv):
        options = [
            '--cluster', '--ssh-config', '--inventory',
            '--config',
        ]
        parser = Transport(
            argv, options=options,
            check_help=False,
            check_version=False
        )
        parser.parse_args()

        self.config_path = parser.get('--config', configuration.location())

        # load medic configuration
        loaded_config = configuration.load(path=parser.get('--config', self.config_path))

        # this is the earliest we can have enough config to setup logging
        log.setup(loaded_config)
        # update the module-wide configuration object
        ceph_medic.config.update(configuration.get_overrides(loaded_config))
        ceph_medic.config['file'] = loaded_config

        # SSH config
        ceph_medic.config['ssh_config'] = parser.get('--ssh-config')
        if ceph_medic.config['ssh_config']:
            ssh_config_path = ceph_medic.config['ssh_config']
            if not os.path.exists(ssh_config_path):
                terminal.error("the given ssh config path does not exist: %s" % ssh_config_path)
                sys.exit()

        ceph_medic.config['cluster_name'] = parser.get('--cluster')
        ceph_medic.metadata['cluster_name'] = 'ceph'

        # XXX Can't be if/else through all the connections possible here,
        # generlize, get a helper, cleanup
        # Deployment Type
        if ceph_medic.config['file'].get_safe('global', 'deployment_type') == 'kubernetes':
            k8s_hosts = generate_k8s_hosts()
            ceph_medic.config['nodes'] = k8s_hosts
            ceph_medic.config['hosts_file'] = ':memory:'
            self.hosts_file = ':memory:'

        else:
            # Hosts file
            self.hosts_file = parser.get('--inventory', configuration.get_host_file())

            # find the hosts files, by the CLI first, fallback to the configuration
            # file, and lastly if none of those are found or defined, try to load
            # from well known locations (cwd, and /etc/ansible/)
            loaded_hosts = configuration.load_hosts(
                parser.get('--inventory',
                           ceph_medic.config.get('--inventory', self.hosts_file)))
            ceph_medic.config['nodes'] = loaded_hosts.nodes
            ceph_medic.config['hosts_file'] = loaded_hosts.filename
            self.hosts_file = loaded_hosts.filename

        parser.catch_version = ceph_medic.__version__
        parser.mapper = self.mapper
        parser.catch_help = self.help(parser.subhelp())
        if len(argv) <= 1:
            return parser.print_help()
        ceph_medic.config['config_path'] = self.config_path
        parser.dispatch()
        parser.catches_help()
        parser.catches_version()


# TODO: get this out of here, generalize, cleanup
def generate_k8s_hosts():
    namespace = ceph_medic.config['file'].get_safe('kubernetes', 'namespace', 'rook-ceph')
    local_conn = remoto.connection.get('local')()
    cmd = ['kubectl', '--request-timeout=5', '-n', namespace, 'get', 'pods', '-o', 'json']
    out, err, code = remoto.process.check(local_conn, cmd)
    if code:
        terminal.error('Unable to retrieve the pods via kubectl using command: %s' % ' '.join(cmd))
        raise SystemExit('\n'.join(err))
    pods = json.loads(''.join(out))
    base_inventory = {
        'rgws': [], 'mgrs': [], 'mdss': [], 'clients': [], 'osds': [], 'mons': []
    }
    label_map = {
        'rook-ceph-mgr': 'mgrs',
        'rook-ceph-mon': 'mons',
        'rook-ceph-osd': 'osds',
        'rook-ceph-mds': 'mdss',
        'rook-ceph-rgw': 'rgws',
        'rook-ceph-client': 'clients',
    }

    for item in pods['items']:
        label_name = item['metadata'].get('labels', {}).get('app')
        if not label_name:
            continue
        if label_name in label_map:
            inventory_key = label_map[label_name]
            base_inventory[inventory_key].append(
                {'host': item['metadata']['name'], 'group': None}
            )
    for key, value in dict(base_inventory).items():
        if not value:
            base_inventory.pop(key)
    return base_inventory
