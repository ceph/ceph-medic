from collections import namedtuple


class UnloadedConfig(object):
    """
    This class is used as the default value for config.ceph so that if
    a configuration file is not successfully loaded then it will give
    a nice error message when values from the config are used.
    """
    def __init__(self, error=None):
        self.error = error

    def __getattr__(self, *a):
        raise RuntimeError(self.error)


config = namedtuple('config', ['verbosity', 'nodes', 'hosts_file', 'file', 'cluster_name'])
config.file = UnloadedConfig("No valid ceph-medic configuration file was loaded")
config.nodes = {}

metadata = {'failed_nodes': {}, 'rgws': {}, 'mgrs': {}, 'mdss': {}, 'clients': {}, 'osds': {}, 'mons': {}, 'nodes': {}, 'cluster': {}}

daemon_types = [i for i in metadata.keys() if i not in ('nodes', 'failed_nodes', 'cluster')]

__version__ = '1.0.6'
