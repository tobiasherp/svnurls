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
from os.path import normpath, curdir
def _(s, *args, **kwargs):
    return s

__all__ = [
        'change_svn_url',      # return changed svn URL
        'split_svn_url',       # the urlsplit function
        'unsplit_svn_url',     # the corresponding urlunsplit
        'SplitSubversionURL',  # the namedtuple class
        ]

forbidden_chars = set('<>|@?*')
reserved_names = 'trunk branches tags'.split()


def change_svn_url(url, **kwargs):
    """
    Changes the given URL according to the keyword arguments;
    the allowed arguments resemble the keys of the namedtuple class,
    with one exception:
    The 'branch' keyword argument takes a branch only;
    to replace the 'branch part' (which can contain the trunk or a tag as well)
    in a universal way, use the 'branch_part' argument.

    >>> url1 = 'svn+ssh://svn.mycompany/repo1/my.project/trunk/setup.py'

    Switch to another branch:
    >>> change_svn_url(url1, branch_part='branches/feature1')
    'svn+ssh://svn.mycompany/repo1/my.project/branches/feature1/setup.py'
    >>> change_svn_url(url1, branch='feature1')
    'svn+ssh://svn.mycompany/repo1/my.project/branches/feature1/setup.py'
    >>> change_svn_url(url1, branch='branches/feature1')
    'svn+ssh://svn.mycompany/repo1/my.project/branches/feature1/setup.py'

    Switch to the trunk:
    >>> change_svn_url(url1, branch_part='trunk')
    'svn+ssh://svn.mycompany/repo1/my.project/trunk/setup.py'
    >>> change_svn_url(url1, trunk='trunk')
    'svn+ssh://svn.mycompany/repo1/my.project/trunk/setup.py'
    >>> change_svn_url(url1, trunk=True)
    'svn+ssh://svn.mycompany/repo1/my.project/trunk/setup.py'

    Switch to a tag:
    >>> change_svn_url(url1, branch_part='tags/v1.0')
    'svn+ssh://svn.mycompany/repo1/my.project/tags/v1.0/setup.py'
    >>> change_svn_url(url1, tag='v1.0')
    'svn+ssh://svn.mycompany/repo1/my.project/tags/v1.0/setup.py'
    >>> change_svn_url(url1, tag='tags/v1.0')
    'svn+ssh://svn.mycompany/repo1/my.project/tags/v1.0/setup.py'

    The branch_part option can be used for bare 'branches' and 'tags' urls:
    >>> url2 = change_svn_url(url1, suffix='')
    >>> url2
    'svn+ssh://svn.mycompany/repo1/my.project/trunk/'

    >>> change_svn_url(url2, branch_part='branches')
    'svn+ssh://svn.mycompany/repo1/my.project/branches/'
    >>> change_svn_url(url2, branch_part='tags')
    'svn+ssh://svn.mycompany/repo1/my.project/tags/'

    >>> change_svn_url(url2, branches=1)
    'svn+ssh://svn.mycompany/repo1/my.project/branches/'
    >>> change_svn_url(url2, branches='branches')
    'svn+ssh://svn.mycompany/repo1/my.project/branches/'
    >>> change_svn_url(url2, tags=True)
    'svn+ssh://svn.mycompany/repo1/my.project/tags/'
    >>> change_svn_url(url2, tags='tags')
    'svn+ssh://svn.mycompany/repo1/my.project/tags/'

    Wrong values yield ValueErrors.

    If conflicting keyword args are used, a TypeError occurs:
    >>> change_svn_url(url2, branch='v1_0', trunk=1)
    Traceback (most recent call last):
    ...
    TypeError: Both branch and trunk target index 3

    However, if only one of those arguments yields a "true" value,
    there is no problem:
    >>> change_svn_url(url2, branch='v2_0', trunk=0, tags=None, branches='')
    'svn+ssh://svn.mycompany/repo1/my.project/branches/v2_0/'
    >>> change_svn_url(url2, branch='', trunk=0, tags=None, branches='')
    'svn+ssh://svn.mycompany/repo1/my.project/'
    """
    split_kwargs = kwargs.pop('split_kwargs', {})
    liz = list(split_svn_url(url, **split_kwargs))
    new_value = {}
    blocked_kwargs = {}
    for key, val in kwargs.items():
        i = url_part_index[key]
        new = url_part_checkers[key](val)
        if new:
            if i in blocked_kwargs:
                keys = ' and '.join(sorted([key, blocked_kwargs[i]]))
                raise TypeError('Both %(keys)s target index %(i)d'
                        % locals())
            blocked_kwargs[i] = key
            new_value[i] = new
        elif i not in new_value:
            new_value[i] = new
    for i, new in new_value.items():
        liz[i] = new
    return unsplit_svn_url(liz)


