from ceph_medic.compat import BaseConfigParser, configparser, StringIO
import logging
import os
import sys
from os import path
import re
from ceph_medic import terminal, metadata

logger = logging.getLogger(__name__)

medic_conf_template = """
#
# ceph-medic configuration file
#

[global]
# Overrides for some of ceph-medic's global flags, like verbosity or cluster
# name Cluster Name. Ceph defaults this to 'ceph' when not specified, and
# ceph-medic will try to infer this if the configuration is not found on the
# first '.conf' file in /etc/ceph/
--cluster = ceph
# Use a specific location for the Ansible inventory file, it defaults to look
# into the current working directory and /etc/ansible (in that order) unless
# specified here or directly at the command line
#--inventory
#
# The logging verbosity, this will affect both the terminal and file logging
# levels
--verbosity = info
#
# Should always be an absolute path, although '.' is allowed to log from
# wherever the CLI is executed from (current working directory)
--log-path = .
# What type of deployment is the cluster using? Valid values are:
# baremetal, container, openshift, kubernetes
# deployment_type = baremetal

[check]
# Overrides for some of ceph-medic's check flags, like what errors or warnings
# to ignore. By default nothing is ignored (everything is reported). Ignores
# should be comma separated into their respective codes.
# --ignore = ECOMM101,ECOMM102

[baremetal]
# baremetal options

[kubernetes]
namespace = rook-ceph
"""


class _TrimIndentFile(object):
    """
    This is used to take a file-like object and removes any
    leading tabs from each line when it's read. This is important
    because some ceph configuration files include tabs which break
    ConfigParser.
    """
    def __init__(self, fp):
        self.fp = fp

    def readline(self):
        line = self.fp.readline()
        return line.lstrip(' \t')

    def __iter__(self):
        return iter(self.readline, '')


def location():
    """
    Find and return the location of the ceph-medic configuration file. If this
    file does not exist, create one in a default location.
    """
    return _locate_or_create()


def get_host_file(_path=None):
    """
    If ``_path`` is passed in, return that (makes it easier for the caller if
    it can pass a ``None``) otherwise look into the most common locations for
    a host file and if found, return that.
    """
    if _path:
        return _path
    # if no path is passed onto us try and look in the cwd for a hosts file
    if os.path.isfile('hosts'):
        logger.info(
            'found and loaded the hosts file from the current working directory: %s',
            os.getcwd()
        )
        return path.abspath('hosts')

    # if that is not the case, try for /etc/ansible/hosts
    if path.isfile('/etc/ansible/hosts'):
        return '/etc/ansible/hosts'
    logger.warning('unable to find an Ansible hosts file to work with')
    logger.warning('tried locations: %s, %s', os.getcwd(), '/etc/ansible/hosts')


def load_hosts(_path=None):
    """
    Very similar to a plain configuration load, but do not fail if a hosts file
    is not loaded. Try the hardest to load one, and return an empty dictionary
    if nothing is found.
    """
    if _path and not os.path.exists(_path):
        terminal.error("the given inventory path does not exist: %s" % _path)
        sys.exit()
    _path = _path or get_host_file()
    return AnsibleInventoryParser(_path)


def parse_hosts(conf):
    """
    From a parsed hosts file, loop through all the nodes and get the actual
    hosts from each line
    """
    parsed_hosts = {}
    if not conf:
        return parsed_hosts
    for section in conf.sections:
        parsed_hosts[section] = []


def load_string(conf_as_string):
    """
    An easy way to get the INI configuration as a string, but return a Conf
    object after writing it to a StringIO (file-like) object.
    """
    file_obj = StringIO()
    file_obj.write(conf_as_string)
    file_obj.seek(0)
    return load(file=_TrimIndentFile(file_obj))


def load(path=None, file=None):
    parser = Conf()
    try:
        if file:
            parser._read_file(file)
        elif path and os.path.exists(path):
            parser.read(path)
        else:
            parser.read(location())
        return parser
    except configparser.ParsingError as error:
        terminal.error('Unable to read configuration file')
        terminal.error(str(error))
        logger.exception('Unable to parse INI-style file')


def _locate_or_create():
    home_config = path.expanduser('~/.cephmedic.conf')
    # With order of importance
    locations = [
        path.join(os.getcwd(), 'cephmedic.conf'),
        home_config,
    ]

    for location in locations:
        if path.exists(location):
            logger.debug('found configuration file at: %s' % location)
            return location
    logger.info('could not find configuration file, will create one in $HOME')
    create_stub(home_config)
    return home_config


