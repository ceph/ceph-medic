import pytest
import random
from ceph_medic import runner
import ceph_medic
from ceph_medic.tests import base_metadata


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


@pytest.fixture(scope='class', autouse=True)
def clear_metadata():
    ceph_medic.metadata = base_metadata


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
            'ceph': {'installed': True, 'version': '12.2.1', 'sockets':{}},
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


class Capture(object):

    def __init__(self, *a, **kw):
        self.a = a
        self.kw = kw
        self.calls = []
        self.return_values = kw.get('return_values', False)
        self.always_returns = kw.get('always_returns', False)

    def __call__(self, *a, **kw):
        self.calls.append({'args': a, 'kwargs': kw})
        if self.always_returns:
            return self.always_returns
        if self.return_values:
            return self.return_values.pop()


class Factory(object):

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


@pytest.fixture
def factory():
    return Factory


@pytest.fixture
def conn():
    """
    Useful when trying to pass a ``conn`` object around that will porbably want
    to log output
    """
    log = lambda x: x
    logger = Factory(error=log, exception=log)
    return Factory(logger=logger)


@pytest.fixture
def capture():
    return Capture()


@pytest.fixture
def fake_run(monkeypatch):
    fake_run = Capture()
    monkeypatch.setattr('remoto.process.run', fake_run)
    return fake_run


@pytest.fixture
def fake_check(monkeypatch):
    fake_call = Capture(always_returns=([], [], 0))
    monkeypatch.setattr('remoto.process.check', fake_call)
    return fake_call


@pytest.fixture
def stub_check(monkeypatch):
    """
    Monkeypatches process.check, so that a caller can add behavior to the
    response
    """
    def apply(return_values, module=None, string_module='remoto.process.check'):
        """
        ``return_values`` should be a tuple of 3 elements: stdout, stderr, and
        code. This should mimic the ``check()`` return values. For example::

            (['stdout'], ['stderr'], 0)

        Each item in the stdout or stderr lists represents a line.
        Additionally, if more than one response is wanted, a list with multiple
        tuples can be provided::


            [
                (['output'], [], 0),
                ([], ['error condition'], 1),
                (['output'], [], 0),
            ]

        When patching, most of the time the default ``string_module`` will be
        fine, but if it is required to patch an actual module with the added
        string, then it is possible to use them accordingly: whne the module is
        set, the call to ``monkeypatch`` will use both like::

            monkeypatch.setattr(module, 'function', value)

        Otherwise it will just patch it like::

            monkeypatch.setattr('remoto.process.check', value)

        """
        if isinstance(return_values, tuple):
            return_values = [return_values]
        stubbed_call = Capture(return_values=return_values)
        if module:
            monkeypatch.setattr(module, string_module, stubbed_call)
        else:
            monkeypatch.setattr(string_module, stubbed_call)
        return stubbed_call

    return apply


@pytest.fixture(autouse=True)
def reset_file_config(request, monkeypatch):
    """
    The globally available ``ceph_medic.config.file`` might get mangled in
    tests, make sure that after evert test, it gets reset, preventing pollution
    going into other tests later.
    """
    def fin():
        ceph_medic.config.file = ceph_medic.UnloadedConfig()
    request.addfinalizer(fin)
