#! /usr/bin/env python

'''These are unit tests that are derived from the rfc at http://www.robotstxt.org/norobots-rfc.txt'''

import unittest
import robotparser

class TestRobotparserRFC(unittest.TestCase):
	def test_basic(self):
		# Test beginning matching
		r = robotparser.RobotFileParser()
		r.parse('''
			User-agent: *
			Disallow: /tmp''')
		self.assertTrue(not r.can_fetch('t', '/tmp'))
		self.assertTrue(not r.can_fetch('t', '/tmp.html'))
		self.assertTrue(not r.can_fetch('t', '/tmp/a.html'))

		r = robotparser.RobotFileParser()
		r.parse('''
			User-agent: *
			Disallow: /tmp/''')
		self.assertTrue(    r.can_fetch('t', '/tmp'))
		self.assertTrue(not r.can_fetch('t', '/tmp/'))
		self.assertTrue(not r.can_fetch('t', '/tmp/a.html'))

	def test_unquoting(self):
		# Now test escaping entities
		r = robotparser.RobotFileParser()
		r.parse('''
			User-agent: *
			Disallow: /a%3cd.html''')
		self.assertTrue(not r.can_fetch('t', '/a%3cd.html'))
		self.assertTrue(not r.can_fetch('t', '/a%3Cd.html'))
		# And case indpendent
		r = robotparser.RobotFileParser()
		r.parse('''
			User-agent: *
			Disallow: /a%3Cd.html''')
		self.assertTrue(not r.can_fetch('t', '/a%3cd.html'))
		self.assertTrue(not r.can_fetch('t', '/a%3Cd.html'))
		# And escape the urls themselves
		r = robotparser.RobotFileParser()
		r.parse('''
			User-agent: *
			Disallow: /%7ejoe/index.html''')
		self.assertTrue(not r.can_fetch('t', '/~joe/index.html'))
		self.assertTrue(not r.can_fetch('t', '/%7ejoe/index.html'))

	def test_unquoting_forward_slash(self):
		# But not with foward slash
		r = robotparser.RobotFileParser()
		r.parse('''
			User-agent: *
			Disallow: /a%2fb.html''')
		self.assertTrue(not r.can_fetch('t', '/a%2fb.html'))
		self.assertTrue(    r.can_fetch('t', '/a/b.html'))
		r = robotparser.RobotFileParser()
		r.parse('''
			User-agent: *
			Disallow: /a/b.html''')
		self.assertTrue(    r.can_fetch('t', '/a%2fb.html'))
		self.assertTrue(not r.can_fetch('t', '/a/b.html'))

	def test_rfc_example(self):
		r = robotparser.RobotFileParser()
		r.parse('''# /robots.txt for http://www.fict.org/
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
		self.assertTrue(not r.can_fetch('unhipbot', '/'))
		self.assertTrue(not r.can_fetch('unhipbot', '/index.html'))
		self.assertTrue(    r.can_fetch('unhipbot', '/robots.txt'))
		self.assertTrue(not r.can_fetch('unhipbot', '/server.html'))
		self.assertTrue(not r.can_fetch('unhipbot', '/services/fast.html'))
		self.assertTrue(not r.can_fetch('unhipbot', '/services/slow.html'))
		self.assertTrue(not r.can_fetch('unhipbot', '/orgo.gif'))
		self.assertTrue(not r.can_fetch('unhipbot', '/org/about.html'))
		self.assertTrue(not r.can_fetch('unhipbot', '/org/plans.html'))
		self.assertTrue(not r.can_fetch('unhipbot', '/%7Ejim/jim.html'))
		self.assertTrue(not r.can_fetch('unhipbot', '/%7Emak/mak.html'))
		# The webcrawler agent
		self.assertTrue(    r.can_fetch('webcrawler', '/'))
		self.assertTrue(    r.can_fetch('webcrawler', '/index.html'))
		self.assertTrue(    r.can_fetch('webcrawler', '/robots.txt'))
		self.assertTrue(    r.can_fetch('webcrawler', '/server.html'))
		self.assertTrue(    r.can_fetch('webcrawler', '/services/fast.html'))
		self.assertTrue(    r.can_fetch('webcrawler', '/services/slow.html'))
		self.assertTrue(    r.can_fetch('webcrawler', '/orgo.gif'))
		self.assertTrue(    r.can_fetch('webcrawler', '/org/about.html'))
		self.assertTrue(    r.can_fetch('webcrawler', '/org/plans.html'))
		self.assertTrue(    r.can_fetch('webcrawler', '/%7Ejim/jim.html'))
		self.assertTrue(    r.can_fetch('webcrawler', '/%7Emak/mak.html'))
		# The excite agent
		self.assertTrue(    r.can_fetch('excite', '/'))
		self.assertTrue(    r.can_fetch('excite', '/index.html'))
		self.assertTrue(    r.can_fetch('excite', '/robots.txt'))
		self.assertTrue(    r.can_fetch('excite', '/server.html'))
		self.assertTrue(    r.can_fetch('excite', '/services/fast.html'))
		self.assertTrue(    r.can_fetch('excite', '/services/slow.html'))
		self.assertTrue(    r.can_fetch('excite', '/orgo.gif'))
		self.assertTrue(    r.can_fetch('excite', '/org/about.html'))
		self.assertTrue(    r.can_fetch('excite', '/org/plans.html'))
		self.assertTrue(    r.can_fetch('excite', '/%7Ejim/jim.html'))
		self.assertTrue(    r.can_fetch('excite', '/%7Emak/mak.html'))
		# All others
		self.assertTrue(not r.can_fetch('anything', '/'))
		self.assertTrue(not r.can_fetch('anything', '/index.html'))
		self.assertTrue(    r.can_fetch('anything', '/robots.txt'))
		self.assertTrue(    r.can_fetch('anything', '/server.html'))
		self.assertTrue(    r.can_fetch('anything', '/services/fast.html'))
		self.assertTrue(    r.can_fetch('anything', '/services/slow.html'))
		self.assertTrue(not r.can_fetch('anything', '/orgo.gif'))
		self.assertTrue(    r.can_fetch('anything', '/org/about.html'))
		self.assertTrue(not r.can_fetch('anything', '/org/plans.html'))
		self.assertTrue(not r.can_fetch('anything', '/%7Ejim/jim.html'))
		self.assertTrue(    r.can_fetch('anything', '/%7Emak/mak.html'))

if __name__ == '__main__':
	unittest.main()
