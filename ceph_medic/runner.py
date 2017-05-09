from ceph_medic import metadata, terminal, daemon_types
from ceph_medic import checks, __version__


class Runner(object):

    def __init__(self):
        self.passed = 0
        self.fail = 0
        self.total = 0
        self.total_hosts = len(metadata['nodes'].keys())

    def run(self):
        """
        Go through all the daemons, and all checks. Single entrypoint for running
        checks everywhere.
        """
        start_header()
        for daemon_type in daemon_types:
            self.run_daemons(daemon_type)
        self.total = self.fail + self.passed
        return self

    def run_daemons(self, daemon_type):
        if metadata[daemon_type]:  # we have nodes of this type to run
            nodes_header(daemon_type)

        # naive/simple reporting for now

        for host, data in metadata[daemon_type].items():
            modules = [checks.common, getattr(checks, daemon_type, None)]
            self.run_host(host, data, modules)

    def run_host(self, host, data, modules):
        terminal.loader.write(' %s' % terminal.yellow(host))
        has_error = False
        for module in modules:
            checks = collect_checks(module)
            for check in checks:
                result = getattr(module, check)(host, data)
                if result:
                    self.fail += 1
                    if not has_error:
                        terminal.loader.write(' %s\n' % terminal.red(host))

                    code, message = result
                    if code.startswith('E'):
                        code = terminal.red(code)
                    elif code.startswith('W'):
                        code = terminal.yellow(code)
                    print "   %s: %s" % (code, message)
                    has_error = True
                else:
                    self.passed += 1

        if not has_error:
            terminal.loader.write(' %s\n' % terminal.green(host))


def report(results):
    # TODO: what about skipped checks? or hosts that we couldn't connect to?
    if results.fail:
        msg = terminal.red(
            "\n%s passed %s checks failed on %s hosts" % (
                results.passed, results.fail, results.total_hosts))
    else:
        msg = terminal.green(
            "\n%s checks passed on %s hosts" % (results.passed, results.total_hosts))
    terminal.write.raw(msg)


start_header_tmpl = """
{title:=^80}
Version: {version}
Total hosts: [{total_hosts}]
OSDs: {osds: >4}    MONs: {osds: >4}     Clients: {osds: >4}
MDSs: {mdss: >4}    RGWs: {osds: >4}     MGRs: {osds: >7}
"""


def start_header():
    daemon_totals = dict((daemon, 0) for daemon in daemon_types)
    total_hosts = 0
    for daemon in daemon_types:
        count = len(metadata[daemon].keys())
        total_hosts += count
        daemon_totals[daemon] = count
    terminal.write.raw(start_header_tmpl.format(
        title='  Starting remote check session  ',
        version=__version__,
        total_hosts=total_hosts,
        **daemon_totals))
    terminal.write.raw('='*80)


def nodes_header(daemon_type):
    readable_daemons = {
        'rgws': 'rados gateways',
        'mgrs': 'managers',
    }

    terminal.write.bold('\n[{daemon:^15}]\n'.format(
        daemon=readable_daemons.get(daemon_type, daemon_type)))


def collect_checks(module):
    checks = [i for i in dir(module) if i.startswith('check')]
    return checks
