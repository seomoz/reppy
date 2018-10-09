#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

'''These are unit tests that are derived from the rfc at
http://www.robotstxt.org/norobots-rfc.txt'''

import codecs
import unittest

import mock
from requests.exceptions import SSLError

from reppy import robots

from .util import requests_fixtures


class RobotsTest(unittest.TestCase):
    '''Tests about our Robots class.'''

    def test_expired(self):
        '''Returns true if expired.'''
        with mock.patch.object(robots.time, 'time', return_value=10):
            robot = robots.Robots.parse('http://example.com/robots.txt', '', expires=5)
            self.assertTrue(robot.expired)

    def test_not_expired(self):
        '''Returns false if not expired.'''
        with mock.patch.object(robots.time, 'time', return_value=10):
            robot = robots.Robots.parse('http://example.com/robots.txt', '', expires=15)
            self.assertFalse(robot.expired)

    def test_ttl(self):
        '''Returns the time remaining until expiration.'''
        with mock.patch.object(robots.time, 'time', return_value=10):
            robot = robots.Robots.parse('http://example.com/robots.txt', '', expires=15)
            self.assertEqual(robot.ttl, 5)

    def test_no_leading_user_agent(self):
        '''Treats missing User-Agent as default user agent'''
        robot = robots.Robots.parse('http://example.com/robots.txt', '''
            Disallow: /path
            Allow: /path/exception
            Crawl-delay: 7
        ''')
        self.assertNotEqual(robot.agent('agent'), None)
        self.assertTrue(robot.allowed('/path/exception', 'agent'))
        self.assertFalse(robot.allowed('/path', 'agent'))
        self.assertTrue(robot.allowed('/', 'agent'))
        self.assertEquals(robot.agent('agent').delay, 7)

    def test_malformed_crawl_delay(self):
        '''Handles a malformed delay.'''
        robot = robots.Robots.parse('http://example.com/robots.txt', '''
            User-agent: *
            Crawl-delay: word
        ''')
        self.assertEqual(robot.agent('agent').delay, None)

    def test_honors_default_agents(self):
        '''Honors the default user agent when that's all that's available.'''
        robot = robots.Robots.parse('http://example.com/robots.txt', '''
            User-agent: *
            Disallow: /tmp

            User-agent: other-agent
            Allow: /tmp
        ''')
        self.assertFalse(robot.allowed('/tmp', 'agent'))
        self.assertTrue(robot.allowed('/path', 'agent'))

    def test_honors_specific_agent(self):
        '''Honors the specific user agent if a match is found.'''
        robot = robots.Robots.parse('http://example.com/robots.txt', '''
            User-agent: *
            Disallow: /tmp

            User-agent: agent
            Allow: /tmp
        ''')
        self.assertTrue(robot.allowed('/tmp', 'agent'))
        self.assertTrue(robot.allowed('/path', 'agent'))

    def test_grouping(self):
        '''Multiple consecutive User-Agent lines are allowed.'''
        robot = robots.Robots.parse('http://example.com/robots.txt', '''
            User-agent: one
            User-agent: two
            Disallow: /tmp
        ''')
        self.assertFalse(robot.allowed('/tmp', 'one'))
        self.assertFalse(robot.allowed('/tmp', 'two'))

    def test_grouping_unknown_keys(self):
        '''
        When we encounter unknown keys, we should disregard any grouping that may have
        happened between user agent rules.

        This is an example from the wild. Despite `Noindex` not being a valid directive,
        we'll not consider the '*' and 'ia_archiver' rules together.
        '''
        rules = robots.Robots.parse('http://example.com/robots.txt', '''
            User-agent: *
            Disallow: /content/2/
            User-agent: *
            Noindex: /gb.html
            Noindex: /content/2/
            User-agent: ia_archiver
            Disallow: /
        ''')
        self.assertTrue(rules.allowed('/foo', 'agent'))
        self.assertTrue(not rules.allowed('/bar', 'ia_archiver'))

    def test_separates_agents(self):
        '''Hands back an appropriate agent.'''
        robot = robots.Robots.parse('http://example.com/robots.txt', '''
            User-agent: one
            Crawl-delay: 1

            User-agent: two
            Crawl-delay: 2
        ''')
        self.assertNotEqual(
            robot.agent('one').delay,
            robot.agent('two').delay)

    def test_exposes_sitemaps(self):
        '''Finds and exposes sitemaps.'''
        robot = robots.Robots.parse('http://example.com/robots.txt', '''
            Sitemap: http://a.com/sitemap.xml
            Sitemap: http://b.com/sitemap.xml
        ''')
        self.assertEqual(list(robot.sitemaps), [
            'http://a.com/sitemap.xml', 'http://b.com/sitemap.xml'
        ])

    def test_case_insensitivity(self):
        '''Make sure user agent matches are case insensitive'''
        robot = robots.Robots.parse('http://example.com/robots.txt', '''
            User-agent: Agent
            Disallow: /path
        ''')
        self.assertFalse(robot.allowed('/path', 'agent'))
        self.assertFalse(robot.allowed('/path', 'aGeNt'))

    def test_empty(self):
        '''Makes sure we can parse an empty robots.txt'''
        robot = robots.Robots.parse('http://example.com/robots.txt', '')
        self.assertEqual(list(robot.sitemaps), [])
        self.assertTrue(robot.allowed('/', 'agent'))

    def test_comments(self):
        '''Robust against comments.'''
        robot = robots.Robots.parse('http://example.com/robots.txt', '''
            User-Agent: *  # comment saying it's the default agent
            Allow: /
        ''')
        self.assertNotEqual(robot.agent('agent'), None)

    def test_accepts_full_url(self):
        '''Can accept a url string.'''
        robot = robots.Robots.parse('http://example.com/robots.txt', '''
            User-Agent: agent
            Disallow: /
        ''')
        self.assertFalse(robot.allowed('http://example.com/path', 'agent'))

    def test_skip_malformed_line(self):
        '''If there is no colon in a line, then we must skip it'''
        robot = robots.Robots.parse('http://example.com/robots.txt', '''
            User-Agent: agent
            Disallow /no/colon/in/this/line
        ''')
        self.assertTrue(robot.allowed('/no/colon/in/this/line', 'agent'))

    def test_fetch_status_200(self):
        '''A 200 parses things normally.'''
        with requests_fixtures('test_fetch_status_200'):
            robot = robots.Robots.fetch('http://localhost:8080/robots.txt')
            self.assertFalse(robot.allowed('/path', 'agent'))

    def test_fetch_status_401(self):
        '''A 401 gives us an AllowNone Robots.'''
        with requests_fixtures('test_fetch_status_401'):
            robot = robots.Robots.fetch('http://localhost:8080/robots.txt')
            self.assertIsInstance(robot, robots.AllowNone)

    def test_fetch_status_403(self):
        '''A 403 gives us an AllowNone Robots.'''
        with requests_fixtures('test_fetch_status_403'):
            robot = robots.Robots.fetch('http://localhost:8080/robots.txt')
            self.assertIsInstance(robot, robots.AllowNone)

    def test_fetch_status_4XX(self):
        '''A 4XX gives us an AllowAll Robots.'''
        with requests_fixtures('test_fetch_status_4XX'):
            robot = robots.Robots.fetch('http://localhost:8080/robots.txt')
            self.assertIsInstance(robot, robots.AllowAll)

    def test_fetch_status_5XX(self):
        '''A server error raises an exception.'''
        with requests_fixtures('test_fetch_status_5XX'):
            with self.assertRaises(robots.exceptions.BadStatusCode):
                robots.Robots.fetch('http://localhost:8080/robots.txt')

    def test_content_too_big(self):
        '''Raises an exception if the content is too big.'''
        with requests_fixtures('test_content_too_big'):
            with self.assertRaises(robots.exceptions.ReppyException):
                robots.Robots.fetch('http://localhost:8080/robots.txt', max_size=5)

    def test_ssl_exception(self):
        '''Raises a ReppyException on SSL errors.'''
        with mock.patch.object(robots.requests, 'get', side_effect=SSLError('Kaboom')):
            with self.assertRaises(robots.exceptions.SSLException):
                robots.Robots.fetch('https://localhost:8080/robots.txt')

    def test_connection_exception(self):
        '''Raises a ReppyException on connection errors.'''
        with self.assertRaises(robots.exceptions.ConnectionException):
            robots.Robots.fetch('http://localhost:8080/robots.txt')

    def test_malformed_url(self):
        '''Raises a ReppyException on malformed URLs.'''
        with self.assertRaises(robots.exceptions.MalformedUrl):
            robots.Robots.fetch('gobbledygook')

    def test_excessive_redirects(self):
        '''Raises a ReppyException on too many redirects.'''
        with requests_fixtures('test_excessive_redirects'):
            with self.assertRaises(robots.exceptions.ExcessiveRedirects):
                robots.Robots.fetch('http://localhost:8080/robots.txt')

    def test_robots_url_http(self):
        '''Works with a http URL.'''
        url = 'http://user@example.com:80/path;params?query#fragment'
        expected = 'http://example.com/robots.txt'
        self.assertEqual(robots.Robots.robots_url(url), expected)

    def test_robots_url_https(self):
        '''Works with a https URL.'''
        url = 'https://user@example.com:443/path;params?query#fragment'
        expected = 'https://example.com/robots.txt'
        self.assertEqual(robots.Robots.robots_url(url), expected)

    def test_robots_url_non_default_port(self):
        '''Works with a URL with a non-default port.'''
        url = 'http://user@example.com:8080/path;params?query#fragment'
        expected = 'http://example.com:8080/robots.txt'
        self.assertEqual(robots.Robots.robots_url(url), expected)

    def test_robots_url_invalid_port(self):
        '''Raises exception when given an invalid port.'''
        url = 'http://:::cnn.com/'
        with self.assertRaises(ValueError):
            robots.Robots.robots_url(url)

    def test_utf8_bom(self):
        '''If there's a utf-8 BOM, we should parse it as such'''
        robot = robots.Robots.parse('http://example.com/robots.txt',
            codecs.BOM_UTF8 + b'''
            User-Agent: agent
            Allow: /path

            User-Agent: other
            Disallow: /path
        ''')
        self.assertTrue(robot.allowed('http://example.com/path', 'agent'))
        self.assertFalse(robot.allowed('http://example.com/path', 'other'))

    def test_str_function(self):
        '''
        If there is valid UTF-8, str() should return a representation of the
        directives.

        This came out of a UnicodeDecodeError happening in Python 2, when we
        were unduly decoding the bytes (via UTF-8) to unicode, then implictly
        converting back to bytes via UTF-8.
        '''
        robot = robots.Robots.parse('http://example.com/robots.txt',
            codecs.BOM_UTF8 + b'''
            User-Agent: \xc3\xa4gent
            Allow: /swedish-chef
        ''')
        s = str(robot)
        self.assertTrue('ägent' in s)

    def test_utf16_bom(self):
        '''If there's a utf-16 BOM, we should parse it as such'''
        robot = robots.Robots.parse('http://example.com/robots.txt',
            codecs.BOM_UTF16 + b'''
            User-Agent: agent
            Allow: /path

            User-Agent: other
            Disallow: /path
        ''')
        self.assertTrue(robot.allowed('http://example.com/path', 'agent'))
        self.assertFalse(robot.allowed('http://example.com/path', 'other'))

    def test_rfc_example(self):
        '''Tests the example provided by the RFC.'''
        robot = robots.Robots.parse('http://www.fict.org', '''
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
        ''')

        # The unhip bot
        self.assertFalse(robot.allowed('/', 'unhipbot'))
        self.assertFalse(robot.allowed('/index.html', 'unhipbot'))
        self.assertTrue(robot.allowed('/robots.txt', 'unhipbot'))
        self.assertFalse(robot.allowed('/server.html', 'unhipbot'))
        self.assertFalse(robot.allowed('/services/fast.html', 'unhipbot'))
        self.assertFalse(robot.allowed('/services/slow.html', 'unhipbot'))
        self.assertFalse(robot.allowed('/orgo.gif', 'unhipbot'))
        self.assertFalse(robot.allowed('/org/about.html', 'unhipbot'))
        self.assertFalse(robot.allowed('/org/plans.html', 'unhipbot'))
        self.assertFalse(robot.allowed('/%7Ejim/jim.html', 'unhipbot'))
        self.assertFalse(robot.allowed('/%7Emak/mak.html', 'unhipbot'))

        # The webcrawler agent
        self.assertTrue(robot.allowed('/', 'webcrawler'))
        self.assertTrue(robot.allowed('/index.html', 'webcrawler'))
        self.assertTrue(robot.allowed('/robots.txt', 'webcrawler'))
        self.assertTrue(robot.allowed('/server.html', 'webcrawler'))
        self.assertTrue(robot.allowed('/services/fast.html', 'webcrawler'))
        self.assertTrue(robot.allowed('/services/slow.html', 'webcrawler'))
        self.assertTrue(robot.allowed('/orgo.gif', 'webcrawler'))
        self.assertTrue(robot.allowed('/org/about.html', 'webcrawler'))
        self.assertTrue(robot.allowed('/org/plans.html', 'webcrawler'))
        self.assertTrue(robot.allowed('/%7Ejim/jim.html', 'webcrawler'))
        self.assertTrue(robot.allowed('/%7Emak/mak.html', 'webcrawler'))

        # The excite agent
        self.assertTrue(robot.allowed('/', 'excite'))
        self.assertTrue(robot.allowed('/index.html', 'excite'))
        self.assertTrue(robot.allowed('/robots.txt', 'excite'))
        self.assertTrue(robot.allowed('/server.html', 'excite'))
        self.assertTrue(robot.allowed('/services/fast.html', 'excite'))
        self.assertTrue(robot.allowed('/services/slow.html', 'excite'))
        self.assertTrue(robot.allowed('/orgo.gif', 'excite'))
        self.assertTrue(robot.allowed('/org/about.html', 'excite'))
        self.assertTrue(robot.allowed('/org/plans.html', 'excite'))
        self.assertTrue(robot.allowed('/%7Ejim/jim.html', 'excite'))
        self.assertTrue(robot.allowed('/%7Emak/mak.html', 'excite'))

        # All others
        self.assertFalse(robot.allowed('/', 'anything'))
        self.assertFalse(robot.allowed('/index.html', 'anything'))
        self.assertTrue(robot.allowed('/robots.txt', 'anything'))
        self.assertTrue(robot.allowed('/server.html', 'anything'))
        self.assertTrue(robot.allowed('/services/fast.html', 'anything'))
        self.assertTrue(robot.allowed('/services/slow.html', 'anything'))
        self.assertFalse(robot.allowed('/orgo.gif', 'anything'))
        self.assertTrue(robot.allowed('/org/about.html', 'anything'))
        self.assertFalse(robot.allowed('/org/plans.html', 'anything'))
        self.assertFalse(robot.allowed('/%7Ejim/jim.html', 'anything'))
        self.assertTrue(robot.allowed('/%7Emak/mak.html', 'anything'))

    def test_after_response_hook(self):
        '''Calls after_response_hook when response is received'''
        state = {"called": False}

        def hook(response):
            state["called"] = True
            self.assertEquals(response.status_code, 200)
        with requests_fixtures('test_after_response_hook'):
            robots.Robots.fetch(
                'http://example.com/robots.txt', after_response_hook=hook)
            self.assertTrue(state["called"])

    def test_after_response_hook_on_error(self):
        '''Calls after_response_hook when error occurs during fetch'''
        state = {"called": False}
        expected_url = 'http://localhost:8080/robots.txt'

        def hook(response):
            state["called"] = True
            self.assertIsInstance(
                response, robots.exceptions.ConnectionException)
            self.assertEquals(response.url, expected_url)
        with self.assertRaises(robots.exceptions.ConnectionException):
            robots.Robots.fetch(expected_url, after_response_hook=hook)
        self.assertTrue(state["called"])

    def test_after_parse_hook(self):
        '''Calls after_parse_hook after parsing robots.txt'''
        state = {"called": False}

        def hook(robots):
            state["called"] = True
            self.assertFalse(robots.allowed('/disallowed', 'me'))
        with requests_fixtures('test_after_parse_hook'):
            robots.Robots.fetch(
                'http://example.com/robots.txt', after_parse_hook=hook)
            self.assertTrue(state["called"])


class AllowNoneTest(unittest.TestCase):
    '''Tests about the AllowNone Robots class.'''

    def test_allow(self):
        '''Allows nothing.'''
        robot = robots.AllowNone('http://example.com/robots.txt')
        self.assertFalse(robot.allowed('/', 'agent'))

    def test_allow_robots_txt(self):
        '''Allows robots.txt.'''
        robot = robots.AllowNone('http://example.com/robots.txt')
        self.assertTrue(robot.allowed('/robots.txt', 'agent'))


class AllowAllTest(unittest.TestCase):
    '''Tests about the AllowAll Robots class.'''

    def test_allow(self):
        '''Allows nothing.'''
        robot = robots.AllowAll('http://example.com/robots.txt')
        self.assertTrue(robot.allowed('/', 'agent'))