def create_stub(_path=None):
    _path = _path or path.expanduser('~/.cephmedic.conf')
    logger.debug('creating new configuration file: %s' % _path)
    with open(_path, 'w') as cm_conf:
        cm_conf.write(medic_conf_template)


def get_overrides(_conf=None):
    """
    Read the configuration file and look for ceph-medic sections and flags to
    set the defaults, these are later checked by the main method to see if any
    need to be overridden *again* if specified on the CLI directly.
    """
    # Get the subcommand name to avoid overwritting values from other
    # subcommands that are not going to be used
    conf = _conf or load()
    conf_arguments = {}
    for section_name in conf.sections():
        if section_name == 'global':
            for k, v in conf.items(section_name):
                conf_arguments[k] = v
        else:
            conf_arguments[section_name] = {}
            for k, v in conf.items(section_name):
                conf_arguments[section_name][k] = v

    return conf_arguments


class Conf(BaseConfigParser):
    """
    Subclasses from SafeConfigParser to give a few helpers for the ceph-medic
    configuration. Specifically, it addresses the need to work with Ansible
    host sections and some custom values that might be comma-separated
    """

    def get_safe(self, section, key, default=None):
        """
        Attempt to get a configuration value from a certain section
        in a ``cfg`` object but returning None if not found. Avoids the need
        to be doing try/except {ConfigParser Exceptions} every time.
        """
        try:
            return self.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def get_list(self, section, key):
        """
        Assumes that the value for a given key is going to be a list separated
        by commas. It gets rid of trailing comments.  If just one item is
        present it returns a list with a single item, if no key is found an
        empty list is returned.
        """
        value = self.get_safe(section, key, [])
        if value == []:
            return value

        # strip comments
        value = re.split(r'\s+#', value)[0]

        # split on commas
        value = value.split(',')

        # strip spaces
        return [x.strip() for x in value]

    def optionxform(self, s):
        """
        Ceph configuration allows both these forms (considering them equal)::

            some key option = 1
            some_key_option = 1

        This method ensures that regardless of any of the formats, all options
        will be treated as using the underscores. This is also how ceph-deploy
        reads Ceph configuration values
        """
        s = s.replace('_', ' ')
        s = '_'.join(s.split())
        return s

    def _read_file(self, _file):
        """
        The ConfigParser class is already quite the complicated object deriving
        from an ABC type of class, deprecating ``.readfp()`` in Python3.3 and
        newer - although it is available. This semi-private method provides the
        abstraction depending on availability of the newer method type.
        """
        if hasattr(self, 'read_file'):
            return self.read_file(_file)
        return self.readfp(_file)


