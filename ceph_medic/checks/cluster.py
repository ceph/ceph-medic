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

def check_nearfull():
        """
        Checks if the osd capacity is at nearfull
        """
        code = 'ECLS2'
        msg = 'Cluster is nearfull'
        try:
                osd_map = metadata['cluster']['status']['osdmap']['osdmap']
        except KeyError:
                return
        if osd_map['nearfull']:
                return code, msg