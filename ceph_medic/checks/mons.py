from ceph_medic import metadata

#
# Utilities
#

def get_secret(data):
    """
    keyring files look like::

    [mon.]
        key = AQBvaBFZAAAAABAA9VHgwCg3rWn8fMaX8KL01A==
            caps mon = "allow *"

    Fetch that keyring file and extract the actual key, no spaces.
    """
    file_paths = data['paths']['/var/lib/ceph']['files'].keys()
    _path = data['paths']['/var/lib/ceph']['files']
    for _file in file_paths:
        if _file.startswith('/var/lib/ceph/mon/') and _file.endswith('keyring'):
            contents = _path[_file]['contents'].split('\n')
            return [i for i in contents if 'key' in i][0].split(' ')[-1]


def get_monitor_dirs(dirs):
    """
    Find all the /var/lib/ceph/mon/* directories. This is a bit tricky because
    we don't know if there are nested directories (the metadata reports them in
    a flat list).
    We must go through all of them and make sure that by splitting there aren't
    any nested ones and we are only reporting actual monitor dirs.
    """
    # get all the actual monitor dirs
    found = []
    prefix = '/var/lib/ceph/mon/'
    mon_dirs = [d for d in dirs if d.startswith(prefix)]
    for _dir in mon_dirs:
        dirs = _dir.split(prefix)[-1].split('/')
        found.extend(dirs)
    return set(found)


#
# Error Checks
#

def check_mon_secret(host, data):
    code = 'EMON1'
    msg = 'secret key "%s" is different than host(s): %s'
    mismatched_hosts = []

    current_secret = get_secret(data)

    for host, host_data in metadata['mons'].items():
        host_secret = get_secret(host_data)
        if current_secret != host_secret:
            mismatched_hosts.append(host)

    if mismatched_hosts:
        return code, msg % (current_secret, ','.join(mismatched_hosts))

#
# Warning Checks
#

def check_multiple_mon_dirs(host, data):
    code = 'WMON1'
    msg = 'multiple /var/lib/ceph/mon/* dirs found: %s'
    dirs = data['paths']['/var/lib/ceph']['dirs']
    multiple_mons = [d for d in dirs if d.startswith('/var/lib/ceph/mon/')]
    monitor_dirs = get_monitor_dirs(dirs)
    if len(monitor_dirs) > 1:
        return code, msg % ','.join(monitor_dirs)
