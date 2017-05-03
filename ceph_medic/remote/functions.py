import os
import grp
import pwd
import traceback
import sys


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
            details['attributes'][attr] = getattr(error, attr)
    return details


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

    metadata = {'exception': {}}
    try:
        stat_info = os.stat(path)
        if get_contents and os.path.isfile(path):
            with open(path, 'r') as opened_file:
                metadata['contents'] = opened_file.read()
    except Exception as error:
        return {'exception': capture_exception(error)}

    # get all the stat results back into the metadata
    for attr in dir(stat_info):
        if not attr.startswith('__'):
            metadata[attr] = getattr(stat_info, attr)

    # translate the owner and group:
    metadata['owner'] = pwd.getpwuid(stat_info.st_uid)[0]
    metadata['group'] = grp.getgrgid(stat_info.st_gid)[0]

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

    return dict(path=path, dirs=dirs, files=files)


# remoto magic, needed to execute these functions remotely
if __name__ == '__channelexec__':
    for item in channel:  # noqa
        channel.send(eval(item))  # noqa
