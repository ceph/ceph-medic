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
    msg = 'osd default pool min_size is set to 1, can potentially lose data'
    conf = get_ceph_conf(data)
    if not conf:  # no ceph.conf found!
        return
    size = conf.get_safe('global', 'osd_pool_default_min_size', '0')
    if int(size) == 1:
        return code, msg


def check_min_osd_nodes(host, data):
    code = 'WOSD3'
    msg = 'OSD nodes might not be enough for a healthy cluster (%s needed, %s found)'
    conf = get_ceph_conf(data)
    if not conf:  # no ceph.conf found!
        return
    default_size = int(conf.get_safe('global', 'osd_pool_default_size', '3'))
    min_size = int(conf.get_safe('global', 'osd_pool_default_min_size', '0'))
    magical_number = default_size + min_size + 1
    osd_nodes = len(metadata['osds'])
    if magical_number > osd_nodes:
        return code, msg % (magical_number, osd_nodes)


def check_reasonable_ratios(host, data):
    code = 'WOSD4'
    msg = 'Ratios have been modified to unreasonable values: %s'
    unreasonable_ratios = []
    reasonable_ratios = {
      "backfillfull_ratio": 0.9,
      "nearfull_ratio": 0.85,
      "full_ratio": 0.95
    }

    dump = data['ceph']['osd'].get('dump', {})
    for name, value in reasonable_ratios.items():
        ratio = dump.get(name)
        if not ratio:
            continue
        if ratio != reasonable_ratios[name]:
            unreasonable_ratios.append(name)
    if unreasonable_ratios:
        msg = msg % ', '.join(sorted(unreasonable_ratios))
        return code, msg
