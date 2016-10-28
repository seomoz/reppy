#! /usr/bin/env python

from __future__ import print_function

from contextlib import contextmanager
import sys
import time

from reppy.robots import Robots
content = '''
# /robots.txt for http://www.fict.org/
# comments to webmaster@fict.org

User-agent: unhipbot
Disallow: /

User-agent: webcrawler
User-agent: excite
Disallow:

User-agent: *
Disallow: /org/plans.html
Allow: /org/
Allow: /serv
Allow: /~mak
Disallow: /
'''

@contextmanager
def timer(name, count):
    '''Time this block.'''
    start = time.time()
    try:
        yield count
    finally:
        duration = time.time() - start
        print(name)
        print('=' * 10)
        print('Total: %s' % duration)
        print('  Avg: %s' % (duration / count))
        print(' Rate: %s' % (count / duration))
        print('')


with timer('Parse', 100000) as count:
    for _ in xrange(count):
        Robots.parse('http://example.com/robots.txt', content)


parsed = Robots.parse('http://example.com/robots.txt', content)
with timer('Evaluate', 100000) as count:
    for _ in xrange(count):
        parsed.allowed('/org/example.html', 'other-bot')
