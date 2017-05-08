config = {
    'verbosity': 'info',
    'nodes': {},
    'hosts_file': None,
}

metadata = {'rgws': {}, 'mgrs': {}, 'mdss':{}, 'clients': {}, 'osds':{}, 'mons':{}, 'nodes': {}}

daemon_types = [i for i in metadata.keys() if i != 'nodes']

__version__ = '0.0.1'
