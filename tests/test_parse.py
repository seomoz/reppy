#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''These are unit tests that are derived from the rfc at
http://www.robotstxt.org/norobots-rfc.txt'''

import random
import unittest

import reppy
import logging
from reppy.parser import Rules
from reppy.exceptions import ReppyException, BadStatusCode
reppy.logger.setLevel(logging.FATAL)


class TestParse(unittest.TestCase):
    @staticmethod
    def parse(strng):
        '''Helper to parse a string as a Rules object'''
        return Rules('http://example.com/robots.txt', 200, strng, 0)

    def test_basic(self):
        '''Basic robots.txt parsing'''
        # Test beginning matching
        rules = self.parse('''
            User-agent: *
            Disallow: /tmp''')
        self.assertTrue(not rules.allowed('/tmp', 't'))
        self.assertTrue(not rules.allowed('/tmp.html', 't'))
        self.assertTrue(not rules.allowed('/tmp/a.html', 't'))

        rules = self.parse('''
            User-agent: *
            Disallow: /tmp/''')
        self.assertTrue(rules.allowed('/tmp', 't'))
        self.assertTrue(not rules.allowed('/tmp/', 't'))
        self.assertTrue(not rules.allowed('/tmp/a.html', 't'))
        # Make sure we can also provide a full url
        self.assertTrue(rules.allowed('http://example.com/tmp', 't'))
        self.assertTrue(not rules.allowed('http://example.com/tmp/', 't'))

    def test_unquoting(self):
        '''Ensures we correctly interpret url-escaped entities'''
        # Now test escaping entities
        rules = self.parse('''
            User-agent: *
            Disallow: /a%3cd.html''')
        self.assertTrue(not rules.allowed('/a%3cd.html', 't'))
        self.assertTrue(not rules.allowed('/a%3Cd.html', 't'))
        # And case indpendent
        rules = self.parse('''
            User-agent: *
            Disallow: /a%3Cd.html''')
        self.assertTrue(not rules.allowed('/a%3cd.html', 't'))
        self.assertTrue(not rules.allowed('/a%3Cd.html', 't'))
        # And escape the urls themselves
        rules = self.parse('''
            User-agent: *
            Disallow: /%7ejoe/index.html''')
        self.assertTrue(not rules.allowed('/~joe/index.html', 't'))
        self.assertTrue(not rules.allowed('/%7ejoe/index.html', 't'))

    def test_unquoting_forward_slash(self):
        '''Ensures escaped forward slashes are not matched with unescaped'''
        rules = self.parse('''
            User-agent: *
            Disallow: /a%2fb.html''')
        self.assertTrue(not rules.allowed('/a%2fb.html', 't'))
        self.assertTrue(rules.allowed('/a/b.html', 't'))
        rules = self.parse('''
            User-agent: *
            Disallow: /a/b.html''')
        self.assertTrue(rules.allowed('/a%2fb.html', 't'))
        self.assertTrue(not rules.allowed('/a/b.html', 't'))

    def test_rfc_example(self):
        '''Tests the example provided in the RFC'''
        rules = self.parse('''# /robots.txt for http://www.fict.org/
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
            Disallow: /''')
        # The unhip bot
        self.assertTrue(not rules.allowed('/', 'unhipbot'))
        self.assertTrue(not rules.allowed('/index.html', 'unhipbot'))
        self.assertTrue(rules.allowed('/robots.txt', 'unhipbot'))
        self.assertTrue(not rules.allowed('/server.html', 'unhipbot'))
        self.assertTrue(not rules.allowed('/services/fast.html', 'unhipbot'))
        self.assertTrue(not rules.allowed('/services/slow.html', 'unhipbot'))
        self.assertTrue(not rules.allowed('/orgo.gif', 'unhipbot'))
        self.assertTrue(not rules.allowed('/org/about.html', 'unhipbot'))
        self.assertTrue(not rules.allowed('/org/plans.html', 'unhipbot'))
        self.assertTrue(not rules.allowed('/%7Ejim/jim.html', 'unhipbot'))
        self.assertTrue(not rules.allowed('/%7Emak/mak.html', 'unhipbot'))
        # The webcrawler agent
        self.assertTrue(rules.allowed('/', 'webcrawler'))
        self.assertTrue(rules.allowed('/index.html', 'webcrawler'))
        self.assertTrue(rules.allowed('/robots.txt', 'webcrawler'))
        self.assertTrue(rules.allowed('/server.html', 'webcrawler'))
        self.assertTrue(rules.allowed('/services/fast.html', 'webcrawler'))
        self.assertTrue(rules.allowed('/services/slow.html', 'webcrawler'))
        self.assertTrue(rules.allowed('/orgo.gif', 'webcrawler'))
        self.assertTrue(rules.allowed('/org/about.html', 'webcrawler'))
        self.assertTrue(rules.allowed('/org/plans.html', 'webcrawler'))
        self.assertTrue(rules.allowed('/%7Ejim/jim.html', 'webcrawler'))
        self.assertTrue(rules.allowed('/%7Emak/mak.html', 'webcrawler'))
        # The excite agent
        self.assertTrue(rules.allowed('/', 'excite'))
        self.assertTrue(rules.allowed('/index.html', 'excite'))
        self.assertTrue(rules.allowed('/robots.txt', 'excite'))
        self.assertTrue(rules.allowed('/server.html', 'excite'))
        self.assertTrue(rules.allowed('/services/fast.html', 'excite'))
        self.assertTrue(rules.allowed('/services/slow.html', 'excite'))
        self.assertTrue(rules.allowed('/orgo.gif', 'excite'))
        self.assertTrue(rules.allowed('/org/about.html', 'excite'))
        self.assertTrue(rules.allowed('/org/plans.html', 'excite'))
        self.assertTrue(rules.allowed('/%7Ejim/jim.html', 'excite'))
        self.assertTrue(rules.allowed('/%7Emak/mak.html', 'excite'))
        # All others
        self.assertTrue(not rules.allowed('/', 'anything'))
        self.assertTrue(not rules.allowed('/index.html', 'anything'))
        self.assertTrue(rules.allowed('/robots.txt', 'anything'))
        self.assertTrue(rules.allowed('/server.html', 'anything'))
        self.assertTrue(rules.allowed('/services/fast.html', 'anything'))
        self.assertTrue(rules.allowed('/services/slow.html', 'anything'))
        self.assertTrue(not rules.allowed('/orgo.gif', 'anything'))
        self.assertTrue(rules.allowed('/org/about.html', 'anything'))
        self.assertTrue(not rules.allowed('/org/plans.html', 'anything'))
        self.assertTrue(not rules.allowed('/%7Ejim/jim.html', 'anything'))
        self.assertTrue(rules.allowed('/%7Emak/mak.html', 'anything'))

    def test_crawl_delay(self):
        '''Ensures we can parse crawl delays per agent'''
        rules = self.parse('''
            User-agent: agent
            Crawl-delay: 5
            User-agent: *
            Crawl-delay: 1''')
        self.assertEqual(rules.delay('agent'), 5)
        self.assertEqual(rules.delay('testing'), 1)

    def test_sitemaps(self):
        '''Ensures we can read all the sitemaps'''
        rules = self.parse('''
            User-agent: agent
            Sitemap: http://a.com/sitemap.xml
            Sitemap: http://b.com/sitemap.xml''')
        self.assertEqual(rules.sitemaps, [
            'http://a.com/sitemap.xml', 'http://b.com/sitemap.xml'])

    def test_batch_queries(self):
        '''Ensures batch queries run as expected'''
        rules = self.parse('''
            User-agent: *
            Disallow: /a
            Disallow: /b
            Allow: /b/''')
        test_urls = ['/a/hello', '/a/howdy', '/b', '/b/hello']
        allowed = ['/b/hello']
        self.assertEqual(rules.allowed(test_urls, 't'), allowed)

    def test_wildcard(self):
        '''Ensures wildcard matching works as expected'''
        rules = self.parse('''
            User-agent: *
            Disallow: /hello/*/are/you''')
        testUrls = ['/hello/', '/hello/how/are/you', '/hi/how/are/you/']
        allowed  = ['/hello/', '/hi/how/are/you/']
        self.assertEqual(rules.allowed(testUrls, 't'), allowed)

    def test_disallowed(self):
        '''Make sure disallowed is the opposite of allowed'''
        rules = self.parse('''
            User-agent: *
            Disallow: /0xa
            Disallow: /0xb
            Disallow: /0xc
            Disallow: /0xd
            Disallow: /0xe
            Disallow: /0xf''')
        for i in range(1000):
            path = hex(random.randint(0, 16))
            self.assertNotEqual(
                rules.allowed(path, 't'), rules.disallowed(path, 't'))

    def test_case_insensitivity(self):
        '''Make sure user agent matches are case insensitive'''
        rules = self.parse('''
            User-agent: agent
            Disallow: /a''')
        self.assertTrue(rules.disallowed('/a', 'Agent'))
        self.assertTrue(rules.disallowed('/a', 'aGent'))
        self.assertTrue(rules.disallowed('/a', 'AGeNt'))
        self.assertTrue(rules.disallowed('/a', 'AGENT'))

    def test_query(self):
        '''Make sure user agent matches are case insensitive'''
        rules = self.parse('''
            User-agent: agent
            Disallow: /a?howdy''')
        self.assertTrue(rules.allowed('/a', 'agent'))
        self.assertTrue(not rules.allowed('/a?howdy', 'agent'))
        self.assertTrue(not rules.allowed('/a?howdy#fragment', 'agent'))
        self.assertTrue(rules.allowed('/a?heyall', 'agent'))

    def test_allow_all(self):
        '''Ensures an empty disallow directive allows all'''
        rules = self.parse('''
            User-agent: *
            Disallow:  ''')
        agent = 'dotbot'
        self.assertTrue(rules.allowed('/', agent))
        self.assertTrue(rules.allowed('/foo', agent))
        self.assertTrue(rules.allowed('/foo.html', agent))
        self.assertTrue(rules.allowed('/foo/bar', agent))
        self.assertTrue(rules.allowed('/foo/bar.html', agent))

    def test_disallow_all(self):
        '''Ensures we can disallow all paths'''
        rules = self.parse('''
            User-agent: *
            Disallow: /''')
        agent = 'dotbot'
        self.assertTrue(not rules.allowed('/', agent))
        self.assertTrue(not rules.allowed('/foo', agent))
        self.assertTrue(not rules.allowed('/foo.html', agent))
        self.assertTrue(not rules.allowed('/foo/bar', agent))
        self.assertTrue(not rules.allowed('/foo/bar.html', agent))

    def test_allow_certain_pages_only(self):
        '''Tests explicit path allowances, even when they'd otherwise be
        disallowed'''
        rules = self.parse('''
            User-agent: *
            Allow: /onepage.html
            Allow: /oneotherpage.php
            Disallow: /
            Allow: /subfolder/page1.html
            Allow: /subfolder/page2.php
            Disallow: /subfolder/''')
        agent = 'dotbot'
        self.assertTrue(not rules.allowed('/', agent))
        self.assertTrue(not rules.allowed('/foo', agent))
        self.assertTrue(not rules.allowed('/bar.html', agent))
        self.assertTrue(rules.allowed('/onepage.html', agent))
        self.assertTrue(rules.allowed('/oneotherpage.php', agent))
        self.assertTrue(not rules.allowed('/subfolder', agent))
        self.assertTrue(not rules.allowed('/subfolder/', agent))
        self.assertTrue(not rules.allowed('/subfolder/aaaaa', agent))
        self.assertTrue(rules.allowed('/subfolder/page1.html', agent))
        self.assertTrue(rules.allowed('/subfolder/page2.php', agent))

    def test_empty(self):
        '''Makes sure we can part an empty robots.txt'''
        rules = self.parse('')
        self.assertTrue(rules.allowed('/', 't'))
        self.assertEqual(rules.delay('t'), None)
        self.assertEqual(rules.sitemaps, [])

    def test_relative(self):
        '''Basically, we should treat 'hello' like '/hello' '''
        rules = self.parse('''
            User-agent: *
            Disallow: hello
            Disallow: *goodbye''')
        agent = 'dotbot'
        self.assertTrue(not rules.allowed('/hello', agent))
        self.assertTrue(not rules.allowed('/hello/everyone', agent))

    def test_grouping_unknown_keys(self):
        '''When we encounter unknown keys, we should disregard any grouping
        that may have happened between user agent rules.'''
        # For example, in the wild, we encountered:
        #
        #   User-agent: *
        #   Disallow: /content/2/
        #   User-agent: *
        #   Noindex: /gb.html
        #   Noindex: /content/2/
        #   User-agent: ia_archiver
        #   Disallow: /
        #
        # Since 'Noindex' is an unknown directive, the rules for ia_archiver
        # were getting glommed into the rules for *, when that was
        # clearly not the intention.
        rules = self.parse('''
            User-agent: *
            Disallow: /content/2/
            User-agent: *
            Noindex: /gb.html
            Noindex: /content/2/
            User-agent: ia_archiver
            Disallow: /
        ''')
        self.assertTrue(rules.allowed('/foo', 'dotbot'))
        self.assertTrue(not rules.allowed('/bar', 'ia_archiver'))

    def test_utf8_bom(self):
        '''If there's a utf-8 BOM, we should parse it as such'''
        import codecs
        rules = self.parse(codecs.BOM_UTF8 + b'''User-agent: foo
            Allow: /foo

            User-agent: *
            Disallow: /foo
        ''')
        self.assertTrue(rules.allowed('/foo', 'foo'))
        self.assertTrue(not rules.allowed('/foo', 'other'))

    def test_utf16_bom(self):
        '''If there's a utf-16 BOM, we should parse it as such'''
        rules = self.parse(b'''User-agent: foo
            Allow: /foo

            User-agent: *
            Disallow: /foo
        '''.decode('utf-8').encode('utf-16'))
        self.assertTrue(rules.allowed('/foo', 'foo'))
        self.assertTrue(not rules.allowed('/foo', 'other'))

    def test_ascii(self):
         '''If we get bytes without encoding, we should parse it as such'''
         rules = self.parse(b'''User-agent: foo
             Allow: /foo

             User-agent: *
             Disallow: /foo
         ''')
         self.assertTrue(rules.allowed('/foo', 'foo'))
         self.assertTrue(not rules.allowed('/foo', 'other'))

    def test_skip_line(self):
        '''If there is no colon in a line, then we must skip it'''
        rules = self.parse('''User-agent: foo
            Allow: /foo
            Disallow /bar''')
        # This should not throw an exception, and it should not have a disallow
        self.assertTrue(rules.allowed('/bar', 'foo'))

    ###########################################################################
    # Status code issues
    ###########################################################################
    def test_status_forbidden(self):
        '''Make sure that when we get a forbidden status, that we believe
        we're not allowed to crawl a site'''
        rules = Rules('http://example.com/robots.txt', 401, '', 0)
        self.assertTrue(not rules.allowed('/foo', 't'))
        self.assertTrue(not rules.allowed('http://example.com/foo', 't'))

    def test_status_forbidden_allow(self):
        '''Test that if the flag is given, we allow all sites when robots.txt
        is forbidden'''
        rules = Rules('http://example.com/robots.txt', 401, '', 0, disallow_forbidden=False)
        self.assertTrue(rules.allowed('/foo', 't'))
        self.assertTrue(rules.allowed('http://example.com/foo', 't'))

    def test_status_allowed(self):
        '''If no robots.txt exists, we're given free range'''
        rules = Rules('http://example.com/robots.txt', 404, '', 0)
        self.assertTrue(rules.allowed('/foo', 't'))
        self.assertTrue(rules.allowed('http://example.com/foo', 't'))

    def test_server_error(self):
        '''Make sure that if there's a server error, it raises an exception'''
        self.assertRaises(BadStatusCode, Rules,
            'http://example.com/robots.txt', 500, '', 0)

    ###########################################################################
    # Here are some tests from other internal robots.txt parsers
    ###########################################################################
    def test_www_seomoz_org(self):
        rules = self.parse('''
            User-agent: *
            Disallow: /blogdetail.php?ID=537
            Disallow: /tracker

            Sitemap: http://www.seomoz.org/sitemap.xml.gz
            Sitemap: http://files.wistia.com/sitemaps/seomoz_video_sitemap.xml
            ''')
        agent = 'dotbot'
        self.assertTrue(rules.allowed('/blog', agent))
        self.assertTrue(not rules.allowed('/blogdetail.php?ID=537', agent))
        self.assertTrue(not rules.allowed('/tracker', agent))
        agent = 'DoTbOt'
        self.assertTrue(rules.allowed('/blog', agent))
        self.assertTrue(not rules.allowed('/blogdetail.php?ID=537', agent))
        self.assertTrue(not rules.allowed('/tracker', agent))

    def test_allow_all(self):
        # Now test escaping entities
        rules = self.parse('''
            User-agent: *
            Disallow:  ''')
        agent = 'dotbot'
        self.assertTrue(rules.allowed('/', agent))
        self.assertTrue(rules.allowed('/foo', agent))
        self.assertTrue(rules.allowed('/foo.html', agent))
        self.assertTrue(rules.allowed('/foo/bar', agent))
        self.assertTrue(rules.allowed('/foo/bar.html', agent))
        agent = 'oijsdofijsdofijsodifj'
        self.assertTrue(rules.allowed('/', agent))
        self.assertTrue(rules.allowed('/foo', agent))
        self.assertTrue(rules.allowed('/foo.html', agent))
        self.assertTrue(rules.allowed('/foo/bar', agent))
        self.assertTrue(rules.allowed('/foo/bar.html', agent))

    def test_disallow_all(self):
        # But not with foward slash
        rules = self.parse('''
            User-agent: *
            Disallow: /''')
        agent = 'dotbot'
        self.assertTrue(not rules.allowed('/', agent))
        self.assertTrue(not rules.allowed('/foo', agent))
        self.assertTrue(not rules.allowed('/foo.html', agent))
        self.assertTrue(not rules.allowed('/foo/bar', agent))
        self.assertTrue(not rules.allowed('/foo/bar.html', agent))
        agent = 'oijsdofijsdofijsodifj'
        self.assertTrue(not rules.allowed('/', agent))
        self.assertTrue(not rules.allowed('/foo', agent))
        self.assertTrue(not rules.allowed('/foo.html', agent))
        self.assertTrue(not rules.allowed('/foo/bar', agent))
        self.assertTrue(not rules.allowed('/foo/bar.html', agent))

    def test_no_googlebot_folder(self):
        rules = self.parse('''
            User-agent: Googlebot
            Disallow: /no-google/''')
        agent = 'googlebot'
        self.assertTrue(not rules.allowed('/no-google/', agent))
        self.assertTrue(not rules.allowed('/no-google/something', agent))
        self.assertTrue(not rules.allowed('/no-google/something.html', agent))
        self.assertTrue(rules.allowed('/', agent))
        self.assertTrue(rules.allowed('/somethingelse', agent))

    def test_no_googlebot_file(self):
        rules = self.parse('''
            User-agent: Googlebot
            Disallow: /no-google/blocked-page.html''')
        agent = 'googlebot'
        self.assertTrue(rules.allowed('/', agent))
        self.assertTrue(rules.allowed('/no-google/someotherfolder', agent))
        self.assertTrue(rules.allowed('/no-google/someotherfolder/somefile', agent))
        self.assertTrue(not rules.allowed('/no-google/blocked-page.html', agent))

    def test_rogerbot_only(self):
        rules = self.parse('''
            User-agent: *
            Disallow: /no-bots/block-all-bots-except-rogerbot-page.html

            User-agent: rogerbot
            Allow: /no-bots/block-all-bots-except-rogerbot-page.html''')
        agent = 'notroger'
        self.assertTrue(not rules.allowed('/no-bots/block-all-bots-except-rogerbot-page.html', agent))
        self.assertTrue(rules.allowed('/', agent))
        agent = 'rogerbot'
        self.assertTrue(rules.allowed('/no-bots/block-all-bots-except-rogerbot-page.html', agent))
        self.assertTrue(rules.allowed('/', agent))

    def test_allow_certain_pages_only(self):
        rules = self.parse('''
            User-agent: *
            Allow: /onepage.html
            Allow: /oneotherpage.php
            Disallow: /
            Allow: /subfolder/page1.html
            Allow: /subfolder/page2.php
            Disallow: /subfolder/''')
        agent = 'dotbot'
        self.assertTrue(not rules.allowed('/', agent))
        self.assertTrue(not rules.allowed('/foo', agent))
        self.assertTrue(not rules.allowed('/bar.html', agent))
        self.assertTrue(rules.allowed('/onepage.html', agent))
        self.assertTrue(rules.allowed('/oneotherpage.php', agent))
        self.assertTrue(not rules.allowed('/subfolder', agent))
        self.assertTrue(not rules.allowed('/subfolder/', agent))
        self.assertTrue(not rules.allowed('/subfolder/aaaaa', agent))
        self.assertTrue(rules.allowed('/subfolder/page1.html', agent))
        self.assertTrue(rules.allowed('/subfolder/page2.php', agent))

    def test_no_gifs_or_jpgs(self):
        rules = self.parse('''
            User-agent: *
            Disallow: /*.gif$
            Disallow: /*.jpg$''')
        agent = 'dotbot'
        self.assertTrue(rules.allowed('/', agent))
        self.assertTrue(rules.allowed('/foo', agent))
        self.assertTrue(rules.allowed('/foo.html', agent))
        self.assertTrue(rules.allowed('/foo/bar', agent))
        self.assertTrue(rules.allowed('/foo/bar.html', agent))
        self.assertTrue(not rules.allowed('/test.jpg', agent))
        self.assertTrue(not rules.allowed('/foo/test.jpg', agent))
        self.assertTrue(not rules.allowed('/foo/bar/test.jpg', agent))
        self.assertTrue(rules.allowed('/the-jpg-extension-is-awesome.html', agent))
        self.assertTrue(not rules.allowed('/jpg.jpg', agent))
        self.assertTrue(not rules.allowed('/foojpg.jpg', agent))
        self.assertTrue(not rules.allowed('/bar/foojpg.jpg', agent))
        self.assertTrue(not rules.allowed('/.jpg.jpg', agent))
        self.assertTrue(not rules.allowed('/.jpg/.jpg', agent))
        self.assertTrue(not rules.allowed('/test.gif', agent))
        self.assertTrue(not rules.allowed('/foo/test.gif', agent))
        self.assertTrue(not rules.allowed('/foo/bar/test.gif', agent))
        self.assertTrue(rules.allowed('/the-gif-extension-is-awesome.html', agent))

    def test_block_subdirectory_wildcard(self):
        rules = self.parse('''
            User-agent: *
            Disallow: /private*/''')
        agent = 'dotbot'
        self.assertTrue(rules.allowed('/', agent))
        self.assertTrue(rules.allowed('/foo', agent))
        self.assertTrue(rules.allowed('/foo.html', agent))
        self.assertTrue(rules.allowed('/foo/bar', agent))
        self.assertTrue(rules.allowed('/foo/bar.html', agent))
        self.assertTrue(rules.allowed('/private', agent))
        self.assertTrue(rules.allowed('/privates', agent))
        self.assertTrue(rules.allowed('/privatedir', agent))
        self.assertTrue(not rules.allowed('/private/', agent))
        self.assertTrue(not rules.allowed('/private/foo', agent))
        self.assertTrue(not rules.allowed('/private/foo/bar.html', agent))
        self.assertTrue(not rules.allowed('/privates/', agent))
        self.assertTrue(not rules.allowed('/privates/foo', agent))
        self.assertTrue(not rules.allowed('/privates/foo/bar.html', agent))
        self.assertTrue(not rules.allowed('/privatedir/', agent))
        self.assertTrue(not rules.allowed('/privatedir/foo', agent))
        self.assertTrue(not rules.allowed('/privatedir/foo/bar.html', agent))

    def test_block_urls_with_question_marks(self):
        rules = self.parse('''
            User-agent: *
            Disallow: /*?''')
        agent = 'dotbot'
        self.assertTrue(rules.allowed('/', agent))
        self.assertTrue(rules.allowed('/foo', agent))
        self.assertTrue(rules.allowed('/foo.html', agent))
        self.assertTrue(rules.allowed('/foo/bar', agent))
        self.assertTrue(rules.allowed('/foo/bar.html', agent))
        self.assertTrue(not rules.allowed('/?', agent))
        self.assertTrue(not rules.allowed('/foo?q=param', agent))
        self.assertTrue(not rules.allowed('/foo.html?q=param', agent))
        self.assertTrue(not rules.allowed('/foo/bar?q=param', agent))
        self.assertTrue(not rules.allowed('/foo/bar.html?q=param&bar=baz', agent))

    def test_no_question_except_at_end(self):
        rules = self.parse('''
            User-agent: *
            Allow: /*?$
            Disallow: /*?''')
        agent = 'dotbot'
        self.assertTrue(rules.allowed('/', agent))
        self.assertTrue(rules.allowed('/foo', agent))
        self.assertTrue(rules.allowed('/foo.html', agent))
        self.assertTrue(rules.allowed('/foo/bar', agent))
        self.assertTrue(rules.allowed('/foo/bar.html', agent))
        self.assertTrue(rules.allowed('/?', agent))
        self.assertTrue(rules.allowed('/foo/bar.html?', agent))
        self.assertTrue(not rules.allowed('/foo?q=param', agent))
        self.assertTrue(not rules.allowed('/foo.html?q=param', agent))
        self.assertTrue(not rules.allowed('/foo/bar?q=param', agent))
        self.assertTrue(not rules.allowed('/foo/bar.html?q=param&bar=baz', agent))

    def test_wildcard_edge_cases(self):
        rules = self.parse('''
            User-agent: *
            Disallow: /*one
            Disallow: /two*three
            Disallow: /irrelevant/four*five
            Disallow: /six*
            Disallow: /foo/*/seven*/eight*nine
            Disallow: /foo/*/*ten$

            Disallow: /*products/default.aspx
            Disallow: /*/feed/$''')
        agent = 'dotbot'
        self.assertTrue(rules.allowed('/', agent))
        self.assertTrue(rules.allowed('/foo', agent))
        self.assertTrue(rules.allowed('/foo.html', agent))
        self.assertTrue(rules.allowed('/foo/bar', agent))
        self.assertTrue(rules.allowed('/foo/bar.html', agent))
        self.assertTrue(not rules.allowed('/one', agent))
        self.assertTrue(not rules.allowed('/aaaone', agent))
        self.assertTrue(not rules.allowed('/aaaaoneaaa', agent))
        self.assertTrue(not rules.allowed('/oneaaaa', agent))
        self.assertTrue(not rules.allowed('/twothree', agent))
        self.assertTrue(not rules.allowed('/twoaaathree', agent))
        self.assertTrue(not rules.allowed('/twoaaaathreeaaa', agent))
        self.assertTrue(not rules.allowed('/twothreeaaa', agent))
        self.assertTrue(not rules.allowed('/irrelevant/fourfive', agent))
        self.assertTrue(not rules.allowed('/irrelevant/fouraaaafive', agent))
        self.assertTrue(not rules.allowed('/irrelevant/fouraaafiveaaaa', agent))
        self.assertTrue(not rules.allowed('/irrelevant/fourfiveaaa', agent))
        self.assertTrue(not rules.allowed('/six', agent))
        self.assertTrue(not rules.allowed('/sixaaaa', agent))
        self.assertTrue(not rules.allowed('/foo/aaa/seven/eightnine', agent))
        self.assertTrue(not rules.allowed('/foo/aaa/seventeen/eightteennineteen', agent))
        self.assertTrue(not rules.allowed('/foo/aaa/ten', agent))
        self.assertTrue(not rules.allowed('/foo/bbb/often', agent))
        self.assertTrue(rules.allowed('/foo/aaa/tenaciousd', agent))
        self.assertTrue(not rules.allowed('/products/default.aspx', agent))
        self.assertTrue(not rules.allowed('/author/admin/feed/', agent))

    def test_many_wildcards(self):
        rules = self.parse('''
            User-agent: *
            Allow: /***************************************.css''')
        agent = 'dotbot'
        self.assertTrue(rules.allowed('/blog/a-really-long-url-string-that-takes-a-very-long-time-to-process-without-combining-many-asterisks', agent))

    def test_allow_edge_cases(self):
        rules = self.parse('''
            User-agent: *
            Disallow:   /somereallylongfolder/
            Allow:      /*.jpg

            Disallow:   /sales-secrets.php
            Allow:      /sales-secrets.php

            Disallow:   /folder
            Allow:      /folder/

            Allow:      /folder2
            Disallow:   /folder2/''')
        agent = 'dotbot'
        self.assertTrue(not rules.allowed('/somereallylongfolder/', agent))
        self.assertTrue(not rules.allowed('/somereallylongfolder/aaaa', agent))
        self.assertTrue(not rules.allowed('/somereallylongfolder/test.jpg', agent))
        self.assertTrue(rules.allowed('/sales-secrets.php', agent))
        self.assertTrue(rules.allowed('/folder/page', agent))
        self.assertTrue(rules.allowed('/folder/page2', agent))

    def test_redundant_allow(self):
        rules = self.parse('''
            User-agent: *
            Disallow: /en/
            Disallow: /files/documentation/
            Disallow: /files/
            Disallow: /de/careers/
            Disallow: /images/

            Disallow: /print_mode.yes/
            Disallow: /?product=lutensit&print_mode=yes&googlebot=nocrawl
            Allow: /
            Disallow: /search/''')
        agent = 'dotbot'
        self.assertTrue(not rules.allowed('/print_mode.yes/', agent))
        self.assertTrue(not rules.allowed('/print_mode.yes/foo', agent))
        self.assertTrue(not rules.allowed('/search/', agent))
        self.assertTrue(not rules.allowed('/search/foo', agent))

    def test_legacy(self):
        rules = self.parse('''
            user-agent: *  #a comment!
            disallow: /Blerf
            disallow: /Blerg$
            disallow: /blerf/*/print.html$#a comment
            disallow: /blerf/*/blim/blerf$
            disallow: /plerf/*/blim/blim$
                user-agent: BLERF
                DisALLOW:   blerfPage
            blerf:blah''')
        agent = 'dotbot'
        self.assertTrue(not rules.allowed('/Blerf/blah', agent))
        self.assertTrue(rules.allowed('/Blerg/blah', agent))
        self.assertTrue(rules.allowed('/blerf/blah', agent))
        self.assertTrue(not rules.allowed('/Blerg', agent))
        self.assertTrue(not rules.allowed(
            '/blerf/some/subdirs/print.html', agent))
        self.assertTrue(rules.allowed(
            '/blerf/some/subdirs/print.html?extra=stuff', agent))
        self.assertTrue(not rules.allowed(
            '/blerf/some/sub/dirs/blim/blim/blerf', agent))
        self.assertTrue(not rules.allowed(
            '/plerf/some/sub/dirs/blim/blim', agent))
        rules = self.parse('''
            User-agent: *
            Allow: /searchhistory/
            Disallow: /news?output=xhtml&
            Allow: /news?output=xhtml
            Disallow: /search
            Disallow: /groups
            Disallow: /images
            Disallow: /catalogs
            Disallow: /catalogues
            Disallow: /news
            Disallow: /nwshp
            Allow: /news?btcid=
            Disallow: /news?btcid=*&
            Allow: /news?btaid=
            Disallow: /news?btaid=*&
            Disallow: /?
            Disallow: /addurl/image?
            Disallow: /pagead/
            Disallow: /relpage/
            Disallow: /relcontent
            Disallow: /sorry/
            Disallow: /imgres
            Disallow: /keyword/
            Disallow: /u/
            Disallow: /univ/
            Disallow: /cobrand
            Disallow: /custom
            Disallow: /advanced_group_search
            Disallow: /advanced_search
            Disallow: /googlesite
            Disallow: /preferences
            Disallow: /setprefs
            Disallow: /swr
            Disallow: /url
            Disallow: /default
            Disallow: /m?
            Disallow: /m/?
            Disallow: /m/lcb
            Disallow: /m/search?
            Disallow: /wml?
            Disallow: /wml/?
            Disallow: /wml/search?
            Disallow: /xhtml?
            Disallow: /xhtml/?
            Disallow: /xhtml/search?
            Disallow: /xml?
            Disallow: /imode?
            Disallow: /imode/?
            Disallow: /imode/search?
            Disallow: /jsky?
            Disallow: /jsky/?
            Disallow: /jsky/search?
            Disallow: /pda?
            Disallow: /pda/?
            Disallow: /pda/search?
            Disallow: /sprint_xhtml
            Disallow: /sprint_wml
            Disallow: /pqa
            Disallow: /palm
            Disallow: /gwt/
            Disallow: /purchases
            Disallow: /hws
            Disallow: /bsd?
            Disallow: /linux?
            Disallow: /mac?
            Disallow: /microsoft?
            Disallow: /unclesam?
            Disallow: /answers/search?q=
            Disallow: /local?
            Disallow: /local_url
            Disallow: /froogle?
            Disallow: /products?
            Disallow: /froogle_
            Disallow: /product_
            Disallow: /products_
            Disallow: /print
            Disallow: /books
            Disallow: /patents?
            Disallow: /scholar?
            Disallow: /complete
            Disallow: /sponsoredlinks
            Disallow: /videosearch?
            Disallow: /videopreview?
            Disallow: /videoprograminfo?
            Disallow: /maps?
            Disallow: /mapstt?
            Disallow: /mapslt?
            Disallow: /maps/stk/
            Disallow: /mapabcpoi?
            Disallow: /translate?
            Disallow: /ie?
            Disallow: /sms/demo?
            Disallow: /katrina?
            Disallow: /blogsearch?
            Disallow: /blogsearch/
            Disallow: /blogsearch_feeds
            Disallow: /advanced_blog_search
            Disallow: /reader/
            Disallow: /uds/
            Disallow: /chart?
            Disallow: /transit?
            Disallow: /mbd?
            Disallow: /extern_js/
            Disallow: /calendar/feeds/
            Disallow: /calendar/ical/
            Disallow: /cl2/feeds/
            Disallow: /cl2/ical/
            Disallow: /coop/directory
            Disallow: /coop/manage
            Disallow: /trends?
            Disallow: /trends/music?
            Disallow: /notebook/search?
            Disallow: /music
            Disallow: /browsersync
            Disallow: /call
            Disallow: /archivesearch?
            Disallow: /archivesearch/url
            Disallow: /archivesearch/advanced_search
            Disallow: /base/search?
            Disallow: /base/reportbadoffer
            Disallow: /base/s2
            Disallow: /urchin_test/
            Disallow: /movies?
            Disallow: /codesearch?
            Disallow: /codesearch/feeds/search?
            Disallow: /wapsearch?
            Disallow: /safebrowsing
            Disallow: /reviews/search?
            Disallow: /orkut/albums
            Disallow: /jsapi
            Disallow: /views?
            Disallow: /c/
            Disallow: /cbk
            Disallow: /recharge/dashboard/car
            Disallow: /recharge/dashboard/static/
            Disallow: /translate_c?
            Disallow: /s2/profiles/me
            Allow: /s2/profiles
            Disallow: /s2
            Disallow: /transconsole/portal/
            Disallow: /gcc/
            Disallow: /aclk
            Disallow: /cse?
            Disallow: /tbproxy/
            Disallow: /MerchantSearchBeta/
            Disallow: /ime/
            Disallow: /websites?
            Disallow: /shenghuo/search?''')
        self.assertTrue(not rules.allowed('/?as_q=ethics&ie=UTF-8&ui=blg&bl_url=centrerion.blogspot.com&x=0&y=0&ui=blg', agent))
        self.assertTrue(not rules.allowed('/archivesearch?q=stalin&scoring=t&hl=en&sa=N&sugg=d&as_ldate=1900&as_hdate=1919&lnav=hist2', agent))
        rules = self.parse('''
            User-agent: scooter
            Disallow: /

            User-agent: wget
            User-agent: webzip
            Disallow: /

            User-agent: *
            Disallow:''')
        self.assertTrue(rules.allowed('/index.html', agent))

        rules = self.parse('''
            # Alexa
            User-agent: ia_archiver
            Disallow: /utils/date_picker/
            # Ask Jeeves
            User-agent: Teoma
            Disallow: /utils/date_picker/
            # Google
            User-agent: googlebot
            Disallow: /utils/date_picker/
            # MSN
            User-agent: MSNBot
            Disallow: /utils/date_picker/
            # Yahoo!
            User-agent: Slurp
            Disallow: /utils/date_picker/
            # Baidu
            User-agent: baiduspider
            Disallow: /utils/date_picker/
            # All the rest go away
            User-agent: *
            Disallow: /''')
        self.assertTrue(not rules.allowed('/', agent))

        rules = self.parse('''
            User-agent: dotbot
            User-agent:snowball
            Disallow:/''')
        self.assertTrue(not rules.allowed('/', agent))

        rules = self.parse('''
            User-agent: Googlebot-Image
            Disallow: /
            User-agent: *
            Crawl-delay: 7
            Disallow: /faq.php
            Disallow: /groupcp.php
            Disallow: /login.php
            Disallow: /memberlist.php
            Disallow: /merge.php
            Disallow: /modcp.php
            Disallow: /posting.php
            Disallow: /phpBB2/posting.php
            Disallow: /privmsg.php
            Disallow: /profile.php
            Disallow: /search.php
            Disallow: /phpBB2/faq.php
            Disallow: /phpBB2/groupcp.php
            Disallow: /phpBB2/login.php
            Disallow: /phpBB2/memberlist.php
            Disallow: /phpBB2/merge.php
            Disallow: /phpBB2/modcp.php
            Disallow: /phpBB2/posting.php
            Disallow: /phpBB2/posting.php
            Disallow: /phpBB2/privmsg.php
            Disallow: /phpBB2/profile.php
            Disallow: /phpBB2/search.php
            Disallow: /admin/
            Disallow: /images/
            Disallow: /includes/
            Disallow: /install/
            Disallow: /modcp/
            Disallow: /templates/
            Disallow: /phpBB2/admin/
            Disallow: /phpBB2/images/
            Disallow: /phpBB2/includes/
            Disallow: /phpBB2/install/
            Disallow: /phpBB2/modcp/
            Disallow: /phpBB2/templates/
            Disallow: /trac/''')
        self.assertTrue(not rules.allowed(
            '/phpBB2/posting.php?mode=reply&t=895', agent))

        rules = self.parse('''
            User-agent: *
            Disallow: /Product/List
            Disallow: /Product/Search
            Disallow: /Product/TopSellers
            Disallow: /Product/UploadImage
            Disallow: /WheelPit
            Disallow: /iwwida.pvx''')
        self.assertTrue(not rules.allowed('/WheelPit', agent))

    def test_trailing_question(self):
        '''Make sure a trailing question mark doesn't muss anything up'''
        rules = self.parse('''
            User-agent: *
            Disallow: /search
            Disallow: /sdch
            Disallow: /groups
            Disallow: /images
            Disallow: /catalogs
            Allow: /catalogs/about
            Allow: /catalogs/p?''')
        agent = 'dotbot'
        base_url = 'http://example.com'
        self.assertTrue(not rules.allowed('/catalogs/foo', agent))
        self.assertTrue(not rules.allowed('/catalogs/p', agent))
        self.assertTrue(rules.allowed('/catalogs/p?', agent))
        # Make sure it works for full urls as well
        self.assertTrue(not rules.allowed(base_url + '/catalogs/foo', agent))
        self.assertTrue(not rules.allowed(base_url + '/catalogs/p', agent))
        self.assertTrue(rules.allowed(base_url + '/catalogs/p?', agent))

    def test_disallow_all_url(self):
        '''Make sure base url without trailing slash is disallowed
        in case Disallow: / rule is used.'''
        base_url = 'http://example.com'
        rules = self.parse('''
            User-agent: *
            Disallow: /''')
        agent = 'dotbot'
        # all urls should be blocked according to
        #   http://www.robotstxt.org/orig.html#code
        self.assertTrue(not rules.allowed(base_url, agent))
        self.assertTrue(not rules.allowed(base_url + '/', agent))
        self.assertTrue(not rules.allowed(base_url + '/foo.html', agent))

    def test_extract_path(self):
        '''Make sure we can correctly extract example paths'''
        from reppy.parser import Agent
        self.assertEqual('/', Agent.extract_path(''))
        self.assertEqual('/', Agent.extract_path('http://example.com'))
        self.assertEqual('/foo', Agent.extract_path('/foo'))
        self.assertEqual('/foo', Agent.extract_path('http://example.com/foo'))
        self.assertEqual('/foo/', Agent.extract_path('/foo/'))
        self.assertEqual('/foo/',
            Agent.extract_path('http://example.com/foo/'))
        self.assertEqual('/foo/bar', Agent.extract_path('/foo/bar'))
        self.assertEqual('/foo/bar',
            Agent.extract_path('http://example.com/foo/bar'))
        self.assertEqual('/foo/bar?a=b', Agent.extract_path('/foo/bar?a=b'))
        self.assertEqual('/foo/bar?a=b',
            Agent.extract_path('http://example.com/foo/bar?a=b'))

    def test_malformed_crawl_delay(self):
        '''Ignore crawl delays that are too malformed to parse.'''
        rules = self.parse('''
            User-agent: *
            Crawl-delay: 
            ''')
        self.assertEqual(rules.delay('rogerbot'), None)

if __name__ == '__main__':
    unittest.main()
