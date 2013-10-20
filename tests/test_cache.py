#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''These are unit tests that are derived from the rfc at
http://www.robotstxt.org/norobots-rfc.txt'''

import unittest
import sys

if sys.version_info[0] == 3:
    # We cannot run these tests on Python 3 yet, because they rely
    # on the asis module and gevent, both of which are not available.
    raise unittest.SkipTest()

# We need to monkey-path socket
from gevent import monkey; monkey.patch_all()
import asis
import reppy
import logging
from reppy.cache import RobotsCache
from reppy.exceptions import ServerError
reppy.logger.setLevel(logging.FATAL)


class TestCache(unittest.TestCase):
    def setUp(self):
        self.robots = RobotsCache()

    def test_404(self):
        '''When we get a 404, assume free range'''
        with asis.Server('tests/asis/test_404', port=8080):
            self.assertEqual(self.robots.allowed(
                'http://localhost:8080/foo', 'rogerbot'), True)

    def test_caching(self):
        '''We should be able to cache results'''
        with asis.Server('tests/asis/test_caching', port=8080):
            self.assertEqual(
                self.robots.find('http://localhost:8080/foo'), None)
            self.robots.allowed('http://localhost:8080/foo', 'rogerbot')
            self.assertNotEqual(
                self.robots.find('http://localhost:8080/foo'), None)

    def test_context_manager(self):
        '''When using as a context manager, it should clear afterwards'''
        with asis.Server('tests/asis/test_context_manager', port=8080):
            with self.robots:
                self.assertEqual(
                    self.robots.find('http://localhost:8080/foo'), None)
                self.robots.allowed('http://localhost:8080/foo', 'rogerbot')
                self.assertNotEqual(
                    self.robots.find('http://localhost:8080/foo'), None)
            # And now, we should have it no longer cached
            self.assertEqual(
                self.robots.find('http://localhost:8080/foo'), None)

    def test_expires(self):
        '''Should be able to recognize expired rules'''
        with asis.Server('tests/asis/test_expires', port=8080):
            self.assertNotEqual(
                self.robots.find('http://localhost:8080/foo', True), None)
            # Now, it shouldn't be cached, so when we find it again, it should
            # be missing (or at least, requiring a refetch)
            self.assertEqual(
                self.robots.find('http://localhost:8080/foo', False), None)

    def test_clear(self):
        '''Should be able to explicitly clear rules'''
        with asis.Server('tests/asis/test_clear', port=8080):
            self.assertEqual(
                self.robots.find('http://localhost:8080/foo'), None)
            self.robots.allowed('http://localhost:8080/foo', 'rogerbot')
            self.assertNotEqual(
                self.robots.find('http://localhost:8080/foo'), None)
            # Now if we clear the rules, we should not find it
            self.robots.clear()
            self.assertEqual(
                self.robots.find('http://localhost:8080/foo'), None)

    def test_fetch(self):
        '''Ensure that 'fetch' doesn't cache'''
        with asis.Server('tests/asis/test_fetch', port=8080):
            self.assertNotEqual(
                self.robots.fetch('http://localhost:8080/foo'), None)
            self.assertEqual(
                self.robots.find('http://localhost:8080/foo'), None)

    def test_cache(self):
        '''Ensure we can ask it to cache a result'''
        with asis.Server('tests/asis/test_cache', port=8080):
            self.assertEqual(
                self.robots.find('http://localhost:8080/foo'), None)
            self.assertNotEqual(
                self.robots.cache('http://localhost:8080/foo'), None)
            self.assertNotEqual(
                self.robots.find('http://localhost:8080/foo'), None)

    def test_add(self):
        '''We should be able to add rules that we get'''
        with asis.Server('tests/asis/test_add', port=8080):
            self.assertEqual(
                self.robots.find('http://localhost:8080/foo'), None)
            self.robots.add(self.robots.fetch(
                'http://localhost:8080/foo'))
            self.assertNotEqual(
                self.robots.find('http://localhost:8080/foo'), None)

    def test_server_error(self):
        '''Make sure we can catch server errors'''
        self.assertRaises(ServerError, self.robots.allowed,
            'http://localhost:8080/foo', 'rogerbot')

    def test_disallowed(self):
        '''Check the disallowed interface'''
        with asis.Server('tests/asis/test_disallowed', port=8080):
            self.assertFalse(self.robots.disallowed(
                'http://localhost:8080/foo', 'rogerbot'))
            urls = [
                'http://localhost:8080/foo',
                'http://localhost:8080/bar'
            ]
            self.assertEqual(self.robots.allowed(urls, 'rogerbot'), urls)
            self.assertEqual(self.robots.disallowed(urls, 'rogerbot'), [])

    def test_delay(self):
        '''Check the delay interface'''
        with asis.Server('tests/asis/test_delay', port=8080):
            self.assertEqual(self.robots.delay(
                'http://localhost:8080/foo', 'rogerbot'), 5)

    def test_sitemaps(self):
        '''Check the sitemaps interface'''
        with asis.Server('tests/asis/test_sitemaps', port=8080):
            self.assertEqual(
                self.robots.sitemaps('http://localhost:8080/foo'), [
                    'http://localhost:8080/a',
                    'http://localhost:8080/b',
                    'http://localhost:8080/c'
                ])
