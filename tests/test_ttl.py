import unittest

import mock

from reppy import ttl


class TTLPolicyBaseTest(unittest.TestCase):
    '''Tests about TTLPolicyBase.'''

    def test_does_not_implement_ttl(self):
        '''Does not implement the ttl method.'''
        with self.assertRaises(NotImplementedError):
            ttl.TTLPolicyBase().ttl(object())

    def test_implements_expires(self):
        '''Expires is based off of ttl.'''
        policy = ttl.TTLPolicyBase()
        with mock.patch.object(policy, 'ttl', return_value=10):
            with mock.patch.object(ttl.time, 'time', return_value=100):
                self.assertEqual(policy.expires(object()), 110)


class HeaderWithDefaultPolicyTest(unittest.TestCase):
    '''Tests about HeaderWithDefaultPolicy.'''

    def test_no_store(self):
        '''Returns the minimum when no-store present.'''
        response = mock.Mock(headers={
            'cache-control': 'no-store'
        })
        policy = ttl.HeaderWithDefaultPolicy(20, 10)
        self.assertEqual(policy.ttl(response), 10)

    def test_must_revalidate(self):
        '''Returns the minimum when must-revalidate present.'''
        response = mock.Mock(headers={
            'cache-control': 'must-revalidate'
        })
        policy = ttl.HeaderWithDefaultPolicy(20, 10)
        self.assertEqual(policy.ttl(response), 10)

    def test_no_cache(self):
        '''Returns the minimum when no-cache present.'''
        response = mock.Mock(headers={
            'cache-control': 'no-cache'
        })
        policy = ttl.HeaderWithDefaultPolicy(20, 10)
        self.assertEqual(policy.ttl(response), 10)

    def test_s_maxage(self):
        '''Returns the parsed s-maxage.'''
        response = mock.Mock(headers={
            'cache-control': 's-maxage=15'
        })
        policy = ttl.HeaderWithDefaultPolicy(20, 10)
        self.assertEqual(policy.ttl(response), 15)

    def test_max_age(self):
        '''Returns the parsed max-age.'''
        response = mock.Mock(headers={
            'cache-control': 'max-age=15'
        })
        policy = ttl.HeaderWithDefaultPolicy(20, 10)
        self.assertEqual(policy.ttl(response), 15)

    def test_default_for_malformed_maxage(self):
        '''Returns the default when maxage cannot be parsed.'''
        response = mock.Mock(headers={
            'cache-control': 'max-age=not-a-number'
        })
        policy = ttl.HeaderWithDefaultPolicy(20, 10)
        self.assertEqual(policy.ttl(response), 20)

    def test_multiple_cache_control(self):
        '''Can walk through multiple cache control configs.'''
        response = mock.Mock(headers={
            'cache-control': 'foo, max-age=15'
        })
        policy = ttl.HeaderWithDefaultPolicy(20, 10)
        self.assertEqual(policy.ttl(response), 15)

    def test_expires_with_no_date(self):
        '''Uses the host computer's date when the Date header is absent.'''
        expires = 'Thu, 13 Oct 2016 15:50:54 GMT'
        response = mock.Mock(headers={
            'expires': expires
        })
        policy = ttl.HeaderWithDefaultPolicy(20, 10)
        timestamp = ttl.parse_date(expires)
        expected = 60
        with mock.patch.object(ttl.time, 'time', return_value=timestamp - expected):
            self.assertEqual(policy.ttl(response), expected)

    def test_expires_with_malformed_date(self):
        '''Uses the host computer's date when the Date header is unparseable.'''
        expires = 'Thu, 13 Oct 2016 15:50:54 GMT'
        response = mock.Mock(headers={
            'expires': expires,
            'date': 'not parseable as a date'
        })
        policy = ttl.HeaderWithDefaultPolicy(20, 10)
        timestamp = ttl.parse_date(expires)
        expected = 60
        with mock.patch.object(ttl.time, 'time', return_value=timestamp - expected):
            self.assertEqual(policy.ttl(response), expected)

    def test_expires_with_date(self):
        '''Uses the Date header when present.'''
        response = mock.Mock(headers={
            'expires': 'Thu, 13 Oct 2016 15:50:54 GMT',
            'date': 'Thu, 13 Oct 2016 15:49:54 GMT'
        })
        policy = ttl.HeaderWithDefaultPolicy(20, 10)
        self.assertEqual(policy.ttl(response), 60)

    def test_malformed_expires(self):
        '''Returns the default when the Expires header is malformed.'''
        response = mock.Mock(headers={
            'expires': 'not parseable as a date'
        })
        policy = ttl.HeaderWithDefaultPolicy(20, 10)
        self.assertEqual(policy.ttl(response), 20)

    def test_cache_control_precedence(self):
        '''Cache control is used before expires.'''
        response = mock.Mock(headers={
            'cache-control': 'max-age=30',
            'expires': 'Thu, 13 Oct 2016 15:50:54 GMT',
            'date': 'Thu, 13 Oct 2016 15:49:54 GMT'
        })
        policy = ttl.HeaderWithDefaultPolicy(20, 10)
        self.assertEqual(policy.ttl(response), 30)