class AnsibleInventoryParser(object):
    """
    Based roughly on Ansible's ``InventoryParser``, but without capturing
    specifics on host or group vars because ceph-medic only cares about the
    groups and the hosts, and ConfigParser spits bullets with Ansible's lax INI
    format.

    It borrows the regexes from ``InventoryParser`` to match groups and sections, with the ability
    of expanding deeply nested grouping to understand what hosts belong to an actual group.

    Given this hosts file::

        [osds:children]
        usa

        [atlanta]
        osd0

        [florida]
        mon0

        [usa:children]
        atlanta
        florida

    Will make this parser add ``osd0`` as part of ``osds`` so that ceph-medic
    understands what the actual role of that node is. This extra bit of
    expanding and re-doing what Ansible could do for us is done so that we
    aren't requiring all of Ansible just to be able to load a hosts file.

    .. todo:: A try/except import for ``InventoryParser`` should be attempted
              so that we can just use Ansible if present, but fallback to this
              implementation if it isn't.
    """

    def __init__(self, filename=None):
        self.filename = filename
        self.hosts = {}
        self.patterns = {}
        self.groups = {}
        self.nodes = {}

        # Read the hosts file, stripping comments and empty lines
        # which are not needed for parsing
        contents = []

        if filename:
            with open(filename, 'r') as fh:
                for line in fh.readlines():
                    if line.startswith(u';'):
                        continue
                    if line.startswith(u'#'):
                        continue
                    if line:
                        contents.append(line.strip())

        self._parse(contents)

    def _parse(self, lines):
        """
        Read through all the ``lines`` of the hosts file, sorting the groups,
        hosts, and finally the nodes.
        """

        self._compile_patterns()

        # Define `ungrouped` first since hosts might not belong anywhere (why
        # would you do this though). Ansible supports this so we are trying to
        # get it supported here as well
        groupname = 'ungrouped'
        state = 'hosts'

        for line in lines:
            host_item = {'host': None, 'group': None}

            m = self.patterns['section'].match(line)
            if m:
                (groupname, state) = m.groups()
                state = state or 'hosts'
                self.groups[groupname] = []
                self.nodes[groupname] = []
                continue
            if state == 'vars':
                continue
            if state == 'hosts':
                host = self._parse_host_definition(line)
                if host:
                    host_item['host'] = host
                    host_item['group'] = groupname
                    self.nodes[groupname].append(host_item)
            if state == 'children':
                child = self._parse_group_name(line)
                if groupname not in self.groups:
                    self.groups[groupname] = []
                if child and child not in self.groups[groupname]:
                    self.groups[groupname].append(child)
                host_item['parent'] = groupname

            host_group = host_item.get('group')
            if host_group:
                if host_group not in self.hosts:
                    self.hosts[host_group] = [host_item]
                else:
                    self.hosts[host_group].append(host_item)
        self.expand_nodes()
        self.filter_groups()

    def filter_groups(self):
        """
        Removes any groups from self.nodes that do not exist in
        ceph_medic.metadata. We want to do this because we don't care
        about nodes or groups in an inventory that are not part of
        the ceph cluster.
        """
        groups = [key for key in self.nodes.keys()]
        for group in groups:
            if group not in metadata:
                del self.nodes[group]

    def expand_nested_group(self, parent_group, group):
        """
        For a ``group`` list, try to identify if any members are parents of
        other groups, if that is the case, keep recursing until the bottom of
        the membership is identified so that all the hosts can be added to
        ``self.nodes``
        """
        for g in group:
            if self.groups.get(g):
                # this group exists as a parent to some other group so recurse
                # and try to get to the bottom of the nesting
                self.expand_nested_group(parent_group, self.groups.get(g))
            if self.hosts.get(g):
                # This group is the direct parent of host(s), so extend the
                # members of that list
                self.nodes[parent_group].extend(self.hosts.get(g))

    def expand_nodes(self):
        """
        After all groups and hosts have been parsed and their memberships identified, it will then
        look at the group membership of all groups and determine which is the primary parent of the
        tree, so that we can eventually look at ``nodes['osds']`` and retrieve all the hosts that we
        need to know about.
        """
        # now reverse lookup, identifying if groups have other parents
        # so that it can populate the ``nodes`` attribute
        for parent_group, child_groups in self.groups.items():
            if child_groups:
                # pre-populate the value so that we can extend this later
                # without overriding anything that might be already there
                self.nodes[parent_group] = self.nodes.get(parent_group, [])
            for group in child_groups:

                if self.groups.get(group): # means we have a nested parent/child here
                    self.expand_nested_group(parent_group, self.groups[group])

                # this group has direct nodes already so extend
                # the nodes present for that one group
                if self.hosts.get(group):
                    self.nodes[parent_group].extend(self.hosts.get(group))

    def _parse_host_definition(self, line):
        """
        Identify a host from a single line. It supports hosts on the following formats::

            [osds]
            osd0
            osd1:6789 docker=True
            osd3 docker=True

        If the line is empty it will return a ``None`` which is caught by the caller.
        """
        if not line:
            return

        # split on whitespace
        host = line.split()[0]

        # split on colon
        host = host.split(':')[0]
        return host

    def _parse_group_name(self, line):
        """
        Try to match a groupname (which is usually in the format of
        Takes a single line and tries to parse it as a group name. Returns the
        group name if successful, or raises an error.
        """

        m = self.patterns['groupname'].match(line)
        if m:
            return m.group(1)

    def _compile_patterns(self):
        """
        Compiles the regexes based on the original implementation of the parser (``InventoryParser``)
        and sets the to ``self.patterns``
        """
        self.patterns['section'] = re.compile(
            r'''^\[
                    ([^:\]\s]+)             # group name
                    (?::(\w+))?             # optional tag name :
                \]
                \s*                         # ignore trailing whitespace
                (?:\#.*)?                   # and/or a comment till the
                $                           # end of the line
            ''', re.X
        )

        self.patterns['groupname'] = re.compile(
            r'''^
                ([^:\]\s]+)
                \s*                         # ignore trailing whitespace
                (?:\#.*)?                   # and/or a comment till the
                $                           # end of the line
            ''', re.X
        )
