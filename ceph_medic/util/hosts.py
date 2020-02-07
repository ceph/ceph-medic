import json
import logging
import ceph_medic.connection
from ceph_medic import config, terminal
from remoto import connection, process

logger = logging.getLogger(__name__)


def _platform_options(platform):
    try:
        namespace = config.file.get_safe(platform, 'namespace', 'rook-ceph')
        context = config.file.get_safe(platform, 'context', None)
    except RuntimeError:
        namespace = 'rook-ceph'
        context = None
    return {'namespace': namespace, 'context': context}


def container_platform(platform='openshift'):
    """
    Connect to a container platform (kubernetes or openshift), retrieve all the
    available pods that match the namespace (defaults to 'rook-ceph'), and
    return a dictionary including them, regardless of state.
    """
    local_conn = connection.get('local')()
    options = _platform_options(platform)
    context = options.get('context')
    namespace = options.get('namespace')
    executable = 'oc' if platform == 'openshift' else 'kubectl'

    if context:
        cmd = [executable, '--context', context]
    else:
        cmd = [executable]

    cmd.extend(['--request-timeout=5', 'get', '-n', namespace, 'pods', '-o', 'json'])

    try:
        out, err, code = process.check(local_conn, cmd)
    except RuntimeError:
        out = "{}"
        terminal.error('Unable to retrieve the pods using command: %s' % ' '.join(cmd))
    else:
        if code:
            output = out + err
            for line in output:
                terminal.error(line)

    try:
        pods = json.loads(''.join(out))
    except Exception:
        # Python3 has JSONDecodeError which doesn't exist in Python2
        # Python2 just raises ValueError
        stdout = ''.join(out)
        stderr = ''.join(err)
        logger.exception('Invalid JSON from stdout')
        terminal.error('Unable to load JSON from stdout')
        if stdout:
            logger.error('stdout: %s', stdout)
            terminal.error('stdout: %s' % stdout)
        if stderr:
            logger.error('stderr: %s', stderr)
            terminal.error('stderr: %s' % stderr)
        raise SystemExit(1)

    base_inventory = {
        'rgws': [], 'mgrs': [], 'mdss': [], 'clients': [], 'osds': [], 'mons': []
    }
    label_map = {
        'rook-ceph-mgr': 'mgrs',
        'rook-ceph-mon': 'mons',
        'rook-ceph-osd': 'osds',
        'rook-ceph-mds': 'mdss',
        'rook-ceph-rgw': 'rgws',
        'rook-ceph-client': 'clients',
    }

    for item in pods.get('items', {}):
        label_name = item['metadata'].get('labels', {}).get('app')
        if not label_name:
            continue
        if label_name in label_map:
            inventory_key = label_map[label_name]
            base_inventory[inventory_key].append(
                {'host': item['metadata']['name'], 'group': None}
            )
    for key, value in dict(base_inventory).items():
        if not value:
            base_inventory.pop(key)
    return base_inventory


def basic_containers(deployment_type):
    base_inventory = {
        'rgws': [], 'mgrs': [], 'mdss': [], 'clients': [], 'osds': [],
        'mons': []
    }
    label_map = {
        'OSD': 'osds',
        'OSD_CEPH_VOLUME_ACTIVATE': 'osds',
        'MON': 'mons',
        'MGR': 'mgrs',
        'MDS': 'mdss',
        'RGW': 'rgws',
    }
    metal_hosts = set()
    for nodes in config.nodes.values():
        for node in nodes:
            metal_hosts.add(node['host'])
    for host in metal_hosts:
        logger.debug("listing containers for host %s", host)
        cmd = [deployment_type, 'container', 'ls', '--format', 'json',
               '--no-trunc']
        conn = ceph_medic.connection.get_connection(
            host, deployment_type='ssh')
        out, err, code = process.check(conn, cmd)
        if code:
            terminal.error("Unable to list containers on host %s" % host)
            continue
        container_list = json.loads(''.join(out))
        if not container_list:
            terminal.warning("Host %s had no containers" % host)
            continue
        for container in container_list:
            cmd = [deployment_type, 'container', 'inspect', container['Names']]
            out, err, code = process.check(conn, cmd)
            if code:
                terminal.error(
                    "Unable to inspect container %s on host %s" %
                    (container['Names'], host)
                )
                continue
            detail = json.loads(''.join(out))[0]
            env = dict(
                [s.split('=', 1) for s in detail['Config']['Env']])
            if 'CEPH_DAEMON' not in env:
                continue
            if env.get('CLUSTER') != config.cluster_name:
                continue
            role = env['CEPH_DAEMON']
            if role not in label_map:
                continue
            base_inventory[label_map[role]].append(
                {'host': host, 'container': detail['Name'], 'group': None}
            )
    return base_inventory
