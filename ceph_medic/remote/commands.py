"""
A collection of helpers that will connect to a remote node to run a system
command to return a specific value, instead of shipping a module and executing
functions remotely, this just uses the current connection to execute Popen
"""
from remoto.process import check


def ceph_version(conn):
    try:
        output, _, _ = check(conn, ['ceph', '--version'])
        return output[0]
    except RuntimeError:
        conn.logger.exception('failed to fetch ceph version')


def ceph_is_installed(conn):
    try:
        stdout, stderr, exit_code = check(conn, ['which', 'ceph'])
    except RuntimeError:
        conn.logger.exception('failed to check if ceph is available in the path')
        # XXX this might be incorrect
        return False
    if exit_code != 0:
        return False
    return True
