

#
# Utilities
#

def get_osd_ceph_fsids(data):
    fsids = []
    for file_path in data['paths']['/var/lib/ceph']['files'].keys():
        if "ceph_fsid" in file_path:
            fsids.append(data['paths']['/var/lib/ceph']['files'][file_path]['contents'].strip())
    return set(fsids)


def check_osd_ceph_fsid(host, data):
    code = 'WOSD1'
    msg = "Multiple ceph_fsid values found: %s"

    current_fsids = get_osd_ceph_fsids(data)

    if len(current_fsids) > 1:
        return code, msg % ", ".join(current_fsids)
