import os


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


def check_ceph_disk_executable_exists():
    if which('ceph-disk') is None:
        return 'EOSD100', 'ceph-disk exectutable not found'


# Helper functions These might be duplicated with other
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


# remoto magic, needed to execute these functions remotely
if __name__ == '__channelexec__':
    for item in channel:  # noqa
        channel.send(eval(item))  # noqa
