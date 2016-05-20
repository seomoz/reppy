#!/usr/bin/env python

# Copyright (c) 2011 SEOmoz
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

try:
    from setuptools import setup
    extra = {
        'install_requires': ['python-dateutil>=1.5, !=2.0', 'url', 'requests']
    }
except ImportError:
    from distutils.core import setup
    extra = {
        'dependencies': ['python-dateutil>=1.5, !=2.0', 'url', 'requests']
    }

setup(
    name             = 'reppy',
    version          = '0.3.2',
    description      = 'Replacement robots.txt Parser',
    long_description = '''Replaces the built-in robotsparser with a
RFC-conformant implementation that supports modern robots.txt constructs like
Sitemaps, Allow, and Crawl-delay. Main features:

- Memoization of fetched robots.txt
- Expiration taken from the `Expires` header
- Batch queries
- Configurable user agent for fetching robots.txt
- Automatic refetching basing on expiration
''',
    author           = 'Dan Lecocq',
    author_email     = 'dan@seomoz.org',
    url              = 'http://github.com/seomoz/reppy',
    packages         = ['reppy'],
    license          = 'MIT',
    platforms        = 'Posix; MacOS X',
    test_suite       = 'tests.testReppy',
    classifiers      = [
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP'],
    **extra
)
