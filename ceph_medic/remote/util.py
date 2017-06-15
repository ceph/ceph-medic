import os
import subprocess


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
