# flake8: noqa

try:
    import ConfigParser as configparser
except ImportError:
    import configparser

try:
    from ConfigParser import SafeConfigParser as BaseConfigParser
except ImportError:
    from configparser import ConfigParser as BaseConfigParser

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
