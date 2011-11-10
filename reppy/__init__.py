#! /usr/bin/env python
#
# Copyright (c) 2011 SEOmoz
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

'''A robot exclusion protocol parser. Because I could not find a good one.'''

__author__     = 'Dan Lecocq'
__copyright__  = '2011 SEOmoz'
__license__    = 'SEOmoz'
__version__    = '0.1.0'
__maintainer__ = 'Dan Lecocq'
__email__      = 'dan@seomoz.org'
__status__     = 'Development'

import re
import time
import urllib
import urllib2
import logging
import urlparse
import dateutil.parser

logger = logging.getLogger('reppy')
formatter = logging.Formatter('%(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)

# A hash of robots for various sites
robots = {}

def fetch(url, **kwargs):
	'''Make a reppy object, fetching the url'''
	obj = reppy(url=url, **kwargs)
	obj.refresh()
	return obj

def parse(s, **kwargs):
	'''Make a reppy object, parsing the contents of s'''
	obj = reppy(**kwargs)
	obj.parse(s)
	return obj

def getUserAgentString(userAgent):
	'''Return a default user agent string to match, based on userAgent.
	For example, for 'MyUserAgent/1.0', it will generate 'MyUserAgent'
	'''
	return re.sub('(\S+?)(\/.+)?', r'\1', userAgent)

def findOrMakeRobot(url, agent, agentString):
	'''Either return the appropriate global reppy object, or make one'''
	global robots
	parsed = urlparse.urlparse(url)
	robot = robots.get(parsed.netloc, None)
	uas = agentString or getUserAgentString(agent)
	if not robot:
		robot = fetch('%s://%s/robots.txt' % (parsed.scheme, parsed.netloc),
			userAgent=agent, userAgentString=uas)
		robots[parsed.netloc] = robot
	return robot.findAgent(uas)

def allowed(url, agent, agentString=None):
	'''Is the given url allowed for the given agent?'''
	if isinstance(url, basestring):
		return findOrMakeRobot(url, agent, agentString).allowed(url)
	else:
		return [u for u in url if findOrMakeRobot(u, agent, agentString).allowed(u)]

def disallowed(url, agent, agentString=None):
	'''Is the given url disallowed for the given agent?'''
	not allowed(url, agent, agentString)

def crawlDelay(url, agent, agentString=None):
	'''What is the crawl delay for the given agent for the given site'''
	return findOrMakeRobot(url, agent, agentString).crawlDelay

def sitemaps(url):
	'''What are the sitemaps for the associated site'''
	return findOrMakeRobot(url).sitemaps

class agent(object):
	pathRE = re.compile(r'^([^\/]+\/\/)?([^\/]+)?(/?.+?)$')
	'''Represents attributes for a given robot'''
	def __init__(self):
		self.allowances = []
		self.crawlDelay = None
	
	def allowed(self, url):
		'''Can I fetch a given URL?'''
		match = agent.pathRE.match(url)
		path = urllib.unquote(agent.pathRE.match(url).group(3).replace('%2f', '%252f'))
		if path == '/robots.txt':
			return True
		allowed = [a for a in self.allowances if a[1].match(path)]
		if allowed:
			return max(allowed)[2]
		else:
			return True
	
	def disallowed(self, url):
		'''For completeness'''
		return not self.allowed(url)

class reppy(object):
	'''A class that represents a set of agents, and can select them appropriately.
	Associated with one robots.txt file.'''
	
	lineRE = re.compile('^\s*(\S+)\s*:\s*([^#]*)\s*(#.+)?$', re.I)
	
	def __init__(self, ttl=3600*3, url=None, autorefresh=True, userAgent='REPParser/0.1 (Python)', userAgentString=None):
		self.reset()
		# When did we last parse this?
		self.parsed    = time.time()
		# Time to live
		self.ttl       = ttl
		# The url that we fetched
		self.url       = url
		# The user agent to use for future requests
		self.userAgent = userAgent
		# The user agent string to match in robots
		self.userAgentString = (userAgentString or getUserAgentString(userAgent)).lower().encode('utf-8')
		# Do we refresh when we expire?
		self.autorefresh = url and autorefresh
	
	def __getattr__(self, name):
		'''So we can keep track of refreshes'''
		if name == 'expired':
			return self._expired()
		elif name == 'remaining':
			return self._remaining()
		elif self.autorefresh and self._expired():
			self.refresh()
		return self.atts[name.lower()]
	
	def _remaining(self):
		'''How long is left in its life'''
		return self.parsed + self.ttl - time.time()

	def _expired(self):
		'''Has this robots.txt expired?'''
		return self._remaining() < 0
	
	def reset(self):
		'''Reinitialize self'''
		self.atts = {
			'sitemaps' : [],	# The sitemaps we've seen
			'agents'   : {}		# The user-agents we've seen
		}
	
	def refresh(self):
		'''Can only work if we have a url specified'''
		if self.url:
			try:
				req = urllib2.Request(self.url, headers={'User-Agent': self.userAgent})
				page = urllib2.urlopen(req)
			except urllib2.HTTPError as e:
				if e.code == 401 and e.code == 403:
					# If disallowed, assume no access
					logger.debug('Access disallowed to site %s' % e.code)
					self.parse('''User-agent: *\nDisallow: /''')
				elif e.code >= 400 and e.code < 500:
					# From the spec, if it's a 404, then we can proceed without restriction
					logger.debug('Page %s not found.' % e.url)
					self.parse('')
				return
			self.parsed    = time.time()
			# Try to get the header's expiration time, which we should honor
			expires = page.info().get('Expires', None)
			if expires:
				# Add a ttl to the class
				self.ttl = time.time() - time.mktime(dateutil.parser.parse(expires).timetuple())
			self.parse(page.read())
	
	def makeREFromString(self, s):
		'''Make a regular expression that matches the patterns expressable in robots.txt'''
		tmp = re.escape(urllib.unquote(s.replace('%2f', '%252f')))
		return re.compile(tmp.replace('\*', '.*').replace('\$', '$'))
	
	def parse(self, s):
		'''Parse the given string and store the resultant rules'''
		self.reset()
		# The agent we're currently working with
		cur     = None
		# The name of the current agent. There are a couple schools of thought here
		# For example, by including a default agent, the robots.txt's author's intent
		# is clearly accommodated if a Disallow line appears before the a User-Agent
		# line. However, how hard is it to follow the standard? If you're writing a 
		# robots.txt, you should be able to write it correctly.
		curname = '*'
		last    = ''
		for line in s.split('\n'):
			try:
				match = self.lineRE.match(line)
				if match:
					key = match.group(1).strip().lower()
					val = match.group(2).strip()
					if key == 'user-agent' or key == 'useragent':
						# Store the current working agent
						if cur:
							self.atts['agents'][curname] = cur
						try:
							curname = val.lower().encode('utf-8')
						except:
							print 'Failed'
							curname = val.lower()
						if last != 'user-agent' and last != 'useragent':
							# If the last line was a user agent, then all lines
							# below also apply to the last user agent. So, we'll
							# have this user agent point to the one we declared
							# for the previously-listed agent
							cur = self.atts['agents'].get(curname, None) or agent()
					elif cur and key == 'disallow':
						if len(val):
							cur.allowances.append((len(val), self.makeREFromString(val), False))
					elif cur and key == 'allow':
						cur.allowances.append((len(val), self.makeREFromString(val), True ))
					elif cur and key == 'crawl-delay':
						cur.crawlDelay = float(val)
					elif cur and key == 'sitemap':
						self.atts['sitemaps'].append(val)
					else:
						logger.warn('Unknown key %s' % line)
						# To skip over where we set 'last'
						continue
					last = key
				else:
					logger.debug('Skipping line %s' % line)
			except:
				logger.exception('Error parsing...')
		# Now store the user agent that we've been working on
		self.atts['agents'][curname] = cur or agent()
		
	def findAgent(self, agent):
		'''Find the agent given a string for it'''
		try:
			agent = agent.lower().encode('utf-8')
		except:
			pass
		a = self.agents.get((agent or self.userAgentString).lower(), None)
		return a or self.agents.get('*', None)
	
	def allowed(self, url, agent=None):
		'''We try to perform a good match, then a * match'''
		a = self.findAgent(agent)
		if a:
			if isinstance(url, basestring):
				return a.allowed(url)
			else:
				return [u for u in url if a.allowed(u)]
		else:
			return True
	
	def disallowed(self, url, agent=None):
		'''For completeness'''
		return not self.allowed(url, agent)
	
	def crawlDelay(self, agent=None):
		'''How fast can this '''
		a = self.findAgent(agent)
		if a:
			return a.crawlDelay
		else:
			return None