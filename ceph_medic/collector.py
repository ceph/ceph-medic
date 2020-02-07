"""
Collect remote information on Ceph daemons, store everything in memory and make
it available as a global part of the module so that other checks can consume it
"""
from ceph_medic import metadata, remote, terminal
from ceph_medic.terminal import loader
from ceph_medic.connection import get_connection
from execnet.gateway_bootstrap import HostNotFound
import logging


logger = logging.getLogger(__name__)


def collect_paths(conn):
    """
    Gather all the interesting paths from the remote system, stat them, and
    capture contents when needed.

    Generates a tree path, using the "path of interest" as key, and appending
    the absolute paths of files in the 'files' key and directories in the
    'dirs' key. A small subset of a tree would look
    very similar to::

        {
            '/etc/ceph': {
                'dirs': {
                    '/etc/ceph/ceph.d': {...},
                },
                'files': {
                    '/etc/ceph/ceph.d/ceph.conf': {...},
                },
            }
        }

    Each file and dir in a path tree will contain a set of keys populated
    mostly by calling ``stat`` on the remote system for that absolute path, in
    addition to capturing contents when "interesting files" are dfined. For
    example, the contents of a ``ceph.conf`` file will always be captured. This
    is how that file would look like in a tree path::


        {
            '/etc/ceph/ceph.d/test.conf':
                {
                    'contents': '[osd]\nosd mkfs type = xfs\nosd mkfs options[...]    ',
                    'exception': {},
                    'group': 'ceph',
                    'n_fields': 16,
                    'n_sequence_fields': 10,
                    'n_unnamed_fields': 3,
                    'owner': 'ceph',
                    'st_atime': 1492721509.572292,
                    'st_blksize': 4096,
                    'st_blocks': 8,
                    'st_ctime': 1492721507.880156,
                    'st_dev': 64768L,
                    'st_gid': 167,
                    'st_ino': 100704475,
                    'st_mode': 33188,
                    'st_mtime': 1492721506.1060133,
                    'st_nlink': 1,
                    'st_rdev': 0,
                    'st_size': 650,
                    'st_uid': 167
                },

        }

    .. note:: ``contents`` is captured using ``file.read()`` so its value will
              be a single line with possible line breaks (if any). For reading and
              parsing that key on each line a split must be done on the line break.

    """
    path_metadata = {}
    paths = {
        "/etc/ceph": {'get_contents': True},
        "/var/lib/ceph": {
            'get_contents': True,
            'skip_files': ['activate.monmap', 'superblock'],
            'skip_dirs': ['tmp', 'current', 'store.db']
        },
        "/var/run/ceph": {'get_contents': False},
    }
    for p, kw in paths.items():
        # Collect metadata about the files and dirs for the given path and assign
        # it back to the path_metadata for the current node
        path_metadata[p] = get_path_metadata(conn, p, **kw)
    return path_metadata


def get_path_metadata(conn, path, **kw):
    # generate the tree
    tree = conn.remote_module.path_tree(
        path,
        kw.get('skip_dirs'),
        kw.get('skip_files'),
        kw.get('get_contents')
    )

    files = {}
    dirs = {}

    for i in tree['files']:
        files[i] = conn.remote_module.stat_path(i, None, None, kw.get('get_contents'))
    for i in tree['dirs']:
        dirs[i] = conn.remote_module.stat_path(i, None, None, False)

    # actual root path
    dirs[path] = conn.remote_module.stat_path(path, None, None, False)

    return {'dirs': dirs, 'files': files}


def get_node_metadata(conn, hostname, cluster_nodes):
    # "import" the remote functions so that remote calls using the
    # functions can be executed
    conn.import_module(remote.functions)

    node_metadata = {'ceph': {}}

    # collect paths and files first
    loader.write('Host: %-*s  collecting: [%s]' % (40, hostname, terminal.yellow('paths')))
    node_metadata['paths'] = collect_paths(conn)
    loader.write('Host: %-*s  collecting: [%s]' % (40, hostname, terminal.green('paths')))

    # TODO: collect network information, passing all the cluster_nodes
    # so that it can check for inter-node connectivity
    loader.write('Host: %-*s  collecting: [%s]' % (40, hostname, terminal.yellow('network')))
    node_metadata['network'] = collect_network(cluster_nodes)
    loader.write('Host: %-*s  collecting: [%s]' % (40, hostname, terminal.green('network')))

    # TODO: collect device information
    loader.write('Host: %-*s  collecting: [%s]' % (40, hostname, terminal.yellow('devices')))
    node_metadata['devices'] = collect_devices()
    loader.write('Host: %-*s  collecting: [%s]' % (40, hostname, terminal.green('devices')))

    # collect ceph information
    loader.write('Host: %-*s  collecting: [%s]' % (40, hostname, terminal.yellow('ceph information')))
    node_metadata['ceph'] = collect_ceph_info(conn)
    node_metadata['ceph']['sockets'] = collect_socket_info(conn, node_metadata)
    node_metadata['ceph']['osd'] = collect_ceph_osd_info(conn)
    loader.write('Host: %-*s  collecting: [%s]' % (40, hostname, terminal.green('ceph information')))

    return node_metadata


