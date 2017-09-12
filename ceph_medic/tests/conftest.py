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
    def make_data():
        return {
            'ceph': {'installed': True},
            'paths': {
                '/etc/ceph': {'files': {}, 'dirs': {}},
                '/var/lib/ceph': {'files': {}, 'dirs': {}},
            }
        }
    return make_data

