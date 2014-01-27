#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''Tests cribbed from linkscape/processing/test/robotstxt.test.cc'''

import unittest

import reppy
import logging
from reppy import Utility
reppy.logger.setLevel(logging.FATAL)

MYNAME = 'reppy'

class TestMozscape(unittest.TestCase):
    @staticmethod
    def parse(strng):
        '''Helper to parse a string as a Rules object'''
        return reppy.parser.Rules('http://example.com/robots.txt', 200, strng, 0)

    def test_disallow_all(self):
        rules = self.parse("User-agent: *\nDisallow: /\n")
        self.assertFalse(rules.allowed("/", MYNAME))
        self.assertFalse(rules.allowed("/cgi-bin//", MYNAME))
        self.assertFalse(rules.allowed("/tmp/", MYNAME))
        self.assertFalse(rules.allowed("/~joe/", MYNAME))
        self.assertFalse(rules.allowed("/~bob/", MYNAME))
        self.assertFalse(rules.allowed("/stuff/to/read/", MYNAME))

    def test_disallow_specific(self):
        robots_txt = ( "User-agent: *\n"
                     "Disallow: /cgi-bin/\n"
                     "Disallow: /tmp/\n"
                     "Disallow: /~joe/\n" )
        rules = self.parse(robots_txt)
        self.assertTrue(rules.allowed("/", MYNAME))
        self.assertFalse(rules.allowed("/cgi-bin//", MYNAME))
        self.assertFalse(rules.allowed("/tmp/", MYNAME))
        self.assertFalse(rules.allowed("/~joe/", MYNAME))
        self.assertTrue(rules.allowed("/~bob/", MYNAME))
        self.assertTrue(rules.allowed("/stuff/to/read/", MYNAME))

    def test_complete_access(self):
        rules = self.parse("User-agent: *\nDisallow:\n")
        self.assertTrue(rules.allowed("/", MYNAME))
        self.assertTrue(rules.allowed("/cgi-bin//", MYNAME))
        self.assertTrue(rules.allowed("/tmp/", MYNAME))
        self.assertTrue(rules.allowed("/~joe/", MYNAME))
        self.assertTrue(rules.allowed("/~bob/", MYNAME))
        self.assertTrue(rules.allowed("/stuff/to/read/", MYNAME))

    def test_disable_another_robot(self):
        rules = self.parse("User-agent: BadBot\nDisallow: /\n")
        self.assertTrue(rules.allowed("/", MYNAME))
        self.assertTrue(rules.allowed("/cgi-bin//", MYNAME))
        self.assertTrue(rules.allowed("/tmp/", MYNAME))
        self.assertTrue(rules.allowed("/~joe/", MYNAME))
        self.assertTrue(rules.allowed("/~bob/", MYNAME))
        self.assertTrue(rules.allowed("/stuff/to/read/", MYNAME))

    def test_disable_our_robot(self):
        rules = self.parse("User-agent: " + MYNAME + "\nDisallow: /\n")
        self.assertFalse(rules.allowed("/", MYNAME))
        self.assertFalse(rules.allowed("/cgi-bin//", MYNAME))
        self.assertFalse(rules.allowed("/tmp/", MYNAME))
        self.assertFalse(rules.allowed("/~joe/", MYNAME))
        self.assertFalse(rules.allowed("/~bob/", MYNAME))
        self.assertFalse(rules.allowed("/stuff/to/read/", MYNAME))

    def test_allow_another_robot(self):
        robots_txt = ( "User-agent: GoodBot\n"
                     "Disallow:\n"
                     "\n"
                     "User-agent: *\n"
                     "Disallow: /\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/", MYNAME))
        self.assertFalse(rules.allowed("/cgi-bin//", MYNAME))
        self.assertFalse(rules.allowed("/tmp/", MYNAME))
        self.assertFalse(rules.allowed("/~joe/", MYNAME))
        self.assertFalse(rules.allowed("/~bob/", MYNAME))
        self.assertFalse(rules.allowed("/stuff/to/read/", MYNAME))

    def test_allow_our_robot(self):
        robots_txt = ( "User-agent: " + MYNAME + "\n"
                     "Disallow:\n"
                     "\n"
                     "User-agent: *\n"
                     "Disallow: /\n" )
        rules = self.parse(robots_txt)
        self.assertTrue(rules.allowed("/", MYNAME))
        self.assertTrue(rules.allowed("/cgi-bin//", MYNAME))
        self.assertTrue(rules.allowed("/tmp/", MYNAME))
        self.assertTrue(rules.allowed("/~joe/", MYNAME))
        self.assertTrue(rules.allowed("/~bob/", MYNAME))
        self.assertTrue(rules.allowed("/stuff/to/read/", MYNAME))

    def test_allow_variation(self):
        robots_txt = ( "User-agent: " + MYNAME + "\n"
                     "Disallow: /\n"
                     "Allow: /tmp/\n"
                     "Allow: /stuff/\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/", MYNAME))
        self.assertFalse(rules.allowed("/cgi-bin//", MYNAME))
        self.assertTrue(rules.allowed("/tmp/", MYNAME))
        self.assertFalse(rules.allowed("/~joe/", MYNAME))
        self.assertFalse(rules.allowed("/~bob/", MYNAME))
        self.assertTrue(rules.allowed("/stuff/to/read/", MYNAME))

