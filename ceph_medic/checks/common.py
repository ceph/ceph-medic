from collections import Counter
from ceph_medic import metadata, daemon_types
from ceph_medic.util import configuration, str_to_int


#
# Utilities
#

def get_fsid(data):
    # FIXME: might want to load this thing into ConfigParser so that we can fetch
    # information. ceph-deploy is a good example on how to do this. See:
    # https://github.com/ceph/ceph-deploy/blob/master/ceph_deploy/conf/ceph.py
    cluster_path = '/etc/ceph/%s.conf' % metadata['cluster_name']
    try:
        contents = data['paths']['/etc/ceph']['files'][cluster_path]['contents']
    except KeyError:
        return ''
    conf = configuration.load_string(contents)
    try:
        return conf.get_safe('global', 'fsid', '')
    except IndexError:
        return ''


def get_common_fsid():
    """
    Determine what is the most common Cluster FSID. If all of them are the same
    then we are fine, but if there is a mix, we need some base to compare to.
    """
    all_fsids = []

    for daemon_type in daemon_types:
        for node_metadata in metadata[daemon_type].values():
            fsids = get_host_fsids(node_metadata)
            all_fsids.extend(fsids)

    try:
        common_fsid = Counter(all_fsids).most_common()[0][0]
    except IndexError:
        return ''
    return common_fsid


def get_host_fsids(node_metadata):
    """
    Return all the cluster FSIDs found for each socket in a host
    """
    all_fsids = []
    for socket_metadata in node_metadata['ceph']['sockets'].values():
        config = socket_metadata.get('config', {})
        if not config:
            continue
        fsid = config.get('fsid')
        if not fsid:
            continue
        all_fsids.append(fsid)
    return all_fsids


#
# Warning checks
#

def check_colocated_running_mons_osds(host, data):
    code = 'WCOM1'
    msg = 'collocated OSDs with MONs running: %s'
    sockets = data['ceph']['sockets']
    running_mons = []
    running_osds = []
    for socket_name in sockets.keys():
        if "mon." in socket_name:
            running_mons.append(socket_name)
        elif "osd." in socket_name:
            running_osds.append(socket_name)
    if running_mons and running_osds:
        daemons = "\n    %s" % ','.join(running_osds)
        return code, msg % daemons


#
# Error checks
#


def check_ceph_conf_exists(host, data):
    cluster_conf = '/etc/ceph/%s.conf' % metadata['cluster_name']

    files = data['paths']['/etc/ceph']['files'].keys()
    if cluster_conf not in files:
        msg = "%s does not exist" % cluster_conf
        return 'ECOM1', msg


def check_ceph_executable_exists(host, data):
    if data['ceph']['installed'] is False:
        return 'ECOM2', 'ceph executable was not found in common paths when running `which`'


def check_var_lib_ceph_dir(host, data):
    code = 'ECOM3'
    exception = data['paths']['/var/lib/ceph']['dirs']['/var/lib/ceph']['exception']
    if exception:
        msg = '/var/lib/ceph could not be parsed: %s' % exception['repr']
        return code, msg


def check_var_lib_ceph_permissions(host, data):
    code = 'ECOM4'
    group = data['paths']['/var/lib/ceph']['dirs']['/var/lib/ceph']['group']
    owner = data['paths']['/var/lib/ceph']['dirs']['/var/lib/ceph']['owner']
    if group == owner != 'ceph':
        msg = '/var/lib/ceph has invalid ownership:  %s:%s, should be ceph:ceph' % (owner, group)
        return code, msg


def check_cluster_fsid(host, data):
    code = 'ECOM5'
    msg = 'fsid "%s" is different than host(s): %s'
    mismatched_hosts = []

    current_fsid = get_fsid(data)

    # no fsid exists for the current host as defined in ceph.conf, let other
    # checks note about this instead of reporting an empty FSID
    if not current_fsid:
        return

    for daemon, hosts in metadata['nodes'].items():
        for host in hosts:
            hostname = host['host']
            host_fsid = get_fsid(metadata[daemon][hostname])
            if host_fsid and current_fsid != host_fsid:
                mismatched_hosts.append(hostname)

    if mismatched_hosts:
        return code, msg % (current_fsid, ','.join(mismatched_hosts))


