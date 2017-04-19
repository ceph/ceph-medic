import socket


def host_is_resolvable(hostname, _socket=None):
    _socket = _socket or socket  # just used for testing
    try:
        _socket.getaddrinfo(hostname, 0)
    except _socket.gaierror:
        msg = "hostname: %s is not resolvable" % hostname
        raise RuntimeError(msg)
    return True
