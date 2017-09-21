import pytest
import random
from ceph_medic import runner


class FakeWriter(object):

    def __init__(self):
        self.calls = []
        self.write = self.raw
        self.loader = self

    def raw(self, string):
        self.calls.append(string)

    def bold(self, string):
        self.calls.append(string)

    def get_output(self):
        return '\n'.join(self.calls)


@pytest.fixture
def mon_keyring():
    def make_keyring(default=False):
        if default:
            key = "AQBvaBFZAAAAABAA9VHgwCg3rWn8fMaX8KL01A=="
        else:
            key = "%032x==" % random.getrandbits(128)

        return """
    [mon.]
        key = %s
            caps mon = "allow *"
        """ % key
    return make_keyring


@pytest.fixture
def terminal(monkeypatch):
    fake_writer = FakeWriter()
    monkeypatch.setattr(runner.terminal, 'write', fake_writer)
    return fake_writer


@pytest.fixture
def data():
    """
    Default data structure for remote nodes
    """
    def _data():
        return {
            'ceph': {'installed': True, 'version': '12.2.1'},
            'paths': {
                '/etc/ceph': {'files': {}, 'dirs': {}},
                '/var/lib/ceph': {'files': {}, 'dirs': {}},
            }
        }
    return _data


@pytest.fixture
def make_data(data, **kw):
    """
    Customize basic data structure on remote nodes
    """
    def update(dictionary=None):
        base = data()
        if not dictionary:
            return base
        base.update(dictionary)
        return base
    return update


@pytest.fixture
def make_nodes():
    """
    Helper to generate nodes for daemons
    """
    def make_data(**kw):
        """
        ``kw`` is expected to be a mapping between daemon name and hosts for
        that daemon, like::

            make_data(mons=['node1', 'node2']
        """
        # default set of nodes
        data = dict(
            (k, {}) for k in ['rgws', 'mgrs', 'mdss', 'clients', 'osds', 'mons']
        )
        for daemon, node_names in kw.items():
            data[daemon] = [dict(host=node_name) for node_name in node_names]
        return data
    return make_data
