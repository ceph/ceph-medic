from setuptools import setup, find_packages, Command
import re
import sys
import subprocess


install_requires = []
pyversion = sys.version_info[:2]


def read_module_contents():
    with open('ceph_medic/__init__.py') as f:
        return f.read()


module_file = read_module_contents()
metadata = dict(re.findall("__([a-z]+)__\s*=\s*'([^']+)'", module_file))
long_description = open('README.rst').read()
version = metadata['version']


class BumpCommand(Command):
    """ Bump the __version__ number and commit all changes. """

    user_options = [('version=', 'v', 'version number to use')]

    def initialize_options(self):
        new_version = metadata['version'].split('.')
        new_version[-1] = str(int(new_version[-1]) + 1)  # Bump the final part
        self.version = ".".join(new_version)

    def finalize_options(self):
        pass

    def run(self):

        try:
            print('old version: %s  new version: %s' %
                  (metadata['version'], self.version))
            raw_input('Press enter to confirm, or ctrl-c to exit >')
        except KeyboardInterrupt:
            raise SystemExit("\nNot proceeding")

        old = "__version__ = '%s'" % metadata['version']
        new = "__version__ = '%s'" % self.version

        module_file = read_module_contents()
        with open('ceph_medic/__init__.py', 'w') as fileh:
            fileh.write(module_file.replace(old, new))

        # Commit everything with a standard commit message
        cmd = ['git', 'commit', '-a', '-m', 'version %s' % self.version]
        print(' '.join(cmd))
        subprocess.check_call(cmd)


class ReleaseCommand(Command):
    """ Tag and push a new release. """

    user_options = [('sign', 's', 'GPG-sign the Git tag and release files')]

    def initialize_options(self):
        self.sign = False

    def finalize_options(self):
        pass

    def run(self):
        # Create Git tag
        tag_name = 'v%s' % version
        cmd = ['git', 'tag', '-a', tag_name, '-m', 'version %s' % version]
        if self.sign:
            cmd.append('-s')
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Push Git tag to origin remote
        cmd = ['git', 'push', 'origin', tag_name]
        print(' '.join(cmd))
        subprocess.check_call(cmd)

        # Push package to pypi
        cmd = ['python', 'setup.py', 'sdist', 'upload']
        if self.sign:
            cmd.append('--sign')
        print(' '.join(cmd))
        #subprocess.check_call(cmd)

        # Push master to the remote
        cmd = ['git', 'push', 'origin', 'master']
        print(' '.join(cmd))
        subprocess.check_call(cmd)


setup(
    name='ceph-medic',
    version=version,
    packages=find_packages(),

    author='Alfredo Deza',
    author_email='contact@redhat.com',
    description='detect common issues with ceph clusters',
    long_description=long_description,
    license='MIT',
    keywords='ceph doctor',
    url="https://github.com/ceph/ceph-medic",
    zip_safe=False,

    install_requires=[
        'execnet',
        'tambo',
        'remoto>=1.1.2',
    ] + install_requires,

    tests_require=[
        'pytest >=2.1.3',
        'tox',
        'mock',
    ],

    scripts=['bin/ceph-medic'],
    cmdclass={'bump': BumpCommand, 'release': ReleaseCommand},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Utilities',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ]

)
