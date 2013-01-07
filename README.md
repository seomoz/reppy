Robots Exclusion Protocol Parser for Python
===========================================

This started out of a lack of memoization support in other robots.txt parsers
I've encountered, and the lack of support for `Crawl-delay` and `Sitemap` in
the built-in `robotparser`.

Features
--------
- Configurable caching of robots.txt files
- Expiration based on the `Expires` and `Cache-Control` headers
- Configurable automatic refetching basing on expiration
- Support for Crawl-delay
- Support for Sitemaps
- Wildcard matching

Matching
========
This package supports the
[1996 RFC](http://www.robotstxt.org/norobots-rfc.txt), as well as additional
commonly-implemented features, like wildcard matching, crawl-delay, and
sitemaps. There are varying approaches to matching `Allow` and `Disallow`. One
approach is to use the longest match. Another is to use the most specific.
This package chooses to follow the directive that is longest, the assumption
being that it's the one that is most specific -- a term that is a little
difficult to define in this context.

Usage
=====
The easiest way to use `reppy`, you first need a cache object. This object
controls how fetched `robots.txt` are stored and cached, and provides an
interface to issue queries about urls.

```python
from reppy.cache import RobotsCache
# Any args and kwargs provided here are given to `requests.get`. You can use
# this to set request headers and the like
robots = RobotsCache()
# Now ask if a particular url is allowed
robots.allowed('http://example.com/hello', 'my-agent')
```

By default, it fetches `robots.txt` for you using `requests`. If you're,
interested in getting a `Rules` object (which is a parsed `robots.txt` file),
you can ask for it without it being cached:

```python
# This returns a Rules object, which is not cached, but can answer queries
rules = robots.fetch('http://example.com/')
rules.allowed('http://example.com/foo', 'my-agent')
```

If automatic fetching doesn't suit your needs (perhaps you have your own way of
fetching pages), you can still make use of the cache object. To do this,
you'll need to make your own `Rules` object:

```python
from reppy.parser import Rules
# Do some fetching here
# ...
robots.add(Rules('http://example.com/robots.txt',
	status_code,     # What status code did we get back?
	content,         # The content of the fetched page
	expiration))     # When is this page set to expire?
```

Expiration
----------
A `RobotsCache` object can track the expiration times for fetched `robots.txt`
files. This is taken from either the `Cache-Control` or `Expires` headers if
they are present, or defaults to an hour. At some point, I would like this to
be configurable, but I'm still trying to think of the best interface.

```python
rules = RobotsCache.find('http://example.com/robots.txt')
# Now long before it expires?
rules.ttl
# When does it expire?
rules.expires
# Has it expired?
rules.expired
```

Caching
=======
The default caching policy is to cache everything until it expires. At some
point, we'll add other caching policies (probably LRU), but you can also extend
the `RobotsCache` object to implement your own. Override the `cache` method and
you're on your way!

```python
class MyCache(RobotsCache):
	def cache(self, url, *args, **kwargs):
	    fetched = self.fetch(url, *args, **kwargs)
	    self._cache[Utility.hostname(url)] = fetched
	    # Figure out any cached items that need eviction
	    return fetched
```

You may want to explicitly clear the cache, too, which can be done either with
the `clear` method, or it's done automatically when used as a context manager:

```python
# Store some results
robots.allowed('http://example.com/foo')
# Now we'll get rid of the cache
robots.clear()

# Now as a context manager
with robots:
	robots.allowed('http://example.com/foo')

# Now there's nothing cached in robots
```

Queries
=======
Allowed / Disallowed
--------------------
Each of these takes a url and a short user agent string (for example,
'my-agent').

```python
robots.allowed('http://example.com/allowed.html', 'my-agent')
# True
robots.disallowed('http://example.com/allowed.html', 'my-agen't)
# False
```

Alternatively, a rules object provides the same interface:

```python
rules = robots.find('http://example.com/allowed')
rules.allowed('http://example.com/allowed', 'my-agent')
```

Crawl-Delay
-----------
Crawl delay can be specified on a per-agent basis, so when checking the crawl
delay for a site, you must provide an agent.

```python
robots.delay('http://example.com/foo', 'my-agent')
```

If there is no crawl delay specified for the provided agent /or/ for the `*`
agent, then `delay` returns None

Sitemaps
--------
A `robots.txt` file can also specify sitemaps, accessible through a `Rules`
object or a `RobotsCache` object:

```python
robots.sitemaps('http://example.com/')
```

Path-Matching
-------------
Path matching supports both `*` and `$`