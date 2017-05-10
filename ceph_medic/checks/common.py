from ceph_medic import metadata


#
# Utilities
#

def get_fsid(data):
    contents = data['paths']['/etc/ceph']['files'][cluster_path]['contents']
    try:
        fsid_line = [i for i in contents.split('\n') if 'fsid' in i][0].split('=')[-1].strip()
    except IndexError:
        return ''
    return fsid_line

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
        msg = '/var/lib/ceph has invalid ownership:  %s:%s' % (owner, group)
        return code, msg


def check_cluster_fsid(host, data):
    code = 'ECOM5'
    msg = 'fsid "%s" is different than host(s): %s'
    cluster_path = '/etc/ceph/%s.conf' % metadata['cluster_name']
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
