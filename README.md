Robots Exclusion Protocol Parser for Python
===========================================

[![Build Status](https://travis-ci.org/seomoz/reppy.svg?branch=master)](https://travis-ci.org/seomoz/reppy)

`Robots.txt` parsing in Python.

Goals
=====

- __Fetching__ -- helper utilities for fetching and parsing `robots.txt`s, including
    checking `cache-control` and `expires` headers
- __Support for newer features__ -- like `Crawl-Delay` and `Sitemaps`
- __Wildcard matching__ -- without using regexes, no less
- __Performance__ -- with >100k parses per second, >1M URL checks per second once parsed
- __Caching__ -- utilities to help with the caching of `robots.txt` responses

Installation
============
`reppy` is available on `pypi`:

```bash
pip install reppy
```

When installing from source, there are submodule dependencies that must also be fetched:

```bash
git submodule update --init --recursive
make install
```

Usage
=====

Checking when pages are allowed
-------------------------------
Two classes answer questions about whether a URL is allowed: `Robots` and
`Agent`:

```python
from reppy.robots import Robots

# This utility uses `requests` to fetch the content
robots = Robots.fetch('http://example.com/robots.txt')
robots.allowed('http://example.com/some/path/', 'my-user-agent')

# Get the rules for a specific agent
agent = robots.agent('my-user-agent')
agent.allowed('http://example.com/some/path/')
```

The `Robots` class also exposes properties `expired` and `ttl` to describe how
long the response should be considered valid. A `reppy.ttl` policy is used to
determine what that should be:

```python
from reppy.ttl import HeaderWithDefaultPolicy

# Use the `cache-control` or `expires` headers, defaulting to a 30 minutes and
# ensuring it's at least 10 minutes
policy = HeaderWithDefaultPolicy(default=1800, minimum=600)

robots = Robots.fetch('http://example.com/robots.txt', ttl_policy=policy)
```

Customizing fetch
-----------------
The `fetch` method accepts `*args` and `**kwargs` that are passed on to `requests.get`,
allowing you to customize the way the `fetch` is executed:

```python
robots = Robots.fetch('http://example.com/robots.txt', headers={...})
```

Matching Rules and Wildcards
----------------------------
Both `*` and `$` are supported for wildcard matching.

This library follows the matching [1996 RFC](http://www.robotstxt.org/norobots-rfc.txt)
describes. In the case where multiple rules match a query, the longest rules wins as
it is presumed to be the most specific.

Checking sitemaps
-----------------
The `Robots` class also lists the sitemaps that are listed in a `robots.txt`

```python
# This property holds a list of URL strings of all the sitemaps listed
robots.sitemaps
```

Delay
-----
The `Crawl-Delay` directive is per agent and can be accessed through that class. If
none was specified, it's `None`:

```python
# What's the delay my-user-agent should use
robots.agent('my-user-agent').delay
```

Determining the `robots.txt` URL
--------------------------------
Given a URL, there's a utility to determine the URL of the corresponding `robots.txt`.
It preserves the scheme and hostname and the port (if it's not the default port for the
scheme).

```python
# Get robots.txt URL for http://userinfo@example.com:8080/path;params?query#fragment
# It's http://example.com:8080/robots.txt
Robots.robots_url('http://userinfo@example.com:8080/path;params?query#fragment')
```

Caching
=======
There are two cache classes provided -- `RobotsCache`, which caches entire `reppy.Robots`
objects, and `AgentCache`, which only caches the `reppy.Agent` relevant to a client. These
caches duck-type the class that they cache for the purposes of checking if a URL is
allowed:

```python
from reppy.cache import RobotsCache
cache = RobotsCache(capacity=100)
cache.allowed('http://example.com/foo/bar', 'my-user-agent')

from reppy.cache import AgentCache
cache = AgentCache(agent='my-user-agent', capacity=100)
cache.allowed('http://example.com/foo/bar')
```

Like `reppy.Robots.fetch`, the cache constructory accepts a `ttl_policy` to inform the
expiration of the fetched `Robots` objects, as well as `*args` and `**kwargs` to be passed
to `reppy.Robots.fetch`.

Caching Failures
----------------
There's a piece of classic caching advice: "don't cache failures." However, this is not
always appropriate in certain circumstances. For example, if the failure is a timeout,
clients may want to cache this result so that every check doesn't take a very long time.

To this end, the `cache` module provides a notion of a cache policy. It determines what
to do in the case of an exception. The default is to cache a form of a disallowed response
for 10 minutes, but you can configure it as you see fit:

```python
# Do not cache failures (note the `ttl=0`):
from reppy.cache.policy import ReraiseExceptionPolicy
cache = AgentCache('my-user-agent', cache_policy=ReraiseExceptionPolicy(ttl=0))

# Cache and reraise failures for 10 minutes (note the `ttl=600`):
cache = AgentCache('my-user-agent', cache_policy=ReraiseExceptionPolicy(ttl=600))

# Treat failures as being disallowed
cache = AgentCache(
    'my-user-agent',
    cache_policy=DefaultObjectPolicy(ttl=600, lambda _: Agent().disallow('/')))
```

Development
===========
A `Vagrantfile` is provided to bootstrap a development environment:

```bash
vagrant up
```

Alternatively, development can be conducted using a `virtualenv`:

```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Tests
=====
Tests may be run in `vagrant`:

```bash
make test
```

Development
===========

Environment
-----------
To launch the `vagrant` image, we only need to
`vagrant up` (though you may have to provide a `--provider` flag):

```bash
vagrant up
```

With a running `vagrant` instance, you can log in and run tests:

```bash
vagrant ssh
make test
```

Running Tests
-------------
Tests are run with the top-level `Makefile`:

```bash
make test
```

PRs
===
These are not all hard-and-fast rules, but in general PRs have the following expectations:

- __pass Travis__ -- or more generally, whatever CI is used for the particular project
- __be a complete unit__ -- whether a bug fix or feature, it should appear as a complete
    unit before consideration.
- __maintain code coverage__ -- some projects may include code coverage requirements as
    part of the build as well
- __maintain the established style__ -- this means the existing style of established
    projects, the established conventions of the team for a given language on new
    projects, and the guidelines of the community of the relevant languages and
    frameworks.
- __include failing tests__ -- in the case of bugs, failing tests demonstrating the bug
    should be included as one commit, followed by a commit making the test succeed. This
    allows us to jump to a world with a bug included, and prove that our test in fact
    exercises the bug.
- __be reviewed by one or more developers__ -- not all feedback has to be accepted, but
    it should all be considered.
- __avoid 'addressed PR feedback' commits__ -- in general, PR feedback should be rebased
    back into the appropriate commits that introduced the change. In cases, where this
    is burdensome, PR feedback commits may be used but should still describe the changed
    contained therein.

PR reviews consider the design, organization, and functionality of the submitted code.

Commits
=======
Certain types of changes should be made in their own commits to improve readability. When
too many different types of changes happen simultaneous to a single commit, the purpose of
each change is muddled. By giving each commit a single logical purpose, it is implicitly
clear why changes in that commit took place.

- __updating / upgrading dependencies__ -- this is especially true for invocations like
    `bundle update` or `berks update`.
- __introducing a new dependency__ -- often preceeded by a commit updating existing
    dependencies, this should only include the changes for the new dependency.
- __refactoring__ -- these commits should preserve all the existing functionality and
    merely update how it's done.
- __utility components to be used by a new feature__ -- if introducing an auxiliary class
    in support of a subsequent commit, add this new class (and its tests) in its own
    commit.
- __config changes__ -- when adjusting configuration in isolation
- __formatting / whitespace commits__ -- when adjusting code only for stylistic purposes.

New Features
------------
Small new features (where small refers to the size and complexity of the change, not the
impact) are often introduced in a single commit. Larger features or components might be
built up piecewise, with each commit containing a single part of it (and its corresponding
tests).

Bug Fixes
---------
In general, bug fixes should come in two-commit pairs: a commit adding a failing test
demonstrating the bug, and a commit making that failing test pass.

Tagging and Versioning
======================
Whenever the version included in `setup.py` is changed (and it should be changed when
appropriate using [http://semver.org/](http://semver.org/)), a corresponding tag should
be created with the same version number (formatted `v<version>`).

```bash
git tag -a v0.1.0 -m 'Version 0.1.0

This release contains an initial working version of the `crawl` and `parse`
utilities.'

git push --tags origin
```
