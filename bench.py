#! /usr/bin/env python

from __future__ import print_function

from contextlib import contextmanager
import sys
import time

from reppy.cache import RobotsCache
from reppy.parser import Rules

content = '''
User-agent: '*'
Allow: /
'''

cache = RobotsCache()
cache.add(Rules('http://example.com/', 200, content, sys.maxint))

@contextmanager
def timer(count):
    '''Time this block.'''
    start = time.time()
    try:
        yield count
    finally:
        duration = time.time() - start
        print('Total: %s' % duration)
        print('  Avg: %s' % (duration / count))
        print(' Rate: %s' % (count / duration))

with timer(100000) as count:
    for _ in xrange(count):
        cache.allowed('http://example.com/page', 'agent')
