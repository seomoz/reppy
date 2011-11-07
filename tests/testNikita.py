#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

sys.path.append(os.path.abspath('..'))

import reppy
import random
import unittest

import logging
reppy.logger.setLevel(logging.FATAL)

class TestReppyNikita(unittest.TestCase):
	def test_classic(self):
		r = reppy.parse('''# robots.txt for http://www.example.com/
			User-agent: *
			Disallow:    /
			User-agent: foobot
			Disallow:''')
		self.assertTrue(    r.allowed('/', 'foobot'))
		self.assertTrue(    r.allowed('/bar.html', 'Foobot'))
		self.assertTrue(    r.allowed('/', 'SomeOtherBot'))
		self.assertTrue(    r.allowed('/blahblahblah', 'SomeOtherBot'))
	
	def test_mk1994(self):
		r = reppy.parse('''# robots.txt for http://www.example.com/
			User-agent: *
			Disallow: /cyberworld/map/ # This is an infinite virtual URL space
			Disallow: /tmp/ # these will soon disappear
			Disallow: /foo.html
		''')
		self.assertTrue(    r.allowed('/', 'CrunchyFrogBot'))
		self.assertTrue(not r.allowed('/foo.html', 'CrunchyFrogBot'))
		self.assertTrue(    r.allowed('/foo.html', 'CrunchyFrogBot'))
		self.assertTrue(    r.allowed('/foo.shtml', 'CrunchyFrogBot'))
		self.assertTrue(not r.allowed('/foo.htmlx', 'CrunchyFrogBot'))
		self.assertTrue(    r.allowed('/cyberworld/index.html', 'CrunchyFrogBot'))
		self.assertTrue(not r.allowed('/tmp/foo.html', 'CrunchyFrogBot'))
		self.assertTrue(not r.allowed('http://example.com/foo.html', 'CrunchyFrogBot'))
		self.assertTrue(not r.allowed('http://example.org/foo.html', 'CrunchyFrogBot'))
		self.assertTrue(not r.allowed('https://example.org/foo.html', 'CrunchyFrogBot'))
		self.assertTrue(not r.allowed('ftp://example.net/foo.html', 'CrunchyFrogBot'))
	
	def test_blank(self):
		r = reppy.parse('''''')
		self.assertTrue(    r.allowed('/', 'foobot'))
		self.assertTrue(    r.allowed('/foo.html', 'anybot'))
		self.assertTrue(    r.allowed('/TheGoldenAgeOfBallooning/', 'anybot'))
		self.assertTrue(    r.allowed('/TheGoldenAgeOfBallooning/claret/html', 'anybot'))

	def test_bom(self):
		utf8_byte_order_mark = chr(0xef) + chr(0xbb) + chr(0xbf)
		r = reppy.parse('''%sUSERAGENT: FOOBOT
		%suser-agent:%s%s%sbarbot%s
		disallow: /foo/
		''' % (utf8_byte_order_mark, '\t', '\t', '\t', '\t', chr(0xb)))
		self.assertTrue(    r.allowed('/', 'foobot'))
		self.assertTrue(not r.allowed('/foo/bar.html', 'foobot'))
		self.assertTrue(    r.allowed('/foo/bar.html', 'AnotherBot'))
		self.assertTrue(not r.allowed('/foo/bar.html', 'Foobot Version 1.0'))
		self.assertTrue(not r.allowed('/foo/bar.html', 'Mozilla/5.0 (compatible; Foobot/2.1)'))
		self.assertTrue(not r.allowed('/foo/bar.html', 'barbot'))
		self.assertTrue(    r.allowed('/tmp/', 'barbot'))
	
	def test_utf8(self):
		s = '''# robots.txt for http://www.example.com/
			UserAgent: Jävla-Foobot
			Disallow: /

			UserAgent: \u041b\u044c\u0432\u0456\u0432-bot
			Disallow: /totalitarianism/
			'''.decode('utf-8')
		r = reppy.parse(s)
		ua = 'jävla-fanbot'
		self.assertTrue(    r.allowed('/foo/bar.html', ua))
		self.assertTrue(not r.allowed('/foo/bar.html', ua.replace('fan', 'foo')))
		self.assertTrue(    r.allowed('/', 'foobot'))
		self.assertTrue(    r.allowed('/', 'Mozilla/5.0 (compatible; \u041b\u044c\u0432\u0456\u0432-bot/1.1)'))
		self.assertTrue(not r.allowed('/totalitarianism/foo.html', 'Mozilla/5.0 (compatible; \u041b\u044c\u0432\u0456\u0432-bot/1.1)'))
	
	def test_implicit(self):
		r = reppy.parse('''# robots.txt for http://www.example.com/
			User-agent: *
			Disallow:    /
			User-agent: foobot
			Disallow:''')
		self.assertTrue(    r.allowed('/', 'foobot'))
		self.assertTrue(    r.allowed('/bar.html', 'foobot'))
		self.assertTrue(not r.allowed('/', 'SomeOtherBot'))
		self.assertTrue(not r.allowed('/blahblahblah', 'SomeOtherBot'))
	
	def test_wildcards(self):
		r = reppy.parse('''# robots.txt for http://www.example.com/
			User-agent: Rule1TestBot
			Disallow:  /foo*
			User-agent: Rule2TestBot
			Disallow:  /foo*/bar.html
			# Disallows anything containing the letter m!
			User-agent: Rule3TestBot
			Disallow:  *m
			User-agent: Rule4TestBot
			Allow:  /foo/bar.html
			Disallow: *
			User-agent: Rule5TestBot
			Disallow:  /foo*/*bar.html
			User-agent: Rule6TestBot
			Allow:  /foo$
			Disallow:  /foo''')
		self.assertTrue(    r.allowed('/fo.html', 'Rule1TestBot'))
		self.assertTrue(not r.allowed('/foo.html', 'Rule1TestBot'))
		self.assertTrue(not r.allowed('/food', 'Rule1TestBot'))
		self.assertTrue(not r.allowed('/foo/bar.html', 'Rule1TestBot'))
		
		self.assertTrue(    r.allowed('/fo.html', 'Rule2TestBot'))
		self.assertTrue(not r.allowed('/foo/bar.html', 'Rule2TestBot'))
		self.assertTrue(not r.allowed('/food/bar.html', 'Rule2TestBot'))
		self.assertTrue(not r.allowed('/foo/a/b/c/x/y/z/bar.html', 'Rule2TestBot'))
		self.assertTrue(    r.allowed('/food/xyz.html', 'Rule2TestBot'))
		
		self.assertTrue(not r.allowed('/foo.htm', 'Rule3TestBot'))
		self.assertTrue(not r.allowed('/foo.html', 'Rule3TestBot'))
		self.assertTrue(    r.allowed('/foo', 'Rule3TestBot'))
		self.assertTrue(not r.allowed('/foom', 'Rule3TestBot'))
		self.assertTrue(not r.allowed('/moo', 'Rule3TestBot'))
		self.assertTrue(not r.allowed('/foo/bar.html', 'Rule3TestBot'))
		self.assertTrue(    r.allowed('/foo/bar.txt', 'Rule3TestBot'))

		self.assertTrue(not r.allowed('/fo.html', 'Rule4TestBot'))
		self.assertTrue(not r.allowed('/foo.html', 'Rule4TestBot')) 
		self.assertTrue(not r.allowed('/foo', 'Rule4TestBot'))
		self.assertTrue(    r.allowed('/foo/bar.html', 'Rule4TestBot'))
		self.assertTrue(not r.allowed('/foo/bar.txt', 'Rule4TestBot'))

		self.assertTrue(not r.allowed('/foo/bar.html', 'Rule5TestBot'))
		self.assertTrue(not r.allowed('/food/rebar.html', 'Rule5TestBot'))
		self.assertTrue(    r.allowed('/food/rebarf.html', 'Rule5TestBot'))
		self.assertTrue(not r.allowed('/foo/a/b/c/rebar.html', 'Rule5TestBot'))
		self.assertTrue(not r.allowed('/foo/a/b/c/bar.html', 'Rule5TestBot'))

		self.assertTrue(    r.allowed('/foo', 'Rule6TestBot'))
		self.assertTrue(not r.allowed('/foo/', 'Rule6TestBot'))
		self.assertTrue(not r.allowed('/foo/bar.html', 'Rule6TestBot'))
		self.assertTrue(not r.allowed('/fooey', 'Rule6TestBot'))

	def test_crawl_delays(self):
		r = reppy.parse('''# robots.txt for http://www.example.com/
			User-agent: Foobot
			Disallow:  *
			Crawl-Delay: 5
			User-agent: Somebot
			Allow: /foo.html
			Crawl-Delay: .3
			Allow: /bar.html
			Disallow: *
			User-agent: AnotherBot
			Disallow:  *
			Sitemap: http://www.example.com/sitemap.xml
			User-agent: CamelBot
			Disallow: /foo.html
			Crawl-Delay: go away!''')
		self.assertTrue(not r.allowed('/foo.html', 'Foobot'))
		self.assertTrue(    r.allowed('/foo.html', 'Somebot'))
		self.assertTrue(    r.allowed('/bar.html', 'Somebot'))
		self.assertTrue(not r.allowed('/x.html', 'Somebot'))
		self.assertTrue(not r.allowed('/foo.html', 'AnotherBot'))
		
		self.assertEqual(r.crawlDelay('Foobot'), 5)
		self.assertEqual(r.crawlDelay('Blahbot'), None)
		self.assertEqual(r.crawlDelay('Somebot'), 0.3)
		self.assertEqual(r.sitemaps, ['http://www.example.com/sitemap.xml'])
		self.assertEqual(r.crawlDelay('CamelBot'), None)

	def test_bad_syntax(self):
		r = reppy.parse('''# robots.txt for http://www.example.com/
			# This is nonsense; UA most come first.
			Disallow: /
			User-agent: *

			# With apologies to Dr. Seuss, this syntax won't act as the author expects. 
			# It will only match UA strings that contain "onebot twobot greenbot bluebot".
			# To match multiple UAs to a single rule, use multiple "User-agent:" lines.
			User-agent: onebot twobot greenbot bluebot
			Disallow: /

			# Blank lines indicate an end-of-record so the first UA listed here is ignored.
			User-agent: OneTwoFiveThreeSirBot

			# Note from Webmaster: add new user-agents below:
			User-agent: WotBehindTheRabbitBot
			User-agent: ItIsTheRabbitBot
			Disallow: /HolyHandGrenade/''')
		self.assertTrue(    r.allowed('/', 'onebot'))
		self.assertTrue(    r.allowed('/foo/bar.html', 'onebot'))
		self.assertTrue(    r.allowed('/', 'bluebot'))
		self.assertTrue(    r.allowed('/foo/bar.html', 'bluebot'))
		self.assertTrue(    r.allowed('/HolyHandGrenade/Antioch.html', 'OneTwoFiveThreeSirBot'))
		self.assertTrue(not r.allowed('/HolyHandGrenade/Antioch.html', 'WotBehindTheRabbitBot'))

	def test_case_insensitivity(self):
		r = reppy.parse('''# robots.txt for http://www.example.com/
			User-agent: Foobot
			Disallow: /''')
		self.assertTrue(not r.allowed('/', 'Foobot'))
		self.assertTrue(not r.allowed('/', 'FOOBOT'))
		self.assertTrue(not r.allowed('/', 'FoOBoT'))
		self.assertTrue(not r.allowed('/', 'foobot'))
	
	def test_fetch(self):
		# This should throw an error
		self.assertRaises(Exception, reppy.fetch('http://example.com/robots.txt'))
		
		r = reppy.fetch('http://NikitaTheSpider.com/python/rerp/robots.iso-8859-1.txt')
		ua = 'BättreBot'
		self.assertTrue(not r.allowed('/stuff', ua))
		self.assertTrue(    r.allowed('/index.html', ua))
		
		ua = 'BästaBot'
		self.assertTrue(    r.allowed('/stuff', ua))
		self.assertTrue(not r.allowed('/index.html', ua))
		self.assertTrue(    r.allowed('/stuff', 'foobot'))
		self.assertTrue(    r.allowed('/index.html', 'foobot'))

		r = reppy.fetch('http://NikitaTheSpider.com/python/rerp/robots.utf-8.txt')
		ua = 'BättreBot'
		self.assertTrue(not r.allowed('/stuff/', ua))
		self.assertTrue(    r.allowed('/index.html', ua))
		ua = 'BästaBot'
		self.assertTrue(    r.allowed('/stuff/', ua))
		self.assertTrue(not r.allowed('/index.html', ua))
		self.assertTrue(    r.allowed('/stuff', 'foobot'))
		self.assertTrue(    r.allowed('/index.html', 'foobot'))

		r = reppy.fetch('http://NikitaTheSpider.com/ThisDirectoryDoesNotExist/robots.txt')
		self.assertTrue(    r.allowed('/', 'foobot'))
		self.assertTrue(    r.allowed('/stuff', 'javla-foobot'))
		self.assertTrue(    r.allowed('/TotallySecretStuff', 'anybot'))

		r = reppy.fetch('http://NikitaTheSpider.com/python/rerp/robots.401.txt')
		self.assertTrue(not r.allowed('/', 'NigelBot'))
		self.assertTrue(not r.allowed('/foo/bar.html', 'StigBot'))
		self.assertTrue(not r.allowed('/index.html', 'BruceBruceBruceBot'))

		r = reppy.fetch('http://NikitaTheSpider.com/python/rerp/robots.403.txt')
		self.assertTrue(not r.allowed('/', 'NigelBot'))
		self.assertTrue(not r.allowed('/foo/bar.html', 'StigBot'))
		self.assertTrue(not r.allowed('/index.html', 'BruceBruceBruceBot'))

		r = reppy.fetch('http://NikitaTheSpider.com/python/rerp/robots.404.txt')
		self.assertTrue(    r.allowed('/', 'NigelBot'))
		self.assertTrue(    r.allowed('/foo/bar.html', 'StigBot'))
		self.assertTrue(    r.allowed('/index.html', 'BruceBruceBruceBot'))

		self.assertRaises(Exception, reppy.fetch('http://NikitaTheSpider.com/python/rerp/robots.500.txt'))

	def test_expiration(self):
		pass
		# 
		# # -----------------------------------------------------------
		# # Test the parser's expiration features
		# # -----------------------------------------------------------
		# print("Running local time test")
		# 
		# # Create a fresh parser to (re)set the expiration date. I test to see if 
		# # the dates are accurate to +/-1 minute. If your local clock is off by 
		# # more than that, these tests will fail.
		# 
		# parser = robotexclusionrulesparser.RobotExclusionRulesParser()
		# localtime = time.mktime(time.localtime())
		# assert((parser.expiration_date > localtime + robotexclusionrulesparser.SEVEN_DAYS - 60) and
		#        (parser.expiration_date < localtime + robotexclusionrulesparser.SEVEN_DAYS + 60))
		# 
		# print("Passed.")
		# 
		# 
		# print("Running UTC test")
		# 
		# parser = robotexclusionrulesparser.RobotExclusionRulesParser()
		# parser.use_local_time = False
		# utc = calendar.timegm(time.gmtime())
		# assert((parser.expiration_date > utc + robotexclusionrulesparser.SEVEN_DAYS - 60) and
		#        (parser.expiration_date < utc + robotexclusionrulesparser.SEVEN_DAYS + 60))
		# 
		# print("Passed.")

if __name__ == '__main__':
	unittest.main()
