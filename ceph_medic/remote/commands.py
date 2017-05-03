"""
A collection of helpers that will connect to a remote node to run a system
command to return a specific value, instead of shipping a module and executing
functions remotely, this just uses the current connection to execute Popen
"""
from remoto.process import check


def ceph_version(conn):
    output, _, _ = check(conn, ['ceph', '--version'])
    return output[0]


def ceph_is_installed(conn):
    stdout, stderr, exit_code = check(conn, ['which', 'ceph'])
    if exit_code != 0:
        return False
    return True
