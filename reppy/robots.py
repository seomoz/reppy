'''A class holding a parsed robots.txt.'''

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

from .agent import Agent
from .ttl import HeaderWithDefaultPolicy
from . import util, logger, exceptions


class Robots(object):
    '''A class holding a parsed robots.txt.'''

    # The default TTL policy is to cache for 3600 seconds or what's provided in the
    # headers, and a minimum of 600 seconds
    DEFAULT_TTL_POLICY = HeaderWithDefaultPolicy(default=3600, minimum=600)

    @classmethod
    def fetch(cls, url, ttl_policy=None, max_size=1048576, *args, **kwargs):
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

    @classmethod
    def parse(cls, url, content, expires=None):
        '''Parse the provided lines as a robots.txt.'''
        sitemaps = []
        agents = {}
        agent = None
        last_agent = False
        for key, value in util.pairs(content):
            # Consecutive User-Agent lines mean they all have the same rules
            if key == 'user-agent':
                if not last_agent:
                    agent = Agent()
                agents[value] = agent
                last_agent = True
                continue
            else:
                last_agent = False

            if key == 'sitemap':
                sitemaps.append(value)
            elif key in ('disallow', 'allow', 'crawl-delay'):
                if agent is None:
                    raise ValueError(
                        'Directive "%s" must be preceeded by User-Agent' % key)

                if key == 'disallow':
                    agent.disallow(value)
                elif key == 'allow':
                    agent.allow(value)
                else:
                    try:
                        agent.delay = float(value)
                    except ValueError:
                        logger.warn('Could not parse crawl delay: %s', value)
            else:
                logger.warn('Unknown directive "%s"' % key)

        return Robots(url, agents, sitemaps, expires)

    def __init__(self, url, agents, sitemaps, expires=None):
        self.url = url
        self.agents = agents
        self.sitemaps = sitemaps
        self.expires = expires
        self.default = self.agents.get('*', None)

    @property
    def expired(self):
        '''True if the current time is past its expiration.'''
        return time.time() > self.expires

    @property
    def ttl(self):
        '''Remaining time for this response to be considered valid.'''
        return max(self.expires - time.time(), 0)

    def agent(self, name):
        '''Get the rules for the agent with the provided name.'''
        return self.agents.get(name.lower(), self.default)

    def url_allowed(self, url, agent):
        '''Return true if agent may fetch the path in url.'''
        found = self.agent(agent)
        if found is None:
            return True
        return found.url_allowed(url)

    def allowed(self, path, agent):
        '''Return true if agent may fetch path.'''
        found = self.agent(agent)
        if found is None:
            return True
        return found.allowed(path)


class AllowNone(Robots):
    '''No requests are allowed.'''

    def __init__(self, url, expires=None):
        Robots.__init__(self, url, sitemaps=[], expires=expires, agents={
            '*': Agent().disallow('/')
        })


class AllowAll(Robots):
    '''All requests are allowed.'''

    def __init__(self, url, expires=None):
        Robots.__init__(self, url, {}, [], expires=expires)
