'''Tests about our caching policies.'''

import unittest

import mock

from reppy.cache import policy


class TestCachePolicyBase(unittest.TestCase):
    '''Tests about CachePolicyBase.'''

    def test_exception_not_implemented(self):
        '''Does not implement the exception method.'''
        with self.assertRaises(NotImplementedError):
            policy.CachePolicyBase().exception(
                'http://example.com/', ValueError('Kaboom'))


class TestDefaultObjectPolicy(unittest.TestCase):
    '''Tests about DefaultObjectPolicy.'''

    def setUp(self):
        self.factory = mock.Mock()
        self.ttl = 17
        self.policy = policy.DefaultObjectPolicy(self.ttl, self.factory)

    def test_uses_ttl(self):
        '''Uses the provided TTL.'''
        with mock.patch.object(policy.time, 'time', return_value=0):
            expiration, _ = self.policy.exception(
                'http://example.com/', ValueError('Kaboom'))
            self.assertEqual(expiration, self.ttl)

    def test_uses_factory(self):
        '''Uses the provided factory.'''
        _, value = self.policy.exception('http://example.com/', ValueError('Kaboom'))
        self.assertEqual(value, self.factory.return_value)


class TestReraiseExceptionPolicy(unittest.TestCase):
    '''Tests about ReraiseExceptionPolicy.'''

    def setUp(self):
        self.ttl = 17
        self.policy = policy.ReraiseExceptionPolicy(self.ttl)

    def test_uses_ttl(self):
        '''Uses the provided TTL.'''
        with mock.patch.object(policy.time, 'time', return_value=0):
            expiration, _ = self.policy.exception(
                'http://example.com/', ValueError('Kaboom'))
            self.assertEqual(expiration, self.ttl)

    def test_returns_exception(self):
        '''Returns whatever exception was passed in.'''
        exception = ValueError('Kaboom')
        _, value = self.policy.exception('http://example.com/', exception)
        self.assertEqual(value, exception)
