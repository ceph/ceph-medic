from ceph_medic import metadata
from ceph_medic.util import configuration


#
# Utilities
#

def get_fsid(data):
    # FIXME: might want to load this thing into ConfigParser so that we can fetch
    # information. ceph-deploy is a good example on how to do this. See:
    # https://github.com/ceph/ceph-deploy/blob/master/ceph_deploy/conf/ceph.py
    cluster_path = '/etc/ceph/%s.conf' % metadata['cluster_name']
    contents = data['paths']['/etc/ceph']['files'][cluster_path]['contents']
    conf = configuration.load_string(contents)
    try:
        return conf.get_safe('global', 'fsid', '')
    except IndexError:
        return ''

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

    for daemon, hosts in metadata['nodes'].items():
        for host in hosts:
            hostname = host['host']
            host_fsid = get_fsid(metadata[daemon][hostname])
            if current_fsid != host_fsid:
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
        rgw_num_rados_handles = socket_data['config'].get('rgw_num_rados_handles', 1)
        name = socket.split('/var/run/ceph/')[-1]
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
