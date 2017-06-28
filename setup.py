from setuptools import setup, find_packages
import re
import sys


install_requires = []
pyversion = sys.version_info[:2]

module_file = open("ceph_medic/__init__.py").read()
metadata = dict(re.findall("__([a-z]+)__\s*=\s*'([^']+)'", module_file))
long_description = open('README.rst').read()

setup(
    name='ceph-medic',
    version = metadata['version'],
    packages=find_packages(),

    author='Alfredo Deza',
    author_email='contact@redhat.com',
    description='detect common issues with ceph clusters',
    long_description=long_description,
    license='MIT',
    keywords='ceph doctor',
    url="https://github.com/ceph/ceph-medic",
    zip_safe = False,

    install_requires=[
        'execnet',
        'tambo',
        'remoto',
    ] + install_requires,

    tests_require=[
        'pytest >=2.1.3',
        'tox',
        'mock',
    ],

    scripts = ['bin/ceph-medic'],
    classifiers = [
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