def check_ceph_version_parity(host, data):
    code = 'ECOM6'
    msg = '(installed) Ceph version "%s" is different than host(s): %s'
    mismatched_hosts = []
    host_version = data['ceph']['version']
    for daemon, hosts in metadata['nodes'].items():
        for host in hosts:
            hostname = host['host']
            version = metadata[daemon][hostname]['ceph']['version']
            if host_version != version:
                mismatched_hosts.append(hostname)

    if mismatched_hosts:
        return code, msg % (host_version, ','.join(mismatched_hosts))


def check_ceph_socket_and_installed_version_parity(host, data):
    code = 'ECOM7'
    msg = '(installed) Ceph version "%s" is different than version from running socket(s): %s'
    mismatched_sockets = []
    host_version = data['ceph']['version']
    sockets = data['ceph']['sockets']
    for socket, socket_data in sockets.items():
        socket_version = socket_data['version'].get('version')
        if socket_version and socket_version not in host_version:
            mismatched_sockets.append("%s:%s" % (socket, socket_version))

    if mismatched_sockets:
        return code, msg % (host_version, ','.join(mismatched_sockets))


def check_rgw_num_rados_handles(host, data):
    """
    Although this is an RGW setting, the way Ceph handles configurations can
    have this setting be different depending on the daemon. Since we are
    checking on every host and every socket, we are placing this check here
    with common checks.
    """
    code = 'WCOM7'
    msg = "rgw_num_rados_handles shouldn't be larger than 1, can lead to memory leaks: %s"
    sockets = data['ceph']['sockets']
    failed = []
    for socket, socket_data in sockets.items():
        config = socket_data.get('config', {})
        if not config:
            continue
        rgw_num_rados_handles = config.get('rgw_num_rados_handles', 1)
        name = socket.split('/var/run/ceph/')[-1]
        rgw_num_rados_handles = str_to_int(rgw_num_rados_handles)
        if rgw_num_rados_handles > 1:
            failed.append(name)

    if failed:
        return code, msg % ','.join(failed)


def check_fsid_exists(host, data):
    code = 'ECOM8'
    msg = "'fsid' is missing in the ceph configuration"

    current_fsid = get_fsid(data)
    if not current_fsid:
        return code, msg


def check_fsid_per_daemon(host, data):
    """
    In certain deployments types (hi rook!) the FSID will not be present in a
    ceph conf file - it will be passed in *directly* to the daemon as an
    argument. We aren't going to parse arguments, but the admin socket allows
    us to poke inside and check what cluster FSID the daemon is associated
    with.
    """
    code = 'ECOM9'
    msg = 'Found cluster FSIDs from running sockets different than: %s'
    sockets = data['ceph']['sockets']
    common_fsid = get_common_fsid()
    if not common_fsid:  # is this even possible?
        return

    msg = msg % common_fsid
    sockets = data['ceph']['sockets']
    failed = False
    for socket, socket_data in sockets.items():
        config = socket_data.get('config', {})
        if not config:
            continue
        socket_fsid = config.get('fsid')
        if not socket_fsid:
            continue
        if socket_fsid != common_fsid:
            name = socket.split('/var/run/ceph/')[-1]
            msg += '\n    %s : %s' % (name, socket_fsid)
            failed = True
    if failed:
        return code, msg


def check_multiple_running_mons(host, data):
    code = 'ECOM10'
    msg = 'multiple running mons found: %s'
    sockets = data['ceph']['sockets']
    running_mons = []
    for socket_name in sockets.keys():
        if "mon." in socket_name:
            running_mons.append(socket_name)
    if len(running_mons) > 1:
        return code, msg % ','.join(running_mons)
