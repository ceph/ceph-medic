from collections import namedtuple


class UnloadedConfig(object):
    """
    This class is used as the default value for config.ceph so that if
    a configuration file is not successfully loaded then it will give
    a nice error message when values from the config are used.
    """
    def __getattr__(self, *a):
        raise RuntimeError("No valid ceph configuration file was loaded.")


config = namedtuple('config', ['verbosity', 'nodes', 'hosts_file', 'file'])
config.file = UnloadedConfig()

metadata = {'rgws': {}, 'mgrs': {}, 'mdss': {}, 'clients': {}, 'osds': {}, 'mons': {}, 'nodes': {}}

daemon_types = [i for i in metadata.keys() if i != 'nodes']

__version__ = '1.0.4'
