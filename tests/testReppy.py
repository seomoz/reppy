#! /usr/bin/env python

'''These are unit tests that are derived from the rfc at http://www.robotstxt.org/norobots-rfc.txt'''

import os
import sys

sys.path.append(os.path.abspath('..'))

import reppy
import unittest

class TestReppyRFC(unittest.TestCase):
	def test_basic(self):
		# Test beginning matching
		r = reppy.parse('''
			User-agent: *
			Disallow: /tmp''')
		self.assertTrue(not r.allowed('/tmp', 't'))
		self.assertTrue(not r.allowed('/tmp.html', 't'))
		self.assertTrue(not r.allowed('/tmp/a.html', 't'))

		r = reppy.parse('''
			User-agent: *
			Disallow: /tmp/''')
		self.assertTrue(    r.allowed('/tmp', 't'))
		self.assertTrue(not r.allowed('/tmp/', 't'))
		self.assertTrue(not r.allowed('/tmp/a.html', 't'))

	def test_unquoting(self):
		# Now test escaping entities
		r = reppy.parse('''
			User-agent: *
			Disallow: /a%3cd.html''')
		self.assertTrue(not r.allowed('/a%3cd.html', 't'))
		self.assertTrue(not r.allowed('/a%3Cd.html', 't'))
		# And case indpendent
		r = reppy.parse('''
			User-agent: *
			Disallow: /a%3Cd.html''')
		self.assertTrue(not r.allowed('/a%3cd.html', 't'))
		self.assertTrue(not r.allowed('/a%3Cd.html', 't'))
		# And escape the urls themselves
		r = reppy.parse('''
			User-agent: *
			Disallow: /%7ejoe/index.html''')
		self.assertTrue(not r.allowed('/~joe/index.html', 't'))
		self.assertTrue(not r.allowed('/%7ejoe/index.html', 't'))
	
	def test_unquoting_forward_slash(self):
		# But not with foward slash
		r = reppy.parse('''
			User-agent: *
			Disallow: /a%2fb.html''')
		self.assertTrue(not r.allowed('/a%2fb.html', 't'))
		self.assertTrue(    r.allowed('/a/b.html', 't'))
		r = reppy.parse('''
			User-agent: *
			Disallow: /a/b.html''')
		self.assertTrue(    r.allowed('/a%2fb.html', 't'))
		self.assertTrue(not r.allowed('/a/b.html', 't'))
	
	def test_rfc_example(self):
		r = reppy.parse('''# /robots.txt for http://www.fict.org/
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
		self.assertTrue(not r.allowed('/', 'unhipbot'))
		self.assertTrue(not r.allowed('/index.html', 'unhipbot'))
		self.assertTrue(    r.allowed('/robots.txt', 'unhipbot'))
		self.assertTrue(not r.allowed('/server.html', 'unhipbot'))
		self.assertTrue(not r.allowed('/services/fast.html', 'unhipbot'))
		self.assertTrue(not r.allowed('/services/slow.html', 'unhipbot'))
		self.assertTrue(not r.allowed('/orgo.gif', 'unhipbot'))
		self.assertTrue(not r.allowed('/org/about.html', 'unhipbot'))
		self.assertTrue(not r.allowed('/org/plans.html', 'unhipbot'))
		self.assertTrue(not r.allowed('/%7Ejim/jim.html', 'unhipbot'))
		self.assertTrue(not r.allowed('/%7Emak/mak.html', 'unhipbot'))
		# The webcrawler agent
		self.assertTrue(    r.allowed('/', 'webcrawler'))
		self.assertTrue(    r.allowed('/index.html', 'webcrawler'))
		self.assertTrue(    r.allowed('/robots.txt', 'webcrawler'))
		self.assertTrue(    r.allowed('/server.html', 'webcrawler'))
		self.assertTrue(    r.allowed('/services/fast.html', 'webcrawler'))
		self.assertTrue(    r.allowed('/services/slow.html', 'webcrawler'))
		self.assertTrue(    r.allowed('/orgo.gif', 'webcrawler'))
		self.assertTrue(    r.allowed('/org/about.html', 'webcrawler'))
		self.assertTrue(    r.allowed('/org/plans.html', 'webcrawler'))
		self.assertTrue(    r.allowed('/%7Ejim/jim.html', 'webcrawler'))
		self.assertTrue(    r.allowed('/%7Emak/mak.html', 'webcrawler'))
		# The excite agent
		self.assertTrue(    r.allowed('/', 'excite'))
		self.assertTrue(    r.allowed('/index.html', 'excite'))
		self.assertTrue(    r.allowed('/robots.txt', 'excite'))
		self.assertTrue(    r.allowed('/server.html', 'excite'))
		self.assertTrue(    r.allowed('/services/fast.html', 'excite'))
		self.assertTrue(    r.allowed('/services/slow.html', 'excite'))
		self.assertTrue(    r.allowed('/orgo.gif', 'excite'))
		self.assertTrue(    r.allowed('/org/about.html', 'excite'))
		self.assertTrue(    r.allowed('/org/plans.html', 'excite'))
		self.assertTrue(    r.allowed('/%7Ejim/jim.html', 'excite'))
		self.assertTrue(    r.allowed('/%7Emak/mak.html', 'excite'))
		# All others
		self.assertTrue(not r.allowed('/', 'anything'))
		self.assertTrue(not r.allowed('/index.html', 'anything'))
		self.assertTrue(    r.allowed('/robots.txt', 'anything'))
		self.assertTrue(    r.allowed('/server.html', 'anything'))
		self.assertTrue(    r.allowed('/services/fast.html', 'anything'))
		self.assertTrue(    r.allowed('/services/slow.html', 'anything'))
		self.assertTrue(not r.allowed('/orgo.gif', 'anything'))
		self.assertTrue(    r.allowed('/org/about.html', 'anything'))
		self.assertTrue(not r.allowed('/org/plans.html', 'anything'))
		self.assertTrue(not r.allowed('/%7Ejim/jim.html', 'anything'))
		self.assertTrue(    r.allowed('/%7Emak/mak.html', 'anything'))

if __name__ == '__main__':
	unittest.main()
