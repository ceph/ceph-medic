from ceph_medic import metadata
from ceph_medic.util import configuration


#
# Utilities
#

def get_osd_ceph_fsids(data):
    fsids = []
    for file_path in data['paths']['/var/lib/ceph']['files'].keys():
        if "ceph_fsid" in file_path:
            fsids.append(data['paths']['/var/lib/ceph']['files'][file_path]['contents'].strip())
    return set(fsids)


# XXX move out to a central utility module for other checks
def get_ceph_conf(data):
    path = '/etc/ceph/%s.conf' % metadata['cluster_name']
    try:
        conf_file = data['paths']['/etc/ceph']['files'][path]
    except KeyError:
        return None
    return configuration.load_string(conf_file['contents'])


def check_osd_ceph_fsid(host, data):
    code = 'WOSD1'
    msg = "Multiple ceph_fsid values found: %s"

    current_fsids = get_osd_ceph_fsids(data)

    if len(current_fsids) > 1:
        return code, msg % ", ".join(current_fsids)


def check_min_pool_size(host, data):
    code = 'WOSD2'
    msg = 'osd default pool size is set to 1, can potentially lose data'
    conf = get_ceph_conf(data)
    size = conf.get_safe('global', 'osd_pool_default_min_size', '0')
    if int(size) == 1:
        return code, msg
