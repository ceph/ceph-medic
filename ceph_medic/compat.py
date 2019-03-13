# flake8: noqa

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

try:
    from ConfigParser import SafeConfigParser as BaseConfigParser
except ImportError:
    from configparser import ConfigParser as BaseConfigParser

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
