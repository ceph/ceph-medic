import remoto
import json
import ceph_medic
from ceph_medic import terminal


def get_mon_report(conn):
    command = [
        'ceph',
        '--cluster=%s' % ceph_medic.metadata['cluster_name'],
        'report'
    ]
    out, err, code = remoto.process.check(
        conn,
        command
    )

    if code > 0:
        terminal.error('failed to connect to the cluster to fetch a report from the monitor')
        terminal.error('command: %s' % ' '.join(command))
        for line in err:
            terminal.error(line)
        raise RuntimeError()

    try:
        return json.loads(b''.join(out).decode('utf-8'))
    except ValueError:
        return {}


def get_cluster_nodes(conn):
    """
    Ask a monitor (with a pre-made connection) about all the nodes in
    a cluster. This will be able to get us all known MONs and OSDs.

    It returns a dictionary with a mapping that looks like::

        {
            'mons': [
                {
                    'host': 'node1',
                    'public_ip': '192.168.1.100',
                },
            ],
            'osds': [
                {
                    'host': 'node2',
                    'public_ip': '192.168.1.101',
                },
                {
                    'host': 'node3',
                    'public_ip': '192.168.1.102',
                },
            ]
        }

    """
    report = get_mon_report(conn)
    nodes = {'mons': [], 'osds': []}
    try:
        # XXX Is this really needed? in what case we wouldn't have a monmap
        # with mons?
        mons = report['monmap']['mons']
    except KeyError:
        raise SystemExit(report)
    for i in mons:
        nodes['mons'].append({
            'host': i['name'],
            'public_ip': _extract_ip_address(i['public_addr'])
        })

    osds = report['osd_metadata']
    for i in osds:
        nodes['osds'].append({
            'host': i['hostname'],
            'public_ip': _extract_ip_address(i['front_addr'])
        })

    return nodes


# XXX does not support IPV6

def _extract_ip_address(string):
    """
    Addresses from Ceph reports can come up with subnets and ports using ':'
    and '/' to identify them properly. Parse those types of strings to extract
    just the IP.
    """
    port_removed = string.split(':')[0]
    return port_removed.split('/')[0]
