#!/usr/bin/env python
# -*- coding: utf-8 -*- vim: ts=8 sts=4 sw=4 si et tw=79
from setuptools import setup, find_packages
from os.path import dirname, abspath, join, sep, isfile

def read(name):
    fn = join(dirname(abspath(__file__)), name)
    return open(fn, 'r').read()

__author__ = "Tobias Herp <tobias.herp@gmx.de>"
# -------------------------------------------- [ get the version ... [
def read_version(fn, sfn):
    main = open(fn).read().strip()
    if sfn is not None and isfile(sfn):
        suffix = valid_suffix(open(sfn).read().strip())
    else:
        suffix = ''
    return main + suffix
    # ... get the version ...
def valid_suffix(suffix):
    """
    Enforce our suffix convention
    """
    suffix = suffix.strip()
    if not suffix:
        return suffix
    allowed = set('.dev0123456789')
    disallowed = set(suffix).difference(allowed)
    if disallowed:
        disallowed = ''.join(sorted(disallowed))
        raise ValueError('Version suffix contains disallowed characters'
                         ' (%(disallowed)s)'
                         % locals())
    chunks = suffix.split('.')
    chunk = chunks.pop(0)
    if chunk:
        raise ValueError('Version suffix must start with "."'
                         ' (%(suffix)r)'
                         % locals())
    if not chunks:
        raise ValueError('Version suffix is too short'
                         ' (%(suffix)r)'
                         % locals())
    for chunk in chunks:
        if not chunk:
            raise ValueError('Empty chunk %(chunk)r in '
                             'version suffix %(suffix)r'
                             % locals())
        char = chunk[0]
        if char in '0123456789':
            raise ValueError('Chunk %(chunk)r of version suffix %(suffix)r'
                             ' starts with a digit'
                             % locals())
        char = chunk[-1]
        if char not in '0123456789':
            raise ValueError('Chunk %(chunk)r of version suffix %(suffix)r'
                             ' doesn\'t end with a digit'
                             % locals())
    return suffix  # ... valid_suffix
    # ... get the version ...
    # ... get the version ...
VERSION = read_version('VERSION',
                       'VERSION_SUFFIX')
# -------------------------------------------- ] ... get the version ]

long_description = '\n\n\n'.join([
    open(fn).read().strip()
    for fn in [
        'README.rst',
        'CONTRIBUTORS.rst',
        'CHANGES.rst',
        ]])
# from pprint import pprint
if 0:\
pprint({'sys.argv': argv,
        'console_scripts:': console_scripts,
        })

setup(name='svnurls'
    , author='Tobias Herp'
    , author_email='tobias.herp@gmx.de'
    , description="Split and unsplit Subversion URLs"
    , long_description=long_description
    , long_description_content_type='text/x-rst'
    , project_urls={
        'Documentation': 'https://pypi.org/project/svnurls',
        'Source':  'https://github.com/tobiasherp/svnurls',
        'Tracker': 'https://github.com/tobiasherp/svnurls/issues',
        }
    , version=VERSION
    , package_dir={'':'src'}
    , packages=find_packages('src')
    , namespace_packages = ['thebops',
                            ]
    , include_package_data=True
    , classifiers=[
        'Programming Language :: Python',
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
