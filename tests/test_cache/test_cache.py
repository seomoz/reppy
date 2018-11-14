from __future__ import print_function

'''Tests about our caching utilities.'''

import unittest
import mock

import sys

from reppy import cache
from reppy import logger
import reppy.exceptions

from ..util import requests_fixtures


class TestExpiringObject(unittest.TestCase):
    '''Tests about ExpiringObject.'''

    def test_uses_factory(self):
        '''Uses the result from the factory.'''
        factory = mock.Mock(return_value=(10, 'result'))
        obj = cache.ExpiringObject(factory)
        self.assertEqual(obj.get(), 'result')
        self.assertEqual(obj.expires, 10)

    def test_memoizes_cached_result(self):
        '''Memoizes what's returned by the factory.'''
        factory = mock.Mock(return_value=(10, 'result'))
        obj = cache.ExpiringObject(factory)
        with mock.patch.object(cache.time, 'time', return_value=0):
            for _ in range(10):
                obj.get()
        self.assertEqual(factory.call_count, 1)

    def test_reraise_exception(self):
        '''If the provided factory returns an exception, reraise it.'''
        factory = mock.Mock(return_value=(10, ValueError('Kaboom!')))
        obj = cache.ExpiringObject(factory)
        with self.assertRaises(ValueError):
            obj.get()
        self.assertEqual(obj.expires, 10)


class TestBaseCache(unittest.TestCase):
    '''Tests about BaseCache.'''

    def test_does_not_implement_missing(self):
        '''Does not implement the missing method.'''
        with self.assertRaises(NotImplementedError):
            cache.BaseCache(10).fetch('http://example.com/robots.txt')

class TestBaseCacheLRUCacheWithMissingHandler(unittest.TestCase):
    '''Tests LRUCacheWithMissingHandler'''

    def calls_the_missing_function(self):
        # missing ...
        def missing(item):
            return item + item
        cache = cache.LRUCacheWithMissingHandler(maxsize=123, missing=missing)
        self.assertEqual(cache[5], 10)
        self.assertEqual(cache[6], 12)
        self.assertEqual(5 in cache, True)
        self.assertEqual(6 in cache, True)

    def caches_the_result_of_the_missing_function(self):
        calls = []
        def missing(item):
            calls.append(item)
            return item * item
        cache = cache.LRUCacheWithMissingHandler(maxsize=123, missing=missing)
        self.assertEqual(cache[5], 10)
        self.assertEqual(cache[6], 12)
        self.assertEqual(cache[6], 12)
        self.assertEqual(cache[5], 10)
        self.assertEqual(calls, [5, 6])

    def fills_up_capactity(self):
        def missing(item):
            return item + item
        cache = cache.LRUCacheWithMissingHandler(maxsize=2, missing=missing)
        self.assertEqual(cache[5], 10)
        self.assertEqual(cache[6], 12)
        self.assertEqual(cache[7], 14)
        self.assertEqual(5 in cache, False)
        self.assertEqual(6 in cache, True)
        self.assertEqual(7 in cache, True)


class TestRobotsCache(unittest.TestCase):
    '''Tests about RobotsCache.'''

    def setUp(self):
        self.cache = cache.RobotsCache(10)

    def test_returns_a_robots_object(self):
        '''Returns a Robots object.'''
        with requests_fixtures('test_returns_a_robots_object'):
            self.assertIsInstance(
                self.cache.get('http://example.com/blog'), cache.Robots)

    def test_returns_allow_none_on_failure(self):
        '''Returns a AllowNone object on exception.'''
        self.assertIsInstance(
            self.cache.get('http://does-not-resolve/'), cache.AllowNone)

    def test_uses_default_expiration_on_failure(self):
        '''When we get AllowNone, it uses the default expiration.'''
        with mock.patch.object(self.cache.cache_policy, 'ttl', 17):
            with mock.patch.object(cache.time, 'time', return_value=0):
                self.cache.get('http://does-not-resolve/')
                self.assertEqual(
                    self.cache.cache['http://does-not-resolve/robots.txt'].expires, 17)

    def test_robots_allowed(self):
        '''Can check for allowed.'''
        with requests_fixtures('test_robots_allowed'):
            self.assertFalse(
                self.cache.allowed('http://example.com/disallowed', 'agent'))
            self.assertTrue(
                self.cache.allowed('http://example.com/allowed', 'agent'))

    def test_caches_robots(self):
        '''Caches robots responses.'''
        with requests_fixtures('test_caches_robots'):
            self.cache.get('http://example.com/')

        # The fact that these pass without the `requests_fixtures` block demonstrates
        # that these don't result in a second fetch.
        self.assertFalse(
            self.cache.allowed('http://example.com/disallowed', 'agent'))
        self.assertTrue(
            self.cache.allowed('http://example.com/allowed', 'agent'))


class TestAgentCache(unittest.TestCase):
    '''Tests about AgentCache.'''

    def setUp(self):
        self.cache = cache.AgentCache('agent', 10)

    def test_returns_an_agent_object(self):
        '''Returns a Robots object.'''
        with requests_fixtures('test_returns_an_agent_object'):
            self.assertIsInstance(
                self.cache.get('http://example.com/blog'), cache.Agent)

    def test_allows_none_on_failure(self):
        '''Nothing is allowed on failure.'''
        self.assertFalse(
            self.cache.get('http://does-not-resolve/').allowed('/path'))

    def test_uses_default_expiration_on_failure(self):
        '''On fetch failure, it uses the default expiration.'''
        with mock.patch.object(self.cache.cache_policy, 'ttl', 17):
            with mock.patch.object(cache.time, 'time', return_value=0):
                self.cache.get('http://does-not-resolve/')
                self.assertEqual(
                    self.cache.cache['http://does-not-resolve/robots.txt'].expires, 17)

    def test_logs_on_failure(self):
        '''On fetch failure, it logs the exception.'''
        logs = []
        def mock_logger(msg):
            exc_type = sys.exc_info()[0]
            logs.append( (exc_type, msg) )
        with mock.patch.object(logger, 'exception', mock_logger):
            self.cache.get('http://does-not-resolve/')

            expected_err = reppy.exceptions.ConnectionException
            expected_msg = 'Reppy cache fetch error on http://does-not-resolve/robots.txt'
            self.assertIn((expected_err, expected_msg), logs)

    def test_agent_allowed(self):
        '''Can check for allowed.'''
        with requests_fixtures('test_agent_allowed'):
            self.assertFalse(
                self.cache.allowed('http://example.com/disallowed'))
            self.assertTrue(
                self.cache.allowed('http://example.com/allowed'))

    def test_caches_agent(self):
        '''Caches agent responses.'''
        with requests_fixtures('test_caches_agent'):
            self.cache.get('http://example.com/')

        # The fact that these pass without the `requests_fixtures` block demonstrates
        # that these don't result in a second fetch.
        self.assertFalse(
            self.cache.allowed('http://example.com/disallowed'))
        self.assertTrue(
            self.cache.allowed('http://example.com/allowed'))
