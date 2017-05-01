import errno
import os
import grp
import pwd
import subprocess


def skip(*args):
    def decorate(f):
        f._skip = args
        return f
    return decorate


def allow(*args):
    def decorate(f):
        f._allow = args
        return f
    return decorate


def check_ceph_conf_exists():
    if not os.path.exists('/etc/ceph/ceph.conf'):
        return 'ECOM101', '/etc/ceph/ceph.conf does not exist'


def check_ceph_executable_exists():
    if which('ceph') is None:
        return 'ECOM102', 'ceph executable was not found in common paths'


def check_var_lib_ceph_dir():
    try:
        os.stat('/var/lib/ceph')
    except OSError as error:
        if error.errno == errno.ENOENT:
            return 'ECOM103', '/var/lib/ceph does not exist'
        if error.errno == errno.EPERM:
            return 'ECOM104', '/var/lib/ceph is not readable'


@allow('hammer')
def check_root_var_lib_ceph_permissions():
    try:
        stat_info = os.stat('/var/lib/ceph')
    except OSError:
        pass  # some other check will catch this

    uid = stat_info.st_uid
    gid = stat_info.st_gid

    user = pwd.getpwuid(uid)[0]
    group = grp.getgrgid(gid)[0]
    errors = []
    if user != 'root':
        errors.append(('ECOM105', '/var/lib/ceph is not owned by root user (owned by %s)' % user))
    if group != 'root':
        errors.append(('ECOM106', '/var/lib/ceph is not owned by root group (owned by %s)' % user))
    if errors:
        return errors


@skip('hammer')
def check_var_lib_ceph_permissions():
    try:
        stat_info = os.stat('/var/lib/ceph')
    except OSError:
        pass  # some other check will catch this

    uid = stat_info.st_uid
    gid = stat_info.st_gid

    user = pwd.getpwuid(uid)[0]
    group = grp.getgrgid(gid)[0]
    errors = []
    if user != 'ceph':
        errors.append(('ECOM105', '/var/lib/ceph is not owned by ceph user (owned by %s)' % user))
    if group != 'ceph':
        errors.append(('ECOM106', '/var/lib/ceph is not owned by ceph group (owned by %s)' % user))
    if errors:
        return errors

# Helper functions. These might be duplicated with other
# 'remote' modules since they need to be shipped all together.


def which(executable):
    """find the location of an executable"""
    locations = (
        '/usr/local/bin',
        '/bin',
        '/usr/bin',
        '/usr/local/sbin',
        '/usr/sbin',
        '/sbin',
    )

    for location in locations:
        executable_path = os.path.join(location, executable)
        if os.path.exists(executable_path):
            return executable_path


def run(command):
    """
    run a command, return stdout, stderr, and exit code.
    """
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True
    )
    stdout = process.stdout.read().splitlines()
    stderr = process.stderr.read().splitlines()
    returncode = process.wait()

    return stdout, stderr, returncode


# remoto magic, needed to execute these functions remotely
if __name__ == '__channelexec__':
    for item in channel:  # noqa
        channel.send(eval(item))  # noqa
