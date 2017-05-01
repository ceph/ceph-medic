

# Helper functions. These might be duplicated with other
# 'remote' modules since they need to be shipped all together.


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


# remoto magic, needed to execute these functions remotely
if __name__ == '__channelexec__':
    for item in channel:  # noqa
        channel.send(eval(item))  # noqa