# --------------------------------------------- [ value checkers ... [
def repo_value(url):
    """
    check the value for the repo option of the change_svn_url function

    >>> repo_value('^')
    '^'

    Currently, for URLs, query strings and fragments are removed:
    >>> repo_value('svn+ssh://my.srv/repo1?query#fragment')
    'svn+ssh://my.srv/repo1'

    Non-URLs (other than '^') yield value errors:
    >>> repo_value('other')
    Traceback (most recent call last):
    ...
    ValueError: URL 'other' doesn't contain a scheme nor a hostname
    """
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
    The "prefix" starts and ends with a slash

    >>> prefix_value('/')
    '/'
    >>> prefix_value('some/prefix')
    '/some/prefix/'
    """
    forbidden = forbidden_chars.intersection(s)
    if forbidden:
        raise ValueError('%(s)s contains forbidden characters'
                ' (%(forbidden)s)'
                % locals())
    stripped = s.strip('/')
    if stripped:
        return stripped.join('//')
    return '/'


def dotted_name(s):
    """
    A "dotted name" is used for tags and branches.
    >>> dotted_name('v1.0')
    'v1.0'

    There is no replacement whatsoever:
    >>> dotted_name('v1_0')
    'v1_0'

    The name of a tag or branch can't contain a slash;
    the slash would terminate the "branch part":
    >>> dotted_name('one/two')
    Traceback (most recent call last):
    ...
    ValueError: dotted name 'one/two' must not contain slashes

    However, a trailing slash might result from tab expansion
    (e.g. when specifying a project), so it is removed:
    >>> dotted_name('my.project/')
    'my.project'

    """
    forbidden = forbidden_chars.intersection(s)
    if forbidden:
        raise ValueError('%(s)s contains forbidden characters'
                ' (%(forbidden)s)'
                % locals())
    if not s:
        return ''
    elif s in reserved_names:
        raise ValueError('The name %(s)r is reserved!'
                % locals())
    # might result from tab completion:
    stripped = s.rstrip('/')
    if '/' in stripped:
        raise ValueError('dotted name %(stripped)r'
                ' must not contain slashes'
                % locals())
    chunks = stripped.split('.')
    if [chunk
        for chunk in chunks
        if not chunk
        ]:
        raise ValueError('badly dotted name: %(stripped)r'
                % locals())
    return stripped


def branch_part(s):
    """
    Check the value for the 4th part (index: 3) of the split url, the "branch
    part", which can take the trunk or a tag as well

    >>> branch_part('trunk')
    'trunk'
    >>> branch_part('branches/v1_0')
    'branches/v1_0'
    >>> branch_part('tags/v1.0')
    'tags/v1.0'

    You might want to list the tags or branches:
    >>> branch_part('branches')
    'branches'
    >>> branch_part('tags')
    'tags'

    The value is allowed to be empty:
    >>> branch_part('')
    ''

    However, there is no default whatsoever concerning the 'branches/' or
    'tags/' prefix:
    >>> branch_part('somename')
    Traceback (most recent call last):
    ...
    ValueError: 'somename': tags/... or branches/... expected
    """
    if s == 'trunk':
        return s
    elif not s:
        return ''
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
    A "subpath" may end but not start with a slash;
    it resembles a relative filesystem path

    >>> url_subpath('one/../two/./three/')
    'two/three'

    Characters which you won't reasonably use for filesystem names
    (and may be forbidden by your filesystem anyway) cause a ValueError:
    >>> url_subpath('one>two')
    Traceback (most recent call last):
    ...
    ValueError: 'one>two' contains forbidden characters ('>')
    """
    forbidden = forbidden_chars.intersection(s)
    if forbidden:
        forbidden = ''.join(sorted(forbidden))
        raise ValueError('%(s)r contains forbidden characters'
                ' (%(forbidden)r)'
                % locals())
    stripped = normpath(s).lstrip(sep)
    if stripped == curdir:
        return ''
    if sep != '/':
        return stripped.replace(sep, '/')
    return stripped


