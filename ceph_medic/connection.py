import logging
import socket
import remoto
from execnet.gateway_bootstrap import HostNotFound
import ceph_medic
from ceph_medic import terminal

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

    if ceph_medic.config.get('ssh_config'):
        hostname = "-F %s %s" % (ceph_medic.config.get('ssh_config'), hostname)
    try:

        conn = remoto.Connection(
            hostname,
            logger=remote_logger,
            threads=threads,
            detect_sudo=detect_sudo,
        )

        # Set a timeout value in seconds to disconnect and move on
        # if no data is sent back.
        conn.global_timeout = 300

        # XXX put this somewhere else
        if not ceph_medic.config['cluster_name']:
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
            ceph_medic.metadata['cluster_name'] = ceph_medic.config['cluster_name']
        return conn
    except Exception as error:
        msg = "connecting to host: %s " % hostname
        errors = "resulted in errors: %s %s" % (error.__class__.__name__, error)
        logger.error(msg)
        logger.error(errors)
        raise error


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
