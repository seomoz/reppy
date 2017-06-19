#!/usr/bin/env python

# Copyright (c) 2011-2017 SEOmoz, Inc.
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

from distutils.core import setup
from distutils.extension import Extension

ext_files = [
    'reppy/rep-cpp/src/agent.cpp',
    'reppy/rep-cpp/src/directive.cpp',
    'reppy/rep-cpp/src/robots.cpp',
    'reppy/rep-cpp/deps/url-cpp/src/url.cpp',
    'reppy/rep-cpp/deps/url-cpp/src/utf8.cpp',
    'reppy/rep-cpp/deps/url-cpp/src/punycode.cpp',
    'reppy/rep-cpp/deps/url-cpp/src/psl.cpp'
]

kwargs = {}

try:
    from Cython.Distutils import build_ext
    print('Building from Cython')
    ext_files.append('reppy/robots.pyx')
    kwargs['cmdclass'] = {'build_ext': build_ext}
except ImportError:
    print('Building from C++')
    ext_files.append('reppy/robots.cpp')

ext_modules = [
    Extension(
        'reppy.robots', ext_files,
        language='c++',
        extra_compile_args=['-std=c++11'],
        include_dirs=[
            'reppy/rep-cpp/include',
            'reppy/rep-cpp/deps/url-cpp/include'])
]

setup(
    name='reppy',
    version='0.4.7',
    description='Replacement robots.txt Parser',
    long_description='''Replaces the built-in robotsparser with a
RFC-conformant implementation that supports modern robots.txt constructs like
Sitemaps, Allow, and Crawl-delay. Main features:

- Memoization of fetched robots.txt
- Expiration taken from the `Expires` header
- Batch queries
- Configurable user agent for fetching robots.txt
- Automatic refetching based on expiration
''',
    maintainer='Brandon Forehand',
    maintainer_email='brandon@moz.com',
    url='http://github.com/seomoz/reppy',
    license='MIT',
    platforms='Posix; MacOS X',
    ext_modules=ext_modules,
    packages=[
        'reppy',
        'reppy.cache'
    ],
    package_dir={
        'reppy': 'reppy',
        'reppy.cache': 'reppy/cache'
    },
    install_requires=[
        'cachetools',
        'python-dateutil>=1.5, !=2.0',
        'requests',
        'six'
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ],
    **kwargs
)
