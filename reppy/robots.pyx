# cython: linetrace=True
# distutils: define_macros=CYTHON_TRACE=1

from contextlib import closing

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
    # This is somewhat inefficient due to the copying, but it is
    # required to be copied because we often toss the containing
    # Robots object as a temporary thus we'd leave the underlying
    # Agent object dangling without a full copy.
    agent.agent = robots.robots.agent(name)
    return agent

cdef class Agent:
    '''Wrapper around rep-cpp's Rep::Agent class.'''

    cdef CppAgent agent

    from_robots = classmethod(FromRobotsMethod)

    def __str__(self):
        return self.agent.str().decode('utf8')

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


def ParseMethod(cls, url, content):
    '''Parse a robots.txt file.'''
    return cls(url, as_bytes(content))

def FetchMethod(cls, url, max_size=1048576, *args, **kwargs):
    '''Get the robots.txt at the provided URL.'''
    after_response_hook = kwargs.pop('after_response_hook', None)
    after_parse_hook = kwargs.pop('after_parse_hook', None)
    def wrap_exception(etype, cause):
        wrapped = etype(cause)
        wrapped.url = url
        if after_response_hook is not None:
            after_response_hook(wrapped)
        raise wrapped
    try:
        # Limit the size of the request
        kwargs['stream'] = True
        with closing(requests.get(url, *args, **kwargs)) as res:
            content = res.raw.read(amt=max_size, decode_content=True)
            # Try to read an additional byte, to see if the response is too big
            if res.raw.read(amt=1, decode_content=True):
                raise exceptions.ContentTooLong(
                    'Content larger than %s bytes' % max_size)

            if after_response_hook is not None:
                after_response_hook(res)

            if res.status_code == 200:
                robots = cls.parse(url, content)
                if after_parse_hook is not None:
                    after_parse_hook(robots)
                return robots
            elif res.status_code in (401, 403):
                return AllowNone(url)
            elif res.status_code >= 400 and res.status_code < 500:
                return AllowAll(url)
            else:
                raise exceptions.BadStatusCode(
                    'Got %i for %s' % (res.status_code, url), res.status_code)
    except SSLError as exc:
        wrap_exception(exceptions.SSLException, exc)
    except ConnectionError as exc:
        wrap_exception(exceptions.ConnectionException, exc)
    except (URLRequired, MissingSchema, InvalidSchema, InvalidURL) as exc:
        wrap_exception(exceptions.MalformedUrl, exc)
    except TooManyRedirects as exc:
        wrap_exception(exceptions.ExcessiveRedirects, exc)

def RobotsUrlMethod(cls, url):
    '''Get the robots.txt URL that corresponds to the provided one.'''
    return as_string(CppRobots.robotsUrl(as_bytes(url)))

cdef class Robots:
    '''Wrapper around rep-cpp's Rep::Robots class.'''

    # Class methods
    parse = classmethod(ParseMethod)
    fetch = classmethod(FetchMethod)
    robots_url = classmethod(RobotsUrlMethod)

    # Data members
    cdef CppRobots* robots

    def __init__(self, url, const string& content):
        self.robots = new CppRobots(content, as_bytes(url))

    def __str__(self):
        return self.robots.str().decode('utf8')

    def __dealloc__(self):
        del self.robots

    @property
    def sitemaps(self):
        '''Get all the sitemaps in this robots.txt.'''
        return map(as_string, self.robots.sitemaps())

    def allowed(self, path, name):
        '''Is the provided path allowed for the provided agent?'''
        return self.robots.allowed(as_bytes(path), as_bytes(name))

    def agent(self, name):
        '''Return the Agent that corresponds to name.

        Note modifications to the returned Agent will not be reflected
        in this Robots object because it is a *copy*, not the original
        Agent object.
        '''
        return Agent.from_robots(self, as_bytes(name))


cdef class AllowNone(Robots):
    '''No requests are allowed.'''

    def __init__(self, url):
        Robots.__init__(self, url, b'User-agent: *\nDisallow: /')


cdef class AllowAll(Robots):
    '''All requests are allowed.'''

    def __init__(self, url):
        Robots.__init__(self, url, b'')
