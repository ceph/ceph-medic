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