def collect():
    """
    The main collecting entrypoint. This function will call all the pieces
    needed to build the complete metadata set of a remote system so that checks
    can consume and verify that data.

    After collection is done, the full contents of the metadata are available
    at ``ceph_medic.metadata``
    """
    cluster_nodes = metadata['nodes']
    loader.write('collecting remote node information')
    total_nodes = 0
    failed_nodes = 0
    has_cluster_data = False

    for node_type, nodes in cluster_nodes.items():
        for node in nodes:
            # check if a node type exists for this node before doing any work:
            try:
                metadata[node_type]
            except KeyError:
                msg = "Skipping node {} from unknown host group: {}".format(node, node_type)
                logger.warning(msg)
                continue

            total_nodes += 1
            hostname = node['host']
            loader.write('Host: %-40s  connection: [%-20s]' % (hostname, terminal.yellow('connecting')))
            # TODO: make sure that the hostname is resolvable, trying to
            # debug SSH issues with execnet is pretty hard/impossible, use
            # util.net.host_is_resolvable
            try:
                logger.debug('attempting connection to host: %s', node['host'])
                conn = get_connection(node['host'], container=node.get('container'))
                loader.write('Host: %-40s  connection: [%-20s]' % (hostname, terminal.green('connected')))
                loader.write('\n')
            except HostNotFound as err:
                logger.exception('connection failed')
                loader.write('Host: %-40s  connection: [%-20s]' % (hostname, terminal.red('failed')))
                loader.write('\n')
                failed_nodes += 1
                if metadata[node_type].get(hostname):
                    metadata[node_type].pop(hostname)
                metadata['nodes'][node_type] = [i for i in metadata['nodes'][node_type] if i['host'] != hostname]
                metadata['failed_nodes'].update({hostname: str(err)})
                continue

            # send the full node metadata for global scope so that the checks
            # can consume this
            metadata[node_type][hostname] = get_node_metadata(conn, hostname, cluster_nodes)
            if node_type == 'mons':  # if node type is monitor, admin privileges are most likely authorized
                if not has_cluster_data:
                    cluster_data = collect_cluster(conn)
                if cluster_data:
                    metadata['cluster'] = cluster_data
                    has_cluster_data = True
            conn.exit()

    if failed_nodes == total_nodes:
        loader.write(terminal.red('Collection failed!') + ' ' *70)
        # TODO: this helps clear out the 'loader' line so that the error looks
        # clean, but this manual clearing should be done automatically
        terminal.write.raw('')
        raise RuntimeError('All nodes failed to connect. Cannot run any checks')
    if failed_nodes:
        loader.write(terminal.yellow('Collection completed with some failed connections' + ' ' *70 + '\n'))
    else:
        loader.write('Collection completed!' + ' ' *70 + '\n')


# Network
#
def collect_network(cluster_nodes):
    """
    Collect node-specific information, but also try to check connectivity to
    other hosts that are passed in as ``cluster_nodes``
    """
    return {}


# Devices
#
def collect_devices():
    """
    Get all the device information from the current node
    """
    return {}


# Ceph
#
def collect_ceph_info(conn):
    result = dict()
    result['version'] = remote.commands.ceph_version(conn)
    result['installed'] = remote.commands.ceph_is_installed(conn)
    return result


def collect_cluster(conn):
    """
    Captures useful cluster information like the status
    """
    result = dict()
    result['status'] = remote.commands.ceph_status(conn)
    return result


# Ceph socket info
#
def collect_socket_info(conn, node_metadata):
    sockets = [socket for socket in node_metadata['paths']['/var/run/ceph']['files']
               if socket.endswith(".asok")]
    result = dict()
    for socket in sockets:
        result[socket] = {'version': {}, 'config': {}}
        result[socket]['version'] = remote.commands.ceph_socket_version(conn, socket)
        result[socket]['config'] = remote.commands.daemon_socket_config(conn, socket)
    return result


# Ceph OSD info
#
def collect_ceph_osd_info(conn):
    result = {'dump': {}}
    result['dump'] = remote.commands.ceph_osd_dump(conn)
    return result
