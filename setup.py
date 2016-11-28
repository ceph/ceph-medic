from setuptools import setup, find_packages
import os
import sys


install_requires = []
pyversion = sys.version_info[:2]

module_file = open("ceph_doctor/__init__.py").read()
metadata = dict(re.findall("__([a-z]+)__\s*=\s*'([^']+)'", module_file))

setup(
    name='ceph-doctor',
    version = metadata['version'],
    packages=find_packages(),

    author='Alfredo Deza',
    author_email='contact@redhat.com',
    description='detect common issues with ceph clusters',
    long_description=read('README.rst'),
    license='MIT',
    keywords='ceph doctor',
    url="https://github.com/ceph/ceph-doctor",
    zip_safe = False,

    install_requires=[
        'setuptools',
    ] + install_requires,

    tests_require=[
        'pytest >=2.1.3',
        'tox',
    ],

    scripts = ['bin/ceph-doctor'],
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
