from ceph_medic import terminal


class FakeWriter(object):

    def __init__(self):
        self.calls = []

    def write(self, string):
        self.calls.append(string)

    def flush(self):
        pass


class TestWriteClearLine(object):

    def setup(self):
        self.fake_writer = FakeWriter()
        self.loader = terminal._Write(
            _writer=self.fake_writer,
            prefix='\r',
            clear_line=True
        )

    def test_adds_padding_for_81_chars(self):
        self.loader.write('1234567890')
        assert len(self.fake_writer.calls[0]) == 81

    def test_remaining_padding_is_whitespace(self):
        self.loader.write('1234567890')
        assert self.fake_writer.calls[0][11:] == ' ' * 70

    def test_long_line_adds_only_ten_chars(self):
        self.loader.write('1'*81)
        assert self.fake_writer.calls[0][82:] == ' ' * 10
