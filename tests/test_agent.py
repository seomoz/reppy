import unittest

from reppy.robots import Agent, Robots


class AgentTest(unittest.TestCase):
    '''Tests about the Agent.'''

    def parse(self, content, name):
        '''Parse the robots.txt in content and return the agent of the provided name.'''
        return Robots.parse('http://example.com', content).agent(name)

    def test_make_allowed(self):
        '''Make an agent that allows a path.'''
        agent = Agent().disallow('/path').allow('/path/')
        self.assertTrue(agent.allowed('/path/'))
        self.assertFalse(agent.allowed('/path'))

    def test_make_disallowed(self):
        '''Make an agent that disallows a path.'''
        agent = Agent().disallow('/path')
        self.assertFalse(agent.allowed('/path'))

    def test_checks_allowed(self):
        '''Answers the allowed question.'''
        agent = self.parse('''
            User-agent: agent
            Allow: /path
        ''', 'agent')
        self.assertTrue(agent.allowed('/path'))
        self.assertTrue(agent.allowed('/elsewhere'))

    def test_honors_longest_first_priority(self):
        '''The longest matching rule takes priority.'''
        agent = self.parse('''
            User-agent: agent
            Disallow: /path
            Allow: /path/exception
        ''', 'agent')
        self.assertTrue(agent.allowed('/path/exception'))
        self.assertFalse(agent.allowed('/path'))

    def test_robots_txt_allowed(self):
        '''Robots.txt is always allowed.'''
        agent = self.parse('''
            User-agent: agent
            Disallow: /robots.txt
        ''', 'agent')
        self.assertTrue(agent.allowed('/robots.txt'))

    def test_disallow_none(self):
        '''Recognizes the "Disallow:" form of "Allow: /"'''
        agent = self.parse('''
            User-agent: agent
            Disallow:
        ''', 'agent')
        self.assertTrue(agent.allowed('/anything'))

    def test_escaped_rule(self):
        '''Handles the case where the rule is escaped.'''
        agent = self.parse('''
            User-agent: agent
            Disallow: /a%3cd.html
        ''', 'agent')
        self.assertFalse(agent.allowed('/a<d.html'))
        self.assertFalse(agent.allowed('/a%3cd.html'))

    def test_unescaped_rule(self):
        '''Handles the case where the rule is unescaped.'''
        agent = self.parse('''
            User-agent: agent
            Disallow: /a<d.html
        ''', 'agent')
        self.assertFalse(agent.allowed('/a<d.html'))
        self.assertFalse(agent.allowed('/a%3cd.html'))

    def test_escaped_rule_wildcard(self):
        '''Handles the case where the wildcard rule is escaped.'''
        agent = self.parse('''
            User-agent: agent
            Disallow: /a%3c*
        ''', 'agent')
        self.assertFalse(agent.allowed('/a<d.html'))
        self.assertFalse(agent.allowed('/a%3cd.html'))

    def test_unescaped_rule_wildcard(self):
        '''Handles the case where the wildcard rule is unescaped.'''
        agent = self.parse('''
            User-agent: agent
            Disallow: /a<*
        ''', 'agent')
        self.assertFalse(agent.allowed('/a<d.html'))
        self.assertFalse(agent.allowed('/a%3cd.html'))

    def test_accepts_full_url(self):
        '''Accepts a full URL.'''
        agent = self.parse('''
            User-agent: agent
            Disallow: /path;params?query
        ''', 'agent')
        self.assertFalse(agent.allowed('http://exmaple.com/path;params?query'))
