from ceph_medic import metadata
from ceph_medic.util import configuration

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

    .. warning:: If multiple mon dirs exist, this utility will pick the first
    one it finds. There are checks that will complain about multiple mon dirs
    """
    file_paths = data['paths']['/var/lib/ceph']['files'].keys()
    _path = data['paths']['/var/lib/ceph']['files']
    for _file in file_paths:
        if _file.startswith('/var/lib/ceph/mon/') and _file.endswith('keyring'):
            contents = _path[_file]['contents']
            conf = configuration.load_string(contents)
            try:
                return conf.get_safe('mon.', 'key', '').split('\n')[0]
            except IndexError:
                # is it really possible to get a keyring file that doesn't
                # have a monitor secret?
                return ''


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
        # splitting on prefix[-1] will give us:
        # 'ceph-mon-1/maybe/nested' or 'ceph-mon-1'
        dirs = _dir.split(prefix)[-1].split('/')
        # splitting again on '/' and using the first part will ensure we only
        # get the dir
        found.append(dirs[0])
    return set(found)


def get_osd_dirs(dirs):
    """
    Find all the /var/lib/ceph/osd/* directories. This is a bit tricky because
    we don't know if there are nested directories (the metadata reports them in
    a flat list).
    We must go through all of them and make sure that by splitting there aren't
    any nested ones and we are only reporting actual monitor dirs.
    """
    # get all the actual monitor dirs
    found = []
    prefix = '/var/lib/ceph/osd/'
    osd_dirs = [d for d in dirs if d.startswith(prefix)]
    for _dir in osd_dirs:
        # splitting on prefix[-1] will give us:
        # 'ceph-1/maybe/nested' or 'ceph-1'
        dirs = _dir.split(prefix)[-1].split('/')
        # splitting again on '/' and using the first part will ensure we only
        # get the dir
        found.append(dirs[0])
    return set(found)
#
# Error Checks
#


def check_mon_secret(host, data):
    code = 'EMON1'
    msg = 'secret key "%s" is different than host(s): %s'
    mismatched_hosts = []

    current_secret = get_secret(data)
    if not current_secret:
        # there is no file for the current host, so we can't compare
        return

    for host, host_data in metadata['mons'].items():
        host_secret = get_secret(host_data)
        if not host_secret:
            # cannot compare with another host that may not have the secret
            continue
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
    monitor_dirs = get_monitor_dirs(dirs)
    if len(monitor_dirs) > 1:
        return code, msg % ','.join(monitor_dirs)


def check_mon_collocated_with_osd(host, data):
    code = 'WMON2'
    msg = 'collocated OSDs found: %s'
    dirs = data['paths']['/var/lib/ceph']['dirs']
    osd_dirs = get_osd_dirs(dirs)
    if len(osd_dirs):
        return code, msg % ','.join(osd_dirs)


def check_mon_recommended_count(host, data):
    code = 'WMON3'
    msg = 'Recommended number of MONs (3) not met: %s'
    mon_count = len(metadata['mons'].keys())
    if mon_count < 3:
        return code, msg % mon_count


def check_mon_count_is_odd(host, data):
    code = 'WMON4'
    msg = 'Number of MONs is not an odd number: %s'
    mon_count = len(metadata['mons'].keys())
    if mon_count % 2 == 0:
        return code, msg % mon_count


def check_for_single_mon(host, data):
    code = 'WMON5'
    msg = 'A single monitor was detected: %s'
    monitors = list(metadata['mons'].keys())
    if len(monitors) == 1:
        return code, msg % monitors.pop()
