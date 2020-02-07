import logging
import socket
import remoto
import ceph_medic
from execnet.gateway_bootstrap import HostNotFound

logger = logging.getLogger(__name__)


def get_connection(hostname, username=None, threads=5, use_sudo=None, detect_sudo=True, **kw):
    """
    A very simple helper, meant to return a connection
    that will know about the need to use sudo.
    """
    if kw.get('logger') is False:  # explicitly disable remote logging
        remote_logger = None
    else:
        remote_logger = logging.getLogger(hostname)

    if username:
        hostname = "%s@%s" % (username, hostname)

    if ceph_medic.config.ssh_config:
        hostname = "-F %s %s" % (ceph_medic.config.ssh_config, hostname)
    try:
        deployment_type = kw.get(
            'deployment_type',
            ceph_medic.config.file.get_safe(
                'global', 'deployment_type', 'baremetal')
        )
        conn_obj = remoto.connection.get(deployment_type)
        if deployment_type in ['k8s', 'kubernetes', 'openshift', 'oc']:
            conn = container_platform_conn(hostname, conn_obj, deployment_type)
            # check if conn is ok
            stdout, stderr, code = remoto.process.check(conn, ['true'])
            if code:
                raise HostNotFound(
                    'Remote connection failed while testing connection:\n %s' % '\n'.join(stderr))
        elif deployment_type in ['docker', 'podman']:
            conn = conn_obj(
                hostname,
                container_name=kw['container'],
                detect_sudo=detect_sudo,
            )
        elif deployment_type in ['ssh', 'baremetal']:
            conn = conn_obj(
                hostname,
                logger=remote_logger,
                threads=threads,
                detect_sudo=detect_sudo,
            )
        else:
            raise RuntimeError(
                    'Invalid deployment_type: %s' % deployment_type)
        # Set a timeout value in seconds to disconnect and move on
        # if no data is sent back.
        conn.global_timeout = 300
        # XXX put this somewhere else
        if not ceph_medic.config.cluster_name:
            cluster_conf_files, stderr, exit_code = remoto.process.check(conn, ['ls', '/etc/ceph/'])
            cluster_name = 'ceph'
            if 'ceph.conf' not in cluster_conf_files:
                logger.warning('/etc/ceph/ceph.conf was not found, will try to infer the cluster name')
                for i in cluster_conf_files:
                    if i.endswith('conf'):
                        cluster_name = i.split('.conf')[0]
                        logger.warning('inferred %s as the cluster name', cluster_name)
            ceph_medic.metadata['cluster_name'] = cluster_name
        else:
            ceph_medic.metadata['cluster_name'] = ceph_medic.config.cluster_name
        return conn
    except Exception as error:
        msg = "connecting to host: %s " % hostname
        errors = "resulted in errors: %s %s" % (error.__class__.__name__, error)
        logger.error(msg)
        logger.error(errors)
        raise error


def container_platform_conn(hostname, conn_obj, deployment_type):
    """
    This helper function is only valid for container platform connections like
    OpenShift or Kubernetes. Fetches the configuration needed to properly
    configure the connection object, and then returns it.
    """
    container_platforms = {
        'k8s': 'kubernetes',
        'kubernetes': 'kubernetes',
        'oc': 'openshift',
        'openshift': 'openshift',
    }
    deployment_type = container_platforms.get(deployment_type, 'kubernetes')
    namespace = ceph_medic.config.file.get_safe(deployment_type, 'namespace', 'rook-ceph')
    context = ceph_medic.config.file.get_safe(deployment_type, 'context', None)
    return conn_obj(hostname, namespace, context=context)


def as_bytes(string):
    """
    Ensure that whatever type of string is incoming, it is returned as bytes,
    encoding to utf-8 otherwise
    """
    if isinstance(string, bytes):
        return string
    return string.encode('utf-8', errors='ignore')


def get_local_connection(logger, use_sudo=False):
    """
    Helper for local connections that are sometimes needed to operate
    on local hosts
    """
    return get_connection(
        socket.gethostname(),  # cannot rely on 'localhost' here
        None,
        logger=logger,
        threads=1,
        use_sudo=use_sudo,
        detect_sudo=False
    )
