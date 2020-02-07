"""
A collection of helpers that will connect to a remote node to run a system
command to return a specific value, instead of shipping a module and executing
functions remotely, this just uses the current connection to execute Popen
"""
import json
from remoto.process import check


def ceph_version(conn):
    try:
        output, _, exit_code = check(conn, ['ceph', '--version'])
        if exit_code != 0:
            conn.logger.error('Non zero exit status received, unable to retrieve information')
            return
        return output[0]
    except RuntimeError:
        conn.logger.exception('failed to fetch ceph version')


def ceph_socket_version(conn, socket):
    try:
        result = dict()
        output, _, exit_code = check(
            conn,
            ['ceph', '--admin-daemon', socket, '--format', 'json', 'version']
        )
        if exit_code != 0:
            conn.logger.error('Non zero exit status received, unable to retrieve information')
            return result
        try:
            result = json.loads(output[0])
        except ValueError:
            conn.logger.exception(
                "failed to fetch ceph socket version, invalid json: %s" % output[0]
            )
        return result
    except RuntimeError:
        conn.logger.exception('failed to fetch ceph socket version')


def ceph_status(conn):
    try:                # collects information using ceph -s
        stdout, stderr, exit_code = check(conn, ['sudo', 'ceph', '-s', '--format', 'json'])
        result = dict()
        try:
            result = json.loads(''.join(stdout))
        except ValueError:
            conn.logger.exception("failed to fetch ceph status, invalid json: %s" % ''.join(stdout))

        if exit_code == 0:
            return result
        else:
            return {}

    except RuntimeError:
        conn.logger.exception('failed to fetch ceph status')


def ceph_osd_dump(conn):
    try:
        stdout, stderr, exit_code = check(conn, ['sudo', 'ceph', 'osd', 'dump', '--format', 'json'])
        result = dict()
        if exit_code != 0:
            conn.logger.error('could not get osd dump from ceph')
            if stderr:
                for line in stderr:
                    conn.logger.error(line)
            return result
        try:
            result = json.loads(''.join(stdout))
        except ValueError:
            conn.logger.exception("failed to fetch osd dump, invalid json: %s" % ''.join(stdout))

        return result

    except RuntimeError:
        conn.logger.exception('failed to fetch ceph osd dump')


def daemon_socket_config(conn, socket):
    """
    Capture daemon-based config from the socket
    """
    try:
        output, _, exit_code = check(
            conn,
            ['ceph', '--admin-daemon', socket, 'config', 'show', '--format', 'json']
        )
        if exit_code != 0:
            conn.logger.error('Non zero exit status received, unable to retrieve information')
            return
        result = dict()
        try:
            result = json.loads(output[0])
        except ValueError:
            conn.logger.exception(
                "failed to fetch ceph configuration via socket, invalid json: %s" % output[0]
            )
        return result
    except RuntimeError:
        conn.logger.exception('failed to fetch ceph configuration via socket')


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
