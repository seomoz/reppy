#! /usr/bin/env python

'''A robot exclusion protocol parser. Because I could not find a good one.

My thinking is thus:

- User-Agent specifies a scope.
- Allow applies a rule in that scope
- Disallow applies a rule in that scope
- Crawl-delay applies a rule in that scope (not a global)
- Sitemaps are global
'''

import re
import time
import urllib
import urllib2
import urlparse
import dateutil.parser

class agent:
	'''Represents attributes for a given robot'''
	def __init__(self):
		self.disallow   = []
		self.allow      = []
		self.crawlDelay = None
	
	def allowed(self, url):
		'''Can I fetch a given URL?'''
		path = urlparse.urlparse(url).path
		disallow = sum([int(bool(r.match(path))) for r in self.disallow])
		if not disallow:
			return True
		else:
			return bool(sum([int(bool(r.match(path))) for r in self.allow]))
	
	def disallowed(self, url):
		'''For completeness'''
		return not self.allowed(url)

class repp:
	lineRE = re.compile('^\s*(\S+)\s*:\s*(.+?)\s*$', re.I)
	
	@classmethod
	def fetch(c, url, **kwargs):
		page = urllib2.urlopen(url)
		# Try to get the header's expiration time, which we should honor
		expires = page.info().get('Expires', None)
		if expires:
			# Add a ttl to the class
			expires = time.mktime(dateutil.parser.parse(expires).timetuple())
			kwargs['ttl'] = kwargs['ttl'] or expires
		kwargs['url'] = url
		return c.parse(page.read(), **kwargs)
	
	@classmethod
	def parse(c, s, **kwargs):
		obj = c(**kwargs)
		obj._parse(s)
		return obj
	
	def refresh(self):
		'''Can only work if we have a url specified'''
		if self.url:
			page = urllib2.urlopen(self.url)
			# Try to get the header's expiration time, which we should honor
			expires = page.info().get('Expires', None)
			if expires:
				# Add a ttl to the class
				self.ttl = time.mktime(dateutil.parser.parse(expires).timetuple())
			self.parse(page.read())
	
	def makeREFromString(self, s):
		'''Make a regular expression that matches the patterns expressable in robots.txt'''
		# From the spec:
		#	http://www.robotstxt.org/norobots-rfc.txt
		# And based on Google's word:
		#	http://googlewebmastercentral.blogspot.com/2008/06/improving-on-robots-exclusion-protocol.html
		# The specific example of %2f should not be replaced. So, to accomplish that,
		# We'll replace '%2f' with '%252f', which when decoded, is %2f
		tmp = s.replace('%2f', '%252f').replace('*', '.+').replace('$', '.+')
		return re.compile(urllib.unquote(tmp))
	
	def _parse(self, s):
		# The agent we're currently working with
		cur     = agent()
		# The name of the current agent
		curname = '*'
		last    = ''
		for line in s.split('\n'):
			match = self.lineRE.match(line)
			if match:
				key = match.group(1).lower()
				val = match.group(2)
				if key == 'user-agent':
					# Store the current working agent
					self.atts['agents'][curname] = cur
					curname = val
					if last != 'user-agent':
						# If the last line was a user agent, then all lines
						# below also apply to the last user agent. So, we'll
						# have this user agent point to the one we declared
						# for the previously-listed agent
						cur = self.atts['agents'].get(curname, None) or agent()
				elif key == 'disallow':
					cur.disallow.append(self.makeREFromString(val))
				elif key == 'allow':
					cur.allow.append(self.makeREFromString(val))
				elif key == 'crawl-delay':
					cur.crawl.crawlDelay = int(val)
				elif key == 'sitemap':
					self.atts['sitemaps'].append(val)
				else:
					print 'Unknown key %s' % line
					# To skip over where we set 'last'
					continue
				last = key
			else:
				print 'Skipping line %s' % line
		# Now store the user agent that we've been working on
		self.atts['agents'][curname] = cur
	
	def __init__(self, ttl=3600*3, url=None, autorefresh=True):
		'''The string to parse, and the ttl for the robots file'''
		self.atts = {
			'sitemaps' : [],	# The sitemaps we've seen
			'agents'   : {}		# The user-agents we've seen
		}
		# The sitemaps we've seen
		self.sitemaps = []
		# When did we last parse this?
		self.parsed   = time.time()
		# Time to live
		self.ttl      = ttl
		# The url that we fetched
		self.url      = url
		# Do we refresh when we expire?
		self.autorefresh = url and autorefresh
	
	def __getattr__(self, name):
		'''So we can keep track of refreshes'''
		if self.autorefresh and self.expired():
			self.refresh()
		return self.atts[name]
	
	def remaining(self):
		'''How long is left in its life'''
		return self.parsed + ttl - time.time()
	
	def expired(self):
		'''Has this robots.txt expired?'''
		return self.remaining < 0
	
	def findAgent(self, agent):
		a = self.agents.get(agent, None)
		return a or self.agents.get('*', None)
	
	def allowed(self, agent, url):
		'''We try to perform a good match, then a * match'''
		a = self.findAgent(agent)
		if a:
			return a.allowed(url)
		else:
			return True
	
	def disallowed(self, agent):
		return not self.allowed(agent)
	
	def crawlDelay(self, agent):
		'''How fast can this '''
		a = self.findAgent(agent)
		if a:
			return a.crawlDelay
		else:
			return None