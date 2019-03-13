import sys


class colorize(str):
    """
    Pretty simple to use::

        colorize.make('foo').bold
        colorize.make('foo').green
        colorize.make('foo').yellow
        colorize.make('foo').red
        colorize.make('foo').blue

    Otherwise you could go the long way (for example if you are
    testing this class)::

        string = colorize('foo')
        string._set_attributes()
        string.red

    """

    def __init__(self, string):
        self.stdout = sys.__stdout__
        self.appends = ''
        self.prepends = ''
        self.isatty = self.stdout.isatty()

    def _set_attributes(self):
        """
        Sets the attributes here because the str class does not
        allow to pass in anything other than a string to the constructor
        so we can't really mess with the other attributes.
        """
        for k, v in self.__colors__.items():
            setattr(self, k, self.make_color(v))

    def make_color(self, color):
        if not self.isatty or self.is_windows:
            return self
        return color + self + '\033[0m' + self.appends

    @property
    def __colors__(self):
        return  dict(
                blue   = '\033[34m',
                green  = '\033[92m',
                yellow = '\033[33m',
                red    = '\033[91m',
                bold   = '\033[1m',
                ends   = '\033[0m'
        )

    @property
    def is_windows(self):
        if sys.platform == 'win32':
            return True
        return False

    @classmethod
    def make(cls, string):
        """
        A helper method to return itself and workaround the fact that
        the str object doesn't allow extra arguments passed in to the
        constructor
        """
        obj = cls(string)
        obj._set_attributes()
        return obj

#
# Common string manipulations
#
red_arrow = colorize.make('-->').red
blue_arrow = colorize.make('-->').blue
yellow = lambda x: colorize.make(x).yellow
blue = lambda x: colorize.make(x).blue
green = lambda x: colorize.make(x).green
red = lambda x: colorize.make(x).red
bold = lambda x: colorize.make(x).bold


CRITICAL = 5
ERROR = 4
WARNING = 3
INFO = 2
DEBUG = 1

_level_names = {
    CRITICAL : 'critical',
    WARNING  : 'warning',
    INFO     : 'info',
    ERROR    : 'error',
    DEBUG    : 'debug'
}

_reverse_level_names = dict((v, k) for (k, v) in _level_names.items())

_level_colors = {
    'remote'   : 'bold',
    'critical' : 'red',
    'warning'  : 'yellow',
    'info'     : 'blue',
    'debug'    : 'blue',
    'error'    : 'red'
}


class _Write(object):

    def __init__(self, _writer=None, prefix='', suffix='', clear_line=False, flush=False):
        self._writer = _writer or sys.stdout
        self.suffix = suffix
        self.prefix = prefix
        self.flush = flush
        self.clear_line = clear_line

    def bold(self, string):
        self.write(bold(string))

    def raw(self, string):
        self.write(string + '\n')

    def write(self, line):
        padding = ''
        if self.clear_line:
            if len(line) > 80:
                padding = ' ' * 10
            else:
                padding = ' ' * (80 - len(line))
        line = line + padding
        self._writer.write(self.prefix + line + self.suffix)
        if self.flush:
            self._writer.flush()


write = _Write()
loader = _Write(prefix='\r', clear_line=True)


class LogMessage(object):

    def __init__(self, level_name, message, writer=None, config_level=None):
        self.level_name = level_name
        self.message = message
        self.writer = writer or sys.stdout
        self.config_level = config_level or self.get_config_level()

    def skip(self):
        if self.level_int >= self.config_level:
            return False
        return True

    def header(self):
        colored = colorize.make(self.base_string)
        return getattr(colored, self.level_color)

    @property
    def base_string(self):
        if self.config_level < 2:
            return "--> [%s]" % self.level_name
        return "-->"

    @property
    def level_int(self):
        if self.level_name == 'remote':
            return 2
        return _reverse_level_names.get(self.level_name, 4)

    @property
    def level_color(self):
        return _level_colors.get(self.level_name, 'info')

    def line(self):
        msg = self.message.rstrip('\n')
        return "%s %s\n" % (self.header(), msg)

    def write(self):
        if not self.skip():
            self.writer.write(self.line())

    def get_config_level(self):
        import ceph_medic
        level = ceph_medic.config.verbosity
        return _reverse_level_names.get(level, 4)


def error(message):
    return LogMessage('error', message).write()


def debug(message):
    return LogMessage('debug', message).write()


def info(message):
    return LogMessage('info', message).write()


def warning(message):
    return LogMessage('warning', message).write()


def critical(message):
    return LogMessage('critical', message).write()
