from ceph_medic import metadata


#
# Error checks
#

def check_osds_exist():
    code = 'ECLS1'
    msg = 'There are no OSDs available'
    osd_count = len(metadata['osds'].keys())
    if not osd_count:
        return code, msg
