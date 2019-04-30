import logging
from ceph_medic import metadata, terminal, daemon_types
from ceph_medic import checks, __version__
from ceph_medic import config

logger = logging.getLogger(__name__)


class Runner(object):

    def __init__(self):
        self.passed = 0
        self.skipped = 0
        self.total = 0
        self.errors = 0
        self.warnings = 0
        self.ignore = []
        self.internal_errors = []

    @property
    def total_hosts(self):
        # XXX does not ensure unique nodes. In collocated scenarios, a single
        # node that is a 'mon' and an 'osd' would count as two nodes
        count = 0
        for daemon in metadata['nodes'].values():
            count += len(daemon)
        return count

    def run(self):
        """
        Go through all the daemons, and all checks. Single entrypoint for running
        checks everywhere.
        """
        start_header()
        for daemon_type in daemon_types:
            self.run_daemons(daemon_type)

        # these are checks that should run once per cluster
        nodes_header('cluster')
        self.run_cluster(checks.cluster)

        if metadata['failed_nodes']:
            terminal.write.bold('\n{daemon:-^30}\n'.format(daemon=' Failed Nodes '))
            for host, reason in metadata['failed_nodes'].items():
                terminal.loader.write(' %s' % terminal.red(host))
                terminal.write.write('\n')
                reason_lines = reason.split('\n')
                main_reason = reason_lines.pop(0)
                terminal.write.write("  %s\n" % main_reason)
                for line in reason_lines:
                    terminal.write.write("   %s\n" % line)
        self.total = self.errors + self.warnings + self.passed + len(self.internal_errors)
        return self

    def run_daemons(self, daemon_type):
        has_nodes = metadata[daemon_type]
        is_daemon = daemon_type in metadata['nodes']
        if has_nodes and is_daemon:  # we have nodes of this type to run
            nodes_header(daemon_type)
        else:
            return

        for host, data in metadata[daemon_type].items():
            modules = [checks.common, getattr(checks, daemon_type, None)]
            self.run_host(host, data, modules)

    def run_cluster(self, module):
        # XXX get the cluster name here
        cluster_name = '%s cluster' % metadata.get('cluster_name', 'ceph')
        terminal.loader.write(' %s' % terminal.yellow(cluster_name))
        has_error = False
        checks = collect_checks(module)
        for check in checks:
            try:
                # TODO: figure out how to skip running a specific check if
                # the code is ignored, maybe introspecting the function?
                result = getattr(module, check)()
            except Exception as error:
                result = None
                logger.exception('check had an unhandled error: %s', check)
                self.internal_errors.append(error)
            if result:
                code, message = result
                # XXX This is not ideal, we shouldn't need to get all the way here
                # to make sure this is actually ignored. (Or maybe it doesn't matter?)
                if code in self.ignore:
                    self.skipped += 1
                    # avoid writing anything else to the terminal, and just
                    # go to the next check
                    continue
                if not has_error:
                    # XXX get the cluster name here
                    terminal.loader.write(' %s' % terminal.red(cluster_name))
                    terminal.write.write('\n')

                if code.startswith('E'):
                    code = terminal.red(code)
                    self.errors += 1
                elif code.startswith('W'):
                    code = terminal.yellow(code)
                    self.warnings += 1
                terminal.write.write("   %s: %s\n" % (code, message))
                has_error = True
            else:
                self.passed += 1

        if not has_error:
            terminal.loader.write(' %s\n' % terminal.green(cluster_name))

    def run_host(self, host, data, modules):
        terminal.loader.write(' %s' % terminal.yellow(host))
        has_error = False
        for module in modules:
            checks = collect_checks(module)
            for check in checks:
                try:
                    # TODO: figure out how to skip running a specific check if
                    # the code is ignored, maybe introspecting the function?
                    result = getattr(module, check)(host, data)
                except Exception as error:
                    result = None
                    logger.exception('check had an unhandled error: %s', check)
                    self.internal_errors.append(error)
                if result:
                    code, message = result
                    # XXX This is not ideal, we shouldn't need to get all the way here
                    # to make sure this is actually ignored. (Or maybe it doesn't matter?)
                    if code in self.ignore:
                        self.skipped += 1
                        # avoid writing anything else to the terminal, and just
                        # go to the next check
                        continue
                    if not has_error:
                        terminal.loader.write(' %s' % terminal.red(host))
                        terminal.write.write('\n')

                    if code.startswith('E'):
                        self.errors += 1
                        code = terminal.red(code)
                    elif code.startswith('W'):
                        self.warnings += 1
                        code = terminal.yellow(code)
                    terminal.write.write("   %s: %s\n" % (code, message))
                    has_error = True
                else:
                    self.passed += 1

        if not has_error:
            terminal.loader.write(' %s\n' % terminal.green(host))


run_errors = terminal.yellow("""
While running checks, ceph-medic had %s unhandled errors, please look at the
configured log file and report the issue along with the traceback.
""")


def report(results):
    msg = "\n{passed}{error}{warning}{skipped}{internal_errors}{hosts}"

    if results.errors:
        msg = terminal.red(msg)
    elif results.warnings:
        msg = terminal.yellow(msg)
    else:
        msg = terminal.green(msg)

    errors = warnings = internal_errors = ''

    if results.errors:
        errors = '%s errors, ' % results.errors if results.errors > 1 else '1 error, '
    if results.warnings:
        warnings = '%s warnings, ' % results.warnings if results.warnings > 1 else '1 warning, '
    if results.internal_errors:
        internal_errors = "%s internal errors, " % len(results.internal_errors)

    terminal.write.raw(
        msg.format(
            passed="%s passed, " % results.passed,
            error=errors,
            warning=warnings,
            skipped="%s skipped, " % results.skipped if results.skipped else '',
            internal_errors=internal_errors,
            hosts="on %s hosts" % results.total_hosts
        )
    )
    if results.internal_errors:
        terminal.write.raw(run_errors % len(results.internal_errors))


start_header_tmpl = """
{title:=^80}
Version:    {version: >4}    Cluster Name: "{cluster_name}"
Connection: {connection_type}
Total hosts: [{total_hosts}]
OSDs: {osds: >4}    MONs: {mons: >4}     Clients: {clients: >4}
MDSs: {mdss: >4}    RGWs: {rgws: >4}     MGRs: {mgrs: >7}
"""


def start_header():
    connection_type = config.file.get_safe('global', 'deployment_type', 'ssh')
    daemon_totals = dict((daemon, 0) for daemon in daemon_types)
    total_hosts = 0
    for daemon in daemon_types:
        count = len(metadata[daemon].keys())
        total_hosts += count
        daemon_totals[daemon] = count
    terminal.write.raw(start_header_tmpl.format(
        title='  Starting remote check session  ',
        version=__version__,
        connection_type=connection_type,
        total_hosts=total_hosts,
        cluster_name=metadata['cluster_name'],
        **daemon_totals))
    terminal.write.raw('=' * 80)


def nodes_header(daemon_type):
    readable_daemons = {
        'rgws': ' rados gateways ',
        'mgrs': ' managers ',
        'mons': ' mons ',
        'osds': ' osds ',
        'clients': ' clients ',
        'cluster': ' cluster ',
    }

    terminal.write.bold('\n{daemon:-^30}\n'.format(
        daemon=readable_daemons.get(daemon_type, daemon_type)))


def collect_checks(module):
    checks = [i for i in dir(module) if i.startswith('check')]
    return checks
