import json
from ceph_medic import config, terminal
from remoto import connection, process


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

    pods = json.loads(''.join(out))
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
