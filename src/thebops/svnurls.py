# -*- coding: utf-8 -*- äöü vim: ts=8 sts=4 sw=4 si et tw=79
"""
thebops.svnurls: Split / unsplit Subversion URLs

Supports the Subversion standard layout::

    ^/
     ...
     |- my.project
     |  |- trunk
     |  |- branches
     |  |  |- feature1
     |  |  `- v1_0
     |  `- tags
     |     `- v1.0
     :

Tags and branches in Subversion are technically ordinary copies.
This module supports tagging and branching by extracting the "branch part".
"""
from collections import namedtuple
from sys import version_info
if version_info[:2] >= (3, 0):
    from urllib.parse import urlsplit, urlunsplit
else:
    from urlparse import urlsplit, urlunsplit
from os import sep, altsep
from os.path import normpath
def _(s, *args, **kwargs):
    return s

__all__ = [
        'change_svn_url',      # return changed svn URL
        'split_svn_url',       # the urlsplit function
        'unsplit_svn_url',     # the corresponding urlunsplit
        'SplitSubversionURL',  # the namedtuple class
        ]

forbidden_chars = set('<>|@?*')


def change_svn_url(url, **kwargs):
    """
    >>> url1 = 'svn+ssh://svn.mycompany/repo1/my.project/trunk/setup.py'
    >>> change_svn_url(url1, project='other.project/')
    'svn+ssh://svn.mycompany/repo1/other.project/trunk/setup.py'
    >>> change_svn_url(url1, branch='branches/feature1')
    'svn+ssh://svn.mycompany/repo1/my.project/branches/feature1/setup.py'
    """
    split_kwargs = kwargs.pop('split_kwargs', {})
    liz = list(split_svn_url(url, **split_kwargs))
    for key, val in kwargs.items():
        i = url_part_index[key]
        liz[i] = url_part_checkers[key](val)
    return unsplit_svn_url(liz)


def repo_value(url):
    if url == '^':
        return url
    tup = urlsplit(url)
    if tup.scheme or tup.netloc:
        return urlunsplit(tup[:3]+('', ''))
    raise ValueError('URL %(url)r doesn\'t contain a scheme '
                     'nor a hostname'
                     % locals())


def prefix_value(s):
    """
    beginnt und endet mit einem '/'
    """
    forbidden = forbidden_chars.intersection(s)
    if forbidden:
        return ValueError('%(s)s contains forbidden characters'
                ' (%(forbidden)s)'
                % locals())
    stripped = s.strip('/')
    if stripped:
        return stripped.join('//')
    return '/'


def dotted_name(s):
    forbidden = forbidden_chars.intersection(s)
    if forbidden:
        return ValueError('%(s)s contains forbidden characters'
                ' (%(forbidden)s)'
                % locals())
    if not s:
        return ''
    # might result from tab completion:
    stripped = s.rstrip('/')
    if '/' in stripped:
        return ValueError('dotted name %(stripped)r'
                ' must not contain slashes'
                % locals())
    chunks = stripped.split('.')
    if [chunk
        for chunk in chunks
        if not chunk
        ]:
        return ValueError('badly dotted name: %(stripped)r'
                % locals())
    return stripped


def branch_value(s):
    if s == 'trunk':
        return s
    liz = s.split('/', 1)
    if liz[0] not in ('tags', 'branches'):
        raise ValueError('%(s)r: tags/... or branches/... expected'
                % locals())
    if liz[1:] and liz[1]:
        return '/'.join((liz[0],
                         dotted_name(liz[1]),
                         ))
    return liz[0]


def url_subpath(s):
    """
    darf mit '/' enden, aber nicht beginnen
    """
    forbidden = forbidden_chars.intersection(s)
    if forbidden:
        return ValueError('%(s)s contains forbidden characters'
                ' (%(forbidden)s)'
                % locals())
    stripped = normpath(s).lstrip(sep)
    if sep != '/':
        return stripped.replace(sep, '/')
    return stripped


