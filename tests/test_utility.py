#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''These are unit tests that are derived from the rfc at
http://www.robotstxt.org/norobots-rfc.txt'''

import unittest

import reppy
import logging
from reppy import Utility
reppy.logger.setLevel(logging.FATAL)


class TestUtility(unittest.TestCase):
    '''Make sure our utility functions work'''
    def test_cache_control(self):
        '''Make sure parsing of the ttl with cache control works'''
        for directive in ('no-cache', 'no-store', 'must-revalidate'):
            self.assertEqual(Utility.get_ttl({
                'cache-control': directive
            }, 5), 0)

        # Make sure that we can honor s-maxage
        for directive in ('s-maxage=10,foo', 's-maxage = 10'):
            self.assertEqual(Utility.get_ttl({
                'cache-control': directive
            }, 5), 10)
        # If we can't parse it as an integer, then we'll skip it
        self.assertEqual(Utility.get_ttl({
            'cache-control': 's-maxage = not int'
        }, 5), 5)

        # Make sure we can honor max-age
        for directive in ('max-age=10,foo', 'max-age = 10'):
            self.assertEqual(Utility.get_ttl({
                'cache-control': directive
            }, 5), 10)
        # If we can't parse it as an integer, then we'll skip it
        self.assertEqual(Utility.get_ttl({
            'cache-control': 'max-age = not int'
        }, 5), 5)

    def test_expires(self):
        '''Make sure we can honor Expires'''
        # Test a plain-and-simple expires, using now as a default time
        import datetime
        ttl = Utility.get_ttl({
            'expires': (
                datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
            ).strftime('%a, %d %b %Y %H:%M:%S %z')
        }, 5)
        self.assertLess(ttl, 11)
        self.assertGreater(ttl, 9)

        # Make sure this works when a date is provided
        now = datetime.datetime.utcnow()
        ttl = self.assertEqual(Utility.get_ttl({
            'expires': (
                now + datetime.timedelta(seconds=10)
            ).strftime('%a, %d %b %Y %H:%M:%S %z'),
            'date': (
                now
            ).strftime('%a, %d %b %Y %H:%M:%S %z')
        }, 5), 10)

        # If the date is unparseable, use 'now'
        ttl = Utility.get_ttl({
            'expires': (
                datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
            ).strftime('%a, %d %b %Y %H:%M:%S %z'),
            'date': 'not a valid time'
        }, 5)
        self.assertLess(ttl, 11)
        self.assertGreater(ttl, 9)

        # Lastly, if the 'expires' header is unparseable, then pass
        ttl = self.assertEqual(Utility.get_ttl({
            'expires': 'not a valid time'
        }, 5), 5)
