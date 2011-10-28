Robots Exclusion Protocol Parser for Python
===========================================

This started out of a lack of memoization support in other robots.txt parsers
I've encountered, and the lack of support for `Crawl-delay` and `Sitemap` in the
built-in `robotparser`.

Features
--------

- Memoization of fetched robots.txt
- Expiration taken from the `Expires` header
- Batch queries
- Configurable user agent for fetching robots.txt
- Automatic refetching basing on expiration

Usage
=====

The easiest way to use `reppy` is to just ask if a url or urls is/are allowed:

	import reppy
	# This implicitly fetches example.com's robot.txt
	reppy.allowed('http://example.com/howdy')
	# => True
	# Now, it's cached based on when it should expire (read more in `Expiration`)
	reppy.allowed('http://example.com/hello')
	# => True
	# It also supports batch queries
	reppy.allowed(['http://example.com/allowed1', 'http://example.com/allowed2', 'http://example.com/disallowed'])
	# => ['http://example.com/allowed1', 'http://example.com/allowed2']
	# Batch queries are even supported accross several domains (though fetches are not done in parallel)
	reppy.allowed(['http://a.com/allowed', 'http://b.com/allowed', 'http://b.com/disallowed'])
	# => ['http://a.com/allowed', 'http://b.com/allowed']

It's pretty easy to use. The default behavior is to fetch it for you with `urllib2`

	import reppy
	# Make a reppy object associated with a particular domain
	r = reppy.fetch('http://example.com/robots.txt')
	
but you can just as easily parse a string that you fetched.

	import urllib2
	data = urllib2.urlopen('http://example.com/robots.txt').read()
	r = reppy.parse(data)

Expiration
----------

The main advantage of having `reppy` fetch the robots.txt for you is that it can
automatically refetch after its data has expired. It's completely transparent to
you, so you don't even have to think about it -- just keep using it as normal. Or,
if you'd prefer, you can set your own time-to-live, which takes precedence:

	import reppy
	r = reppy.fetch('http://example.com/robots.txt')
	r.ttl
	# => 10800 (How long to live?)
	r.expired()
	# => False (Has it expired?)
	r.remaining()
	# => 10798 (How long until it expires)
	r = reppy.fetch('http://example.com/robots.txt', ttl=1)
	# Wait 2 seconds
	r.expired()
	# => True

Queries
-------

`Reppy` tries to keep track of the host so that you don't have to. This is done automatically
when you use `fetch`, or you can optionally provide the url you fetched it from with `parse`.
Doing so allows you to provide just the path when querying. Otherwise, you must provide the
whole url:

	# This is doable
	r = reppy.fetch('http://example.com/robots.txt')
	r.allowed('/')
	r.allowed(['/hello', '/howdy'])
	# And so is this
	data = urllib2.urlopen('http://example.com/robots.txt').read()
	r = reppy.parse(data, url='http://example.com/robots.txt')
	r.allowed(['/', '/hello', '/howdy'])
	# However, we don't implicitly know which domain these are from
	reppy.allowed(['/', '/hello', '/howdy'])

Crawl-Delay and Sitemaps
------------------------

`Reppy` also exposes the non-RFC, but widely-used `Crawl-Delay` and `Sitemaps` attributes. The
crawl delay is considered on a per-user agent basis, but the sitemaps are considered global. If
they are not specified, the crawl delay is `None`, and sitemaps is an empty list. For example,
if this is my robots.txt:

	User-agent: *
	Crawl-delay: 1
	Sitemap: http://example.com/sitemap.xml
	Sitemap: http://example.com/sitemap2.xml
	
Then these are accessible:

	with file('myrobots.txt', 'r') as f:
		r = reppy.parse(f.read())
	r.sitemaps
	# => ['http://example.com/sitemap.xml', 'http://example.com/sitemap2.xml']
	r.crawlDelay
	# => 1

User-Agent Matching
-------------------

You can provide a user agent of your choosing for fetching robots.txt, and then the user agent
string we match is defaulted to what appears before the first `/`. For example, if you provide
the user agent as 'MyCrawler/1.0', then we'll use 'MyCrawler' as the string to match against
`User-agent`. Comparisons are case-insensitive, and we **do not support wildcards in User-Agent**.
If this default doesn't suit you, you can provide an alternative:

	# This will match against 'myuseragent' by default
	r = reppy.fetch('http://example.com/robots.txt', userAgent='MyUserAgent/1.0')
	# This will match against 'someotheragent' instead
	r = reppy.fetch('http://example.com/robots.txt', userAgent='MyUserAgent/1.0', userAgentString='someotheragent')

Path-Matching
-------------

Path matching supports both `*` and `$`