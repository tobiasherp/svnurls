#!/usr/bin/env python
# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
from os.path import dirname, abspath, join, sep

def read(name):
    fn = join(dirname(abspath(__file__)), name)
    return open(fn, 'r').read()

__author__ = "Tobias Herp <tobias.herp@gmx.de>"
VERSION = (0,
           1,   # initial version
           ''.join(map(str, (
           16,  # py2/py3 for non-Linux only; ...
           ))),
           )
__version__ = '.'.join(map(str, VERSION))

# from pprint import pprint
if 0:\
pprint({'sys.argv': argv,
        'console_scripts:': console_scripts,
        })

setup(name='svnurls'
    , author='Tobias Herp'
    , author_email='tobias.herp@gmx.de'
    , description="Split and unsplit Subversion URLs"
    , long_description=read('README.rst')
    , version=__version__
    , package_dir={'':'src'}
    , packages=find_packages('src')
    , namespace_packages = ['thebops',
                            ]
    , include_package_data=True
    , classifiers=[
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        ]
    , license='MIT'
    , keywords=[
        'subversion', 'svn',
        'standard repository layout',
        'trunk', 'branches', 'tags',
        'urlsplit', 'urlunsplit',
        ]
    )
