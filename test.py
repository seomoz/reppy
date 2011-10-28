#! /usr/bin/env python

'''These are unit tests that are derived from the rfc at http://www.robotstxt.org/norobots-rfc.txt'''

from repp import repp

import random
import unittest

class TestRFC(unittest.TestCase):
	def test_basic(self):
		# Test beginning matching
		r = repp.parse('''
			User-agent: *
			Disallow: /tmp''')
		self.assertTrue(not r.allowed('t', '/tmp'))
		self.assertTrue(not r.allowed('t', '/tmp.html'))
		self.assertTrue(not r.allowed('t', '/tmp/a.html'))

		r = repp.parse('''
			User-agent: *
			Disallow: /tmp/''')
		self.assertTrue(    r.allowed('t', '/tmp'))
		self.assertTrue(not r.allowed('t', '/tmp/'))
		self.assertTrue(not r.allowed('t', '/tmp/a.html'))

	def test_unquoting(self):
		# Now test escaping entities
		r = repp.parse('''
			User-agent: *
			Disallow: /a%3cd.html''')
		self.assertTrue(not r.allowed('t', '/a%3cd.html'))
		self.assertTrue(not r.allowed('t', '/a%3Cd.html'))
		# And case indpendent
		r = repp.parse('''
			User-agent: *
			Disallow: /a%3Cd.html''')
		self.assertTrue(not r.allowed('t', '/a%3cd.html'))
		self.assertTrue(not r.allowed('t', '/a%3Cd.html'))
		# And escape the urls themselves
		r = repp.parse('''
			User-agent: *
			Disallow: /%7ejoe/index.html''')
		self.assertTrue(not r.allowed('t', '/~joe/index.html'))
		self.assertTrue(not r.allowed('t', '/%7ejoe/index.html'))
	
	def test_unquoting_forward_slash(self):
		# But not with foward slash
		r = repp.parse('''
			User-agent: *
			Disallow: /a%2fb.html''')
		self.assertTrue(not r.allowed('t', '/a%2fb.html'))
		self.assertTrue(    r.allowed('t', '/a/b.html'))
		r = repp.parse('''
			User-agent: *
			Disallow: /a/b.html''')
		self.assertTrue(    r.allowed('t', '/a%2fb.html'))
		self.assertTrue(not r.allowed('t', '/a/b.html'))
	
	def test_rfc_example(self):
		r = repp.parse('''# /robots.txt for http://www.fict.org/
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
		self.assertTrue(not r.allowed('unhipbot', '/'))
		self.assertTrue(not r.allowed('unhipbot', '/index.html'))
		self.assertTrue(    r.allowed('unhipbot', '/robots.txt'))
		self.assertTrue(not r.allowed('unhipbot', '/server.html'))
		self.assertTrue(not r.allowed('unhipbot', '/services/fast.html'))
		self.assertTrue(not r.allowed('unhipbot', '/services/slow.html'))
		self.assertTrue(not r.allowed('unhipbot', '/orgo.gif'))
		self.assertTrue(not r.allowed('unhipbot', '/org/about.html'))
		self.assertTrue(not r.allowed('unhipbot', '/org/plans.html'))
		self.assertTrue(not r.allowed('unhipbot', '/%7Ejim/jim.html'))
		self.assertTrue(not r.allowed('unhipbot', '/%7Emak/mak.html'))
		# The webcrawler agent
		self.assertTrue(    r.allowed('webcrawler', '/'))
		self.assertTrue(    r.allowed('webcrawler', '/index.html'))
		self.assertTrue(    r.allowed('webcrawler', '/robots.txt'))
		self.assertTrue(    r.allowed('webcrawler', '/server.html'))
		self.assertTrue(    r.allowed('webcrawler', '/services/fast.html'))
		self.assertTrue(    r.allowed('webcrawler', '/services/slow.html'))
		self.assertTrue(    r.allowed('webcrawler', '/orgo.gif'))
		self.assertTrue(    r.allowed('webcrawler', '/org/about.html'))
		self.assertTrue(    r.allowed('webcrawler', '/org/plans.html'))
		self.assertTrue(    r.allowed('webcrawler', '/%7Ejim/jim.html'))
		self.assertTrue(    r.allowed('webcrawler', '/%7Emak/mak.html'))
		# The excite agent
		self.assertTrue(    r.allowed('excite', '/'))
		self.assertTrue(    r.allowed('excite', '/index.html'))
		self.assertTrue(    r.allowed('excite', '/robots.txt'))
		self.assertTrue(    r.allowed('excite', '/server.html'))
		self.assertTrue(    r.allowed('excite', '/services/fast.html'))
		self.assertTrue(    r.allowed('excite', '/services/slow.html'))
		self.assertTrue(    r.allowed('excite', '/orgo.gif'))
		self.assertTrue(    r.allowed('excite', '/org/about.html'))
		self.assertTrue(    r.allowed('excite', '/org/plans.html'))
		self.assertTrue(    r.allowed('excite', '/%7Ejim/jim.html'))
		self.assertTrue(    r.allowed('excite', '/%7Emak/mak.html'))
		# All others
		self.assertTrue(not r.allowed('anything', '/'))
		self.assertTrue(not r.allowed('anything', '/index.html'))
		self.assertTrue(    r.allowed('anything', '/robots.txt'))
		self.assertTrue(    r.allowed('anything', '/server.html'))
		self.assertTrue(    r.allowed('anything', '/services/fast.html'))
		self.assertTrue(    r.allowed('anything', '/services/slow.html'))
		self.assertTrue(not r.allowed('anything', '/orgo.gif'))
		self.assertTrue(    r.allowed('anything', '/org/about.html'))
		self.assertTrue(not r.allowed('anything', '/org/plans.html'))
		self.assertTrue(not r.allowed('anything', '/%7Ejim/jim.html'))
		self.assertTrue(    r.allowed('anything', '/%7Emak/mak.html'))

if __name__ == '__main__':
	unittest.main()
