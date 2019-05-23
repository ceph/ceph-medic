import os
import grp
import pwd
import traceback
import sys
import subprocess


# Utilities
#
def capture_exception(error):
    details = {'attributes': {}}
    details['name'] = error.__class__.__name__
    details['repr'] = str(error)
    exc_type, exc_value, exc_traceback = sys.exc_info()
    details['traceback'] = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    for attr in dir(error):
        if not attr.startswith('__'):
            try:
                details['attributes'][attr] = str(getattr(error, attr))
            except Exception:
                # getting an exception here is entirely possible, and since
                # there is no remote logging there is nothing we can do other
                # than eat it up. This section is going through each of the
                # attributes of the exception raised so it is mildly acceptable
                # to skip if anything is breaking
                details['attributes'][attr] = None
    return details


def decoded(string):
    try:
        return string.decode('utf-8')
    except AttributeError:
        return string


# Paths
#
def stat_path(path, skip_dirs=None, skip_files=None, get_contents=False):
    """stat a path on a remote host"""
    # Capture all information about a path, optionally getting the contents of
    # the remote path if it is a file. Exceptions get appended to each dictionary
    # object associated with the path

    # .. note:: Neither ``skip_dirs`` nor ``skip_files`` is used here, but the
    # remote execution of functions use name-based arguments which does not allow
    # the use of ``**kw``
    metadata = {u'exception': {}}
    path = decoded(path)
    try:
        stat_info = os.stat(path)
        if get_contents and os.path.isfile(path):
            with open(path, 'r') as opened_file:
                metadata[u'contents'] = decoded(opened_file.read())
    except Exception as error:
        return {'exception': capture_exception(error)}

    allowed_attrs = [
        'n_fields', 'n_sequence_fields', 'n_unnamed_fields', 'st_atime',
        'st_blksize', 'st_blocks', 'st_ctime', 'st_dev', 'st_gid', 'st_ino',
        'st_mode', 'st_mtime', 'st_nlink', 'st_rdev', 'st_size', 'st_uid'
    ]

    # get all the stat results back into the metadata
    for attr in dir(stat_info):
        attr = decoded(attr)
        if attr in allowed_attrs:
            value = decoded(getattr(stat_info, attr))
            metadata[attr] = value

    # translate the owner and group:
    try:
        metadata[u'owner'] = decoded(pwd.getpwuid(stat_info.st_uid)[0])
    except KeyError:
        metadata[u'owner'] = stat_info.st_uid
    try:
        metadata[u'group'] = decoded(grp.getgrgid(stat_info.st_gid)[0])
    except KeyError:
        metadata[u'group'] = stat_info.st_gid

    return metadata


def path_tree(path, skip_dirs=None, skip_files=None, get_contents=None):
    """generate a path tree"""
    # Generate a tree of paths, including directories and files, recursively, but
    # with the ability to exclude dirs and files with ``skip_dirs`` and
    # ``skip_files``.
    # The tree output groups the files and directories like::

    #     {
    #         'path': '/etc/ceph',
    #         'dirs': ['/etc/ceph/ceph.d/'],
    #         'files': ['/etc/ceph/ceph.d/test.conf', '/etc/ceph/rbdmap']
    #     }

    # .. note:: ``get_contents`` is not used here, but the remote execution of functions
    # use name-based arguments which does not allow the use of ``**kw``
    try:
        path = path.decode('utf-8')
    except AttributeError:
        pass
    skip_files = skip_files or []
    skip_dirs = skip_dirs or []
    files = []
    dirs = []
    # traverse for files and directories, topdown allows us to trim the
    # directories on the fly
    for root, _dirs, _files in os.walk(path, topdown=True):
        _dirs[:] = [d for d in _dirs if d not in skip_dirs]
        for _file in _files:
            absolute_path = os.path.join(root, _file)
            if _file in skip_files:
                continue
            files.append(absolute_path)

        for _dir in _dirs:
            absolute_path = os.path.join(root, _dir)
            dirs.append(absolute_path)

    # using the 'u' prefix forces python3<->python2 compatibility otherwise the
    # keys would be bytes, regardless if input is a str which should've forced
    # a 'str' behavior. The prefix is invalid syntax for Python 3.0 to 3.2, so
    # this will be valid in Python 3.3 and newer and Python 2
    return {u'path': path, u'dirs': dirs, u'files': files}


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
