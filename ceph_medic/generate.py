from __future__ import print_function
import sys
import ceph_medic
from ceph_medic.connection import get_connection
import remoto
import json
from tambo import Transport


def generate_inventory(inventory, to_stdout=False, tmp_dir=None):
    """
    Generates a host file to use with an ansible-playbook call.

    The first argument is a dictionary mapping that contains the group name as
    the key and a list of hostnames as values

    For example:

        {'mons': ['mon.host'], 'osds': ['osd1.host', 'osd1.host']}
    """
    result = []
    for section, hosts in inventory.items():
        group_name = section
        result.append("[{0}]".format(group_name))
        if not isinstance(hosts, list):
            hosts = [hosts]
        result.extend(hosts)
    result_str = "\n".join(result) + "\n"
    # if not None the NamedTemporaryFile will be created in the given directory
    if to_stdout:
        print(result_str)
        return
    with open('hosts_file', 'w') as hosts_file:
        hosts_file.write(result_str)


def get_mon_report(conn):
    out, err, code = remoto.process.check(
        conn,
        [
            'ceph',
            'report'
        ],
    )

    if code > 0:
        for line in err:
            print(line)

    try:
        return json.loads(b''.join(out).decode('utf-8'))
    except ValueError:
        return {}


class Generate(object):
    help = "Create a hosts file (Ansible compatible) from the information on a running Ceph cluster"
    long_help = """
Create a hosts file (Ansible compatible) from the information on a running Ceph
cluster.

Usage:

    ceph-medic generate [/path/to/ceph.conf]
    ceph-medic generate [MONITOR HOST]

Loaded Config Path: {config_path}

    """

    def __init__(self, argv=None, parse=True):
        self.argv = argv or sys.argv

    def _help(self):
        skip_internal = ['__file__', 'config_path', 'verbosity']
        node_section = []
        for daemon, node in ceph_medic.config['nodes'].items():
            if daemon in skip_internal or not node:
                continue
            header = "\n* %s:\n" % daemon
            body = '\n'.join(["    %s" % n for n in ceph_medic.config['nodes'][daemon].keys()])
            node_section.append(header+body+'\n')
        return self.long_help.format(
            config_path=ceph_medic.config['config_path']
        )

    def main(self):
        options = ['--stdout']
        parser = Transport(
            self.argv, options=options,
            check_version=False
        )
        parser.catch_help = self._help()

        parser.parse_args()

        if len(self.argv) == 1:
            raise SystemExit("A monitor hostname or a ceph.conf file is required as an argument")

        node = self.argv[-1]
        inventory = {}

        with get_connection(node) as conn:
            report = get_mon_report(conn)
            try:
                mons = report['monmap']['mons']
            except KeyError:
                raise SystemExit(report)
            inventory['mons'] = [i['name'] for i in mons]
            osds = report['osd_metadata']
            inventory['osds'] = [i['hostname'] for i in osds]

        if not inventory:
            raise SystemExit('no hosts where found from remote monitor node: %s' % node)

        generate_inventory(inventory, to_stdout=parser.get('--stdout'))
        conn.exit()
        return