def peg_value(peg):
    if peg in (None, ''):
        return None
    try:
        val = int(peg)
        if val <= 0:
            raise ValueError('peg revision needs to be >= 1 (%(val)r)'
                    % locals())
    except ValueError:
        raise ValueError('peg revision must be a number >= 1 (%(peg)r)'
                % locals())
    else:
        return val


svn_url_parts = 'repo prefix project branch suffix peg'.split()
url_part_index = dict(zip(svn_url_parts,
                          range(len(svn_url_parts))
                          ))
url_part_checkers = {
        'repo':    repo_value,
        'prefix':  prefix_value,
        'project': dotted_name,
        'branch':  branch_value,
        'suffix':  url_subpath,
        'peg':     peg_value,
        }

SplitSubversionURL = namedtuple(
    'SplitSubversionURL',
    svn_url_parts)
def split_svn_url(url, **kwargs):
    """
    Split a Subversion URL in six parts:
    - First, we check the left end:
      We expect the given URL to start with '^/'
      (or '/', with assume_url=True, which is the default),
      or to be a proper URL which features a network protocol scheme.
    - Then we look for trunk, branches or tags.
      This (and the following /-delimited path chunk,
      for tags and branches) is the "branch part", the fourth of the six.
    - The "project" precedes the branch part.
    - The "prefix" precedes the project.
    - the "suffix" follows the branch part.
    - Finally, a PEG revision can be contained,
      which is an integer number or None.

    Return a named tuple (SplitSubversionURL).

    Keyword options:

    - baseurl -- if a full URL is specified,
                 tell which part specifies the repository.
                 Doesn't change the result but adds a check for the prefix

    - assume_url -- if the url starts with a slash, prepend it with a '^'.
                    Default is True, because of svn's output conventions.

    >>> split_svn_url('svn+ssh://svn.mycompany/my.project/trunk/setup.py')
    SplitSubversionURL(repo='svn+ssh://svn.mycompany', prefix='/', project='my.project', branch='trunk', suffix='setup.py', peg=None)

    A repository-internal specification can be parsed as well:
    >>> split_svn_url('^/my.project/trunk/setup.py@123')
    SplitSubversionURL(repo='^', prefix='/', project='my.project', branch='trunk', suffix='setup.py', peg=123)

    >>> split_svn_url('^/my.project/tags/v1.0/setup.py')
    SplitSubversionURL(repo='^', prefix='/', project='my.project', branch='tags/v1.0', suffix='setup.py', peg=None)

    For URL manipulation, we convert the named tuple to a list:
    >>> aslist = list(split_svn_url('^/my.project/trunk/setup.py'))
    >>> aslist
    ['^', '/', 'my.project', 'trunk', 'setup.py', None]
    >>> SplitSubversionURL(*aslist)
    SplitSubversionURL(repo='^', prefix='/', project='my.project', branch='trunk', suffix='setup.py', peg=None)

    For brevity, here is a little helper function for doctest-internal use:

    >>> def ssu_list(s, *args, **kwargs):
    ...     return list(split_svn_url(s, *args, **kwargs))

    However, you'll usually simply use the change_svn_url function which wraps
    the splitting and unsplitting part and checks the arguments for reasonable
    values.

    As this is a simple parsing function, it won't ask Subversion to
    tell about the repository base URL in such cases.

    For the same reason, it can't really know which part of a fully
    qualified URL specifies the repository (and can be abbreviated as
    "^", if working in a matching checkout), and which is part of the
    internal path.
    By default, it guesses the "prefix" to immediately follow the hostname
    (if any):

    >>> url1 = 'svn+ssh://svn.mycompany/repo1/my.project/trunk/setup.py'
    >>> url1_aslist = ssu_list(url1)
    >>> url1_aslist
    ['svn+ssh://svn.mycompany', '/repo1/', 'my.project', 'trunk', 'setup.py', None]

    Normally, this won't matter at all; we usually only use the
    'project', 'branch' and 'suffix' parts.
    But for cases when it *does* matter, you can tell the function about
    the base url:
    >>> ssu_list('svn+ssh://svn.mycompany/repo1/my.project/trunk/setup.py',
    ...          baseurl='svn+ssh://svn.mycompany/repo1')
    ['svn+ssh://svn.mycompany/repo1', '/', 'my.project', 'trunk', 'setup.py', None]

    For '^/...' URLs, this 'baseurl' argument is ignored;
    other URLs are required to match this base: if it doesn't, a
    ValueError will be raised.

    To get back a usable URL, you'll use the corresponding unsplit function:
    >>> url1_fromlist = unsplit_svn_url(url1_aslist)
    >>> url1_fromlist == url1
    True

    You might have noticed that from some parts of the resulting tuple,
    slashes are stripped, but not from all:

    - the 'repo' part usually doesn't end with '/'
      (except perhaps for the file:// scheme)
    - the 'prefix' part both starts and ends with '/'
    - the project part is stripped - it might become exchanged,
      and that given value of course can be given without trailing slashes
      (which are tolerated, in fact, because they might result from tab
      expansion)
    - the 'branch' part is stripped, of course;
    - the 'suffix' part must not start with a '/'
      because this would change the meaning relative in the filesystem.

    So, to un-split the value, you'll better use that function.
    """
    baseurl = kwargs.pop('baseurl', None)
    assume_url = kwargs.pop('assume_url', True)
    if kwargs:
        raise TypeError('Unsupported argument(s): %s'
                % (kwargs.keys(),
                   ))
    startswith = url.startswith
    if startswith('^/'):
        repo = '^'
        url = url[1:]
    elif startswith('/') and assume_url:
        repo = '^'
    elif baseurl:
        baseurl = baseurl.rstrip('/')
        if not startswith(baseurl):
            raise ValueError('URL %(url)r doesn\'t match'
                    ' the given baseurl %(baseurl)r!'
                    % locals())
        rest = url[len(baseurl):]
        if not rest:
            url = rest  # we might support bare repo URLs
        elif rest.startswith('/'):
            url = rest
        else:
            raise ValueError('URL %(url)r doesn\'t match'
                    ' the given baseurl %(baseurl)r!'
                    % locals())
        repo = baseurl
    else:
        tup = urlsplit(url)
        if tup.scheme or tup.netloc:
            repo = urlunsplit(tup[:2]+('', '', ''))
        else:
            raise ValueError('URL %(url)r doesn\'t contain a scheme '
                    'nor a hostname'
                    % locals())
        if tup.query or tup.fragment:
            raise ValueError('Error parsing %r: '
                    "We don't support URLs containing query strings "
                    '(%r) or fragments (%r)!'
                    % (url, tup.query, tup.fragment))
        url = tup.path

    # now that we have the repo,
    # we parse the rest that follows it.
    # we support '@' characters only at the end,
    # followed by a number:
    if '@' in url:
        url, peg = url.split('@', 1)
        peg = peg_value(peg)
    else:
        peg = None

    liz = url.split('/')
    if 'trunk' in liz:
        i = liz.index('trunk')
        j = i + 1
    elif 'branches' in liz:
        i = liz.index('branches')
        j = i + 2
    elif 'tags' in liz:
        i = liz.index('tags')
        j = i + 2
    else:
        i = None
    if i is None:
        prefix = '/'.join(liz[:-1])
        project = liz[-1]
        branch = None
        suffix = None
    else:
        project = liz[i-1]
        prefix = '/'.join(liz[:i-1])
        branch = '/'.join(liz[i:j])
        suffix = '/'.join(liz[j:])
    if project or branch or suffix:
        if not prefix:
            prefix = '/'
        else:
            prefix = '/' + prefix.strip('/') + '/'
    return SplitSubversionURL(repo, prefix,
            project, branch, suffix,
            peg)

def unsplit_svn_url(tup):
    """
    re-join a subversion url which was split by the split_svn_url function
    """
    repo, prefix, project, branch, suffix, peg = tuple(tup)
    res = [repo or '^',
           prefix or '/',
           ]
    if project:
        res.extend([project, '/'])
    if branch:
        res.extend([branch, '/'])
    if suffix:
        res.append(suffix)
    if peg:
        res.extend(['@', str(peg)])
    return ''.join(res)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
