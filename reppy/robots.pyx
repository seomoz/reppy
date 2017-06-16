# cython: linetrace=True
# distutils: define_macros=CYTHON_TRACE=1

from contextlib import closing
import time

import requests
from requests.exceptions import (
    SSLError,
    ConnectionError,
    URLRequired,
    MissingSchema,
    InvalidSchema,
    InvalidURL,
    TooManyRedirects)
import six

from .ttl import HeaderWithDefaultPolicy
from . import util, logger, exceptions

cdef as_bytes(value):
    if isinstance(value, bytes):
        return value
    return value.encode('utf-8')

cdef as_string(value):
    if six.PY3:
        if isinstance(value, bytes):
            return value.decode('utf-8')
    return value


def FromRobotsMethod(cls, Robots robots, const string& name):
    '''Construct an Agent from a CppAgent.'''
    agent = Agent()
    agent.agent = robots.robots.agent(name)
    return agent

cdef class Agent:
    '''Wrapper around rep-cpp's Rep::Agent class.'''

    cdef CppAgent agent

    from_robots = classmethod(FromRobotsMethod)

    @property
    def delay(self):
        '''The delay associated with this agent.'''
        cdef float value = self.agent.delay()
        if value > 0:
            return value
        return None

    def allow(self, path):
        '''Allow the provided path.'''
        self.agent.allow(as_bytes(path))
        return self

    def disallow(self, path):
        '''Disallow the provided path.'''
        self.agent.disallow(as_bytes(path))
        return self

    def allowed(self, path):
        '''Is the provided URL allowed?'''
        return self.agent.allowed(as_bytes(path))


def ParseMethod(cls, url, content, expires=None):
    '''Parse a robots.txt file.'''
    return cls(url, as_bytes(content), expires)

def FetchMethod(cls, url, ttl_policy=None, max_size=1048576, *args, **kwargs):
    '''Get the robots.txt at the provided URL.'''
    try:
        # Limit the size of the request
        kwargs['stream'] = True
        with closing(requests.get(url, *args, **kwargs)) as res:
            content = res.raw.read(amt=max_size, decode_content=True)
            # Try to read an additional byte, to see if the response is too big
            if res.raw.read(amt=1, decode_content=True):
                raise exceptions.ContentTooLong(
                    'Content larger than %s bytes' % max_size)

            # Get the TTL policy's ruling on the ttl
            expires = (ttl_policy or cls.DEFAULT_TTL_POLICY).expires(res)

            if res.status_code == 200:
                return cls.parse(url, content, expires)
            elif res.status_code in (401, 403):
                return AllowNone(url, expires)
            elif res.status_code >= 400 and res.status_code < 500:
                return AllowAll(url, expires)
            else:
                raise exceptions.BadStatusCode(
                    'Got %i for %s' % (res.status_code, url), res.status_code)
    except SSLError as exc:
        raise exceptions.SSLException(exc)
    except ConnectionError as exc:
        raise exceptions.ConnectionException(exc)
    except (URLRequired, MissingSchema, InvalidSchema, InvalidURL) as exc:
        raise exceptions.MalformedUrl(exc)
    except TooManyRedirects as exc:
        raise exceptions.ExcessiveRedirects(exc)

def RobotsUrlMethod(cls, url):
    '''Get the robots.txt URL that corresponds to the provided one.'''
    return as_string(CppRobots.robotsUrl(as_bytes(url)))

cdef class Robots:
    '''Wrapper around rep-cpp's Rep::Robots class.'''

    # The default TTL policy is to cache for 3600 seconds or what's provided in the
    # headers, and a minimum of 600 seconds
    DEFAULT_TTL_POLICY = HeaderWithDefaultPolicy(default=3600, minimum=600)

    # Class methods
    parse = classmethod(ParseMethod)
    fetch = classmethod(FetchMethod)
    robots_url = classmethod(RobotsUrlMethod)

    # Data members
    cdef CppRobots* robots
    cdef object url
    cdef object expires

    def __init__(self, url, const string& content, expires=None):
        self.url = url
        self.robots = new CppRobots(content)
        self.expires = expires

    def __str__(self):
        return self.robots.str()

    def __dealloc__(self):
        del self.robots

    @property
    def sitemaps(self):
        '''Get all the sitemaps in this robots.txt.'''
        return map(as_string, self.robots.sitemaps())

    def allowed(self, path, name):
        '''Is the provided path allowed for the provided agant?'''
        return self.robots.allowed(as_bytes(path), as_bytes(name))

    def agent(self, name):
        '''Return the Agent that corresponds to name.'''
        return Agent.from_robots(self, as_bytes(name))

    @property
    def expired(self):
        '''True if the current time is past its expiration.'''
        return time.time() > self.expires

    @property
    def expires(self):
        '''The expiration of this robots.txt.'''
        return self.expires

    @property
    def ttl(self):
        '''Remaining time for this response to be considered valid.'''
        return max(self.expires - time.time(), 0)


cdef class AllowNone(Robots):
    '''No requests are allowed.'''

    def __init__(self, url, expires=None):
        Robots.__init__(self, url, b'User-agent: *\nDisallow: /', expires)


cdef class AllowAll(Robots):
    '''All requests are allowed.'''

    def __init__(self, url, expires=None):
        Robots.__init__(self, url, b'', expires)