def peg_value(peg):
    """
    PEG revisions are natural numbers

    >>> peg_value('42')
    42
    >>> peg_value('')
    >>> peg_value(1)
    1
    >>> peg_value(0)
    Traceback (most recent call last):
    ...
    ValueError: peg revision needs to be >= 1 (0)
    >>> peg_value('PREV')
    Traceback (most recent call last):
    ...
    ValueError: peg revision must be a number >= 1 ('PREV')
    """
    if peg in (None, ''):
        return None
    try:
        val = int(peg)
    except ValueError:
        raise ValueError('peg revision must be a number >= 1 (%(peg)r)'
                % locals())
    else:
        if val <= 0:
            raise ValueError('peg revision needs to be >= 1 (%(val)r)'
                    % locals())
        return val


# ------------------------------------- [ checker factories ... [
def autoprefix(prefix):
    """
    >>> checker = autoprefix('tags/')
    >>> checker('tags/v1.0')
    'tags/v1.0'
    >>> checker('v1.0')
    'tags/v1.0'
    >>> checker('')
    ''
    >>> checker('branches/v1_0')
    Traceback (most recent call last):
    ...
    ValueError: dotted name 'branches/v1_0' must not contain slashes
    >>> checker('tags/')
    Traceback (most recent call last):
    ...
    ValueError: 'tags/': expected some name after 'tags/'!
    """
    pl = len(prefix)
    msg = '%%(s)r: expected some name after %(prefix)r!' % locals()
    def checker(s):
        if s.startswith(prefix):
            tail = s[pl:]
            if tail:
                return prefix + dotted_name(tail)
            else:
                raise ValueError(msg % locals())
        elif s:
            return prefix + dotted_name(s)
        else:
            return ''
    return checker


def switched_const(const):
    """
    >>> checker = switched_const('trunk')
    >>> checker(0)
    ''
    >>> checker('')
    ''
    >>> checker(1)
    'trunk'
    >>> checker('trunk/')
    'trunk'
    """
    msg = '%%(s)r: expected %(const)r or a boolean value' % locals()
    def checker(val):
        if not val:
            return ''
        if val in (1, True, const):
            return const
        # tolerate values from tab expansion:
        if val[-1] in (sep, altsep):
            val = val[:-1]
        if val == const:
            return const
        raise ValueError(msg % locals())
    return checker
# ------------------------------------- ] ... checker factories ]
# --------------------------------------------- ] ... value checkers ]


# ------------------------------------------ [ named tuple class ... [
svn_url_parts = 'repo prefix project branch suffix peg'.split()

SplitSubversionURL = namedtuple(
    'SplitSubversionURL',
    svn_url_parts)
# ------------------------------------------ ] ... named tuple class ]


url_part_index = dict(zip(svn_url_parts,
                          range(len(svn_url_parts))
                          ))
url_part_index.update({
    'branch_part': 3,
    'tag':         3,
    'trunk':       3,
    'branches':    3,
    'tags':        3,
    })
url_part_checkers = {
        'repo':        repo_value,
        'prefix':      prefix_value,
        'project':     dotted_name,
        'branch_part': branch_part,
        'suffix':      url_subpath,
        'peg':         peg_value,
        'branch':      autoprefix('branches/'),
        'branches':    switched_const('branches'),
        'trunk':       switched_const('trunk'),
        'tag':         autoprefix('tags/'),
        'tags':        switched_const('tags'),
        }


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
