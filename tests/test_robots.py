#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

'''These are unit tests that are derived from the rfc at
http://www.robotstxt.org/norobots-rfc.txt'''

import codecs
import contextlib
import os
import unittest

import mock

skip_asis = False
try:
    import asis
except ImportError:
    print('Skipping asis tests')
    skip_asis = True

from reppy import robots


class RobotsTest(unittest.TestCase):
    '''Tests about our Robots class.'''

    @contextlib.contextmanager
    def server(self, *segments):
        '''Run an asis server with the provided path.'''
        path = os.path.join('tests', 'asis', *segments)
        with asis.Server(path, server='gevent', port=8080).greenlet():
            yield

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

    def test_disallow_first(self):
        '''Handles a missing User-Agent line.'''
        with self.assertRaises(ValueError):
            robot = robots.Robots.parse('http://example.com/robots.txt', '''
                Disallow: /path
            ''')

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
            User-agent: agent
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

    @unittest.skipIf(skip_asis, 'Asis not installed')
    def test_fetch_status_200(self):
        '''A 200 parses things normally.'''
        with self.server('test_fetch_status_200'):
            robot = robots.Robots.fetch('http://localhost:8080/robots.txt')
            self.assertFalse(robot.allowed('/path', 'agent'))

    @unittest.skipIf(skip_asis, 'Asis not installed')
    def test_fetch_status_401(self):
        '''A 401 gives us an AllowNone Robots.'''
        with self.server('test_fetch_status_401'):
            robot = robots.Robots.fetch('http://localhost:8080/robots.txt')
            self.assertIsInstance(robot, robots.AllowNone)

    @unittest.skipIf(skip_asis, 'Asis not installed')
    def test_fetch_status_403(self):
        '''A 403 gives us an AllowNone Robots.'''
        with self.server('test_fetch_status_403'):
            robot = robots.Robots.fetch('http://localhost:8080/robots.txt')
            self.assertIsInstance(robot, robots.AllowNone)

    @unittest.skipIf(skip_asis, 'Asis not installed')
    def test_fetch_status_4XX(self):
        '''A 4XX gives us an AllowAll Robots.'''
        with self.server('test_fetch_status_4XX'):
            robot = robots.Robots.fetch('http://localhost:8080/robots.txt')
            self.assertIsInstance(robot, robots.AllowAll)

    @unittest.skipIf(skip_asis, 'Asis not installed')
    def test_fetch_status_5XX(self):
        '''A server error raises an exception.'''
        with self.server('test_fetch_status_5XX'):
            with self.assertRaises(robots.exceptions.BadStatusCode):
                robots.Robots.fetch('http://localhost:8080/robots.txt')

    @unittest.skipIf(skip_asis, 'Asis not installed')
    def test_content_too_big(self):
        '''Raises an exception if the content is too big.'''
        with self.server('test_content_too_big'):
            with self.assertRaises(robots.exceptions.ReppyException):
                robots.Robots.fetch('http://localhost:8080/robots.txt', max_size=5)

    @unittest.skipIf(skip_asis, 'Asis not installed')
    def test_ssl_exception(self):
        '''Raises a ReppyException on SSL errors.'''
        with self.server('test_ssl_exception'):
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

    @unittest.skipIf(skip_asis, 'Asis not installed')
    def test_excessive_redirects(self):
        '''Raises a ReppyException on too many redirects.'''
        with self.server('test_excessive_redirects'):
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
