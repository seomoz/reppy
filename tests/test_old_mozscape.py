#! /usr/bin/env python
# -*- coding: utf-8 -*-

'''Tests cribbed from linkscape/processing/test/robotstxt.test.old.cc'''

import unittest

import reppy
import logging
from reppy import Utility
reppy.logger.setLevel(logging.FATAL)

MYNAME = 'rogerbot'

class TestOldMozscape(unittest.TestCase):
    @staticmethod
    def parse(strng):
        '''Helper to parse a string as a Rules object'''
        return reppy.parser.Rules('http://example.com/robots.txt', 200, strng, 0)

    def test_wwwseomozorg(self):
        robots_txt = ( "../resources.test/rep/www.seomoz.org\n"
                     "User-agent: *\n"
                     "Disallow: /blogdetail.php?ID=537\n"
                     "Disallow: /tracker\n"
                     "\n"
                     "Sitemap: http://www.seomoz.org/sitemap.xml.gz\n"
                     "Sitemap: http://files.wistia.com/sitemaps/seomoz_video_sitemap.xml\n" )
        rules = self.parse(robots_txt)
        # Basic functionality, and lack of case sensitivity.
        for agent in [ 'reppy', 'rEpPy' ]:
            self.assertTrue(rules.allowed("/blog", agent))
            self.assertFalse(rules.allowed("/blogdetail.php?ID=537", agent))
            self.assertFalse(rules.allowed("/tracker", agent))

    def test_allowall(self):
        rules = self.parse("User-agent: *\nDisallow:")
        for agent in [ "reppy", "oijsdofijsdofijsodifj" ]:
            self.assertTrue(rules.allowed("/", agent))
            self.assertTrue(rules.allowed("/foo", agent))
            self.assertTrue(rules.allowed("/foo.html", agent))
            self.assertTrue(rules.allowed("/foo/bar", agent))
            self.assertTrue(rules.allowed("/foo/bar.html", agent))

    def test_disallowall(self):
        rules = self.parse("User-agent: *\nDisallow: /\n")
        for agent in [ "reppy", "oijsdofijsdofijsodifj" ]:
            self.assertFalse(rules.allowed("/", agent))
            self.assertFalse(rules.allowed("/foo", agent))
            self.assertFalse(rules.allowed("/foo.html", agent))
            self.assertFalse(rules.allowed("/foo/bar", agent))
            self.assertFalse(rules.allowed("/foo/bar.html", agent))

    def test_no_googlebot_folder(self):
        robots_txt = ( "User-agent: Googlebot\n"
                     "Disallow: /no-google/\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/no-google/", "googlebot"))
        self.assertFalse(rules.allowed("/no-google/something", "googlebot"))
        self.assertFalse(rules.allowed("/no-google/something.html", "googlebot"))
        self.assertTrue(rules.allowed("/", "googlebot"))
        self.assertTrue(rules.allowed("/somethingelse", "googlebot"))

    def test_no_googlebot_file(self):
        robots_txt = ( "User-agent: Googlebot\n"
                     "Disallow: /no-google/blocked-page.html\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/no-google/blocked-page.html", "googlebot"))
        self.assertTrue(rules.allowed("/", "googlebot"))
        self.assertTrue(rules.allowed("/no-google", "googlebot"))
        self.assertTrue(rules.allowed("/no-google/someotherfolder", "googlebot"))
        self.assertTrue(rules.allowed("/no-google/someotherfolder/somefile", "googlebot"))

    def test_rogerbot_only(self):
        robots_txt = ( "User-agent: *\n"
                     "Disallow: /no-bots/block-all-bots-except-rogerbot-page.html  \t\t\t\t\n"
                     "\n"
                     "User-agent: rogerbot\n"
                     "Allow: /no-bots/block-all-bots-except-rogerbot-page.html\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/no-bots/block-all-bots-except-rogerbot-page.html", "notroger"))
        self.assertTrue(rules.allowed("/", "notroger"))
        self.assertTrue(rules.allowed("/no-bots/block-all-bots-except-rogerbot-page.html", "rogerbot"))
        self.assertTrue(rules.allowed("/", "rogerbot"))

    def test_allow_certain_pages_only(self):
        robots_txt = ( "User-agent: *\n"
                     "Allow: /onepage.html\n"
                     "Allow: /oneotherpage.php\n"
                     "Disallow: /\n"
                     "Allow: /subfolder/page1.html\n"
                     "Allow: /subfolder/page2.php\n"
                     "Disallow: /subfolder/\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/", "reppy"))
        self.assertFalse(rules.allowed("/foo", "reppy"))
        self.assertFalse(rules.allowed("/bar.html", "reppy"))
        self.assertTrue(rules.allowed("/onepage.html", "reppy"))
        self.assertTrue(rules.allowed("/oneotherpage.php", "reppy"))
        self.assertFalse(rules.allowed("/subfolder", "reppy"))
        self.assertFalse(rules.allowed("/subfolder/", "reppy"))
        self.assertFalse(rules.allowed("/subfolder/aaaaa", "reppy"))
        self.assertTrue(rules.allowed("/subfolder/page1.html", "reppy"))
        self.assertTrue(rules.allowed("/subfolder/page2.php", "reppy"))

    def test_no_gifs_or_jpgs(self):
        robots_txt = ( "User-agent: *\n"
                     "Disallow: /*.gif$\n"
                     "Disallow: /*.jpg$\n" )
        rules = self.parse(robots_txt)

        self.assertTrue(rules.allowed("/", "reppy"))
        self.assertTrue(rules.allowed("/foo", "reppy"))
        self.assertTrue(rules.allowed("/foo.html", "reppy"))
        self.assertTrue(rules.allowed("/foo/bar", "reppy"))
        self.assertTrue(rules.allowed("/foo/bar.html", "reppy"))
        self.assertFalse(rules.allowed("/test.jpg", "reppy"))
        self.assertFalse(rules.allowed("/foo/test.jpg", "reppy"))
        self.assertFalse(rules.allowed("/foo/bar/test.jpg", "reppy"))
        self.assertTrue(rules.allowed("/the-jpg-extension-is-awesome.html", "reppy"))

        # Edge cases where the wildcard could match in multiple places
        self.assertFalse(rules.allowed("/jpg.jpg", "reppy"))
        self.assertFalse(rules.allowed("/foojpg.jpg", "reppy"))
        self.assertFalse(rules.allowed("/bar/foojpg.jpg", "reppy"))
        self.assertFalse(rules.allowed("/.jpg.jpg", "reppy"))
        self.assertFalse(rules.allowed("/.jpg/.jpg", "reppy"))
        self.assertFalse(rules.allowed("/test.gif", "reppy"))
        self.assertFalse(rules.allowed("/foo/test.gif", "reppy"))
        self.assertFalse(rules.allowed("/foo/bar/test.gif", "reppy"))
        self.assertTrue(rules.allowed("/the-gif-extension-is-awesome.html", "reppy"))

    def test_block_subdirectory_wildcard(self):
        robots_txt = ( "User-agent: *\n"
                     "Disallow: /private*/\n" )
        rules = self.parse(robots_txt)

        self.assertTrue(rules.allowed("/", "reppy"))
        self.assertTrue(rules.allowed("/foo", "reppy"))
        self.assertTrue(rules.allowed("/foo.html", "reppy"))
        self.assertTrue(rules.allowed("/foo/bar", "reppy"))
        self.assertTrue(rules.allowed("/foo/bar.html", "reppy"))

        # Disallow clause ends with a slash, so these shouldn't match
        self.assertTrue(rules.allowed("/private", "reppy"))
        self.assertTrue(rules.allowed("/privates", "reppy"))
        self.assertTrue(rules.allowed("/privatedir", "reppy"))
        self.assertFalse(rules.allowed("/private/", "reppy"))
        self.assertFalse(rules.allowed("/private/foo", "reppy"))
        self.assertFalse(rules.allowed("/private/foo/bar.html", "reppy"))
        self.assertFalse(rules.allowed("/privates/", "reppy"))
        self.assertFalse(rules.allowed("/privates/foo", "reppy"))
        self.assertFalse(rules.allowed("/privates/foo/bar.html", "reppy"))
        self.assertFalse(rules.allowed("/privatedir/", "reppy"))
        self.assertFalse(rules.allowed("/privatedir/foo", "reppy"))
        self.assertFalse(rules.allowed("/privatedir/foo/bar.html", "reppy"))

    def test_block_urls_with_question_marks(self):
        robots_txt = ( "User-agent: *\n"
                     "Disallow: /*?\n" )
        rules = self.parse(robots_txt)
        self.assertTrue(rules.allowed("/", "reppy"))
        self.assertTrue(rules.allowed("/foo", "reppy"))
        self.assertTrue(rules.allowed("/foo.html", "reppy"))
        self.assertTrue(rules.allowed("/foo/bar", "reppy"))
        self.assertTrue(rules.allowed("/foo/bar.html", "reppy"))
        self.assertFalse(rules.allowed("/?", "reppy"))
        self.assertFalse(rules.allowed("/foo?q=param", "reppy"))
        self.assertFalse(rules.allowed("/foo.html?q=param", "reppy"))
        self.assertFalse(rules.allowed("/foo/bar?q=param", "reppy"))
        self.assertFalse(rules.allowed("/foo/bar.html?q=param&bar=baz", "reppy"))

    def test_no_question_marks_except_at_end(self):
        robots_txt = ( "User-agent: *\n"
                     "Allow: /*?$\n"
                     "Disallow: /*?\n" )
        rules = self.parse(robots_txt)
        self.assertTrue(rules.allowed("/", "reppy"))
        self.assertTrue(rules.allowed("/foo", "reppy"))
        self.assertTrue(rules.allowed("/foo.html", "reppy"))
        self.assertTrue(rules.allowed("/foo/bar", "reppy"))
        self.assertTrue(rules.allowed("/foo/bar.html", "reppy"))
        self.assertTrue(rules.allowed("/?", "reppy"))
        self.assertTrue(rules.allowed("/foo/bar.html?", "reppy"))
        self.assertFalse(rules.allowed("/foo?q=param", "reppy"))
        self.assertFalse(rules.allowed("/foo.html?q=param", "reppy"))
        self.assertFalse(rules.allowed("/foo/bar?q=param", "reppy"))
        self.assertFalse(rules.allowed("/foo/bar.html?q=param&bar=baz", "reppy"))

    def test_wildcard_edge_cases(self):
        robots_txt = ( "User-agent: *\n"
                     "Disallow: /*one\n"
                     "Disallow: /two*three\n"
                     "Disallow: /irrelevant/four*five\n"
                     "Disallow: /six*\n"
                     "Disallow: /foo/*/seven*/eight*nine\n"
                     "Disallow: /foo/*/*ten$\n"
                     "\n"
                     "Disallow: /*products/default.aspx\n"
                     "Disallow: /*/feed/$\n" )
        rules = self.parse(robots_txt)
        self.assertTrue(rules.allowed("/", "reppy"))
        self.assertTrue(rules.allowed("/foo", "reppy"))
        self.assertTrue(rules.allowed("/foo.html", "reppy"))
        self.assertTrue(rules.allowed("/foo/bar", "reppy"))
        self.assertTrue(rules.allowed("/foo/bar.html", "reppy"))
        self.assertFalse(rules.allowed("/one", "reppy"))
        self.assertFalse(rules.allowed("/aaaone", "reppy"))
        self.assertFalse(rules.allowed("/aaaaoneaaa", "reppy"))
        self.assertFalse(rules.allowed("/oneaaaa", "reppy"))
        self.assertFalse(rules.allowed("/twothree", "reppy"))
        self.assertFalse(rules.allowed("/twoaaathree", "reppy"))
        self.assertFalse(rules.allowed("/twoaaaathreeaaa", "reppy"))
        self.assertFalse(rules.allowed("/twothreeaaa", "reppy"))
        self.assertFalse(rules.allowed("/irrelevant/fourfive", "reppy"))
        self.assertFalse(rules.allowed("/irrelevant/fouraaaafive", "reppy"))
        self.assertFalse(rules.allowed("/irrelevant/fouraaafiveaaaa", "reppy"))
        self.assertFalse(rules.allowed("/irrelevant/fourfiveaaa", "reppy"))
        self.assertFalse(rules.allowed("/six", "reppy"))
        self.assertFalse(rules.allowed("/sixaaaa", "reppy"))
        self.assertFalse(rules.allowed("/products/default.aspx", "reppy"))
        self.assertFalse(rules.allowed("/author/admin/feed/", "reppy"))

    def test_allow_edge_cases(self):
        robots_txt = ( "User-agent: *\n"
                     "Disallow:\t/somereallylongfolder/\n"
                     "Allow:\t\t/*.jpg\n"
                     "\n"
                     "Disallow:\t/sales-secrets.php\n"
                     "Allow: \t\t/sales-secrets.php\n"
                     "\n"
                     "Disallow:\t/folder\n"
                     "Allow:\t\t/folder/\n"
                     "\n"
                     "Allow:\t\t/folder2\n"
                     "Disallow:\t/folder2/\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/somereallylongfolder/", "reppy"))
        self.assertFalse(rules.allowed("/somereallylongfolder/aaaa", "reppy"))
        self.assertFalse(rules.allowed("/somereallylongfolder/test.jpg", "reppy"))
        self.assertTrue(rules.allowed("/sales-secrets.php", "reppy"))
        self.assertTrue(rules.allowed("/folder/page", "reppy"))
        self.assertTrue(rules.allowed("/folder/page2", "reppy"))

    def test_redundant_allow(self):
        robots_txt = ( "User-agent: *\n"
                     "Disallow: /en/\n"
                     "Disallow: /files/documentation/\n"
                     "Disallow: /files/\n"
                     "Disallow: /de/careers/\n"
                     "Disallow: /images/\n"
                     "\n"
                     "Disallow: /print_mode.yes/\n"
                     "Disallow: /?product=lutensit&print_mode=yes&googlebot=nocrawl\n"
                     "Allow: /\n"
                     "Disallow: /search/\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/print_mode.yes/", "reppy"))
        self.assertFalse(rules.allowed("/print_mode.yes/foo", "reppy"))
        self.assertFalse(rules.allowed("/search/", "reppy"))
        self.assertFalse(rules.allowed("/search/foo", "reppy"))

    # Some comments, wildcards, and anchor tests -- this was a legacy test
    # ported from urlexclude
    def test_legacy_test_1(self):
        robots_txt = ( "user-agent: *  #a comment!\n"
                     "disallow: /Blerf\n"
                     "disallow: /Blerg$\n"
                     "disallow: /blerf/*/print.html$#a comment\n"
                     "disallow: /blerf/*/blim/blerf$\n"
                     "disallow: /plerf/*/blim/blim$\n"
                     "\tuser-agent: BLERF\n"
                     "    DisALLOW: \tblerfPage\n"
                     "blerf:blah\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/Blerf/blah", "reppy"))
        self.assertTrue(rules.allowed("/Blerg/blah", "reppy"))
        self.assertTrue(rules.allowed("/blerf/blah", "reppy"))
        self.assertFalse(rules.allowed("/Blerg", "reppy"))
        self.assertFalse(rules.allowed("/blerf/some/subdirs/print.html", "reppy"))
        self.assertTrue(rules.allowed("/blerf/some/subdirs/print.html?extra=stuff", "reppy"))
        self.assertFalse(rules.allowed("/blerf/some/sub/dirs/blim/blim/blerf", "reppy"))
        self.assertFalse(rules.allowed("/plerf/some/sub/dirs/blim/blim", "reppy"))

    def test_legacy_test_2(self):
        robots_txt = ( "User-agent: *\n"
                     "Allow: /searchhistory/\n"
                     "Disallow: /news?output=xhtml&\n"
                     "Allow: /news?output=xhtml\n"
                     "Disallow: /search\n"
                     "Disallow: /groups\n"
                     "Disallow: /images\n"
                     "Disallow: /catalogs\n"
                     "Disallow: /catalogues\n"
                     "Disallow: /news\n"
                     "Disallow: /nwshp\n"
                     "Allow: /news?btcid=\n"
                     "Disallow: /news?btcid=*&\n"
                     "Allow: /news?btaid=\n"
                     "Disallow: /news?btaid=*&\n"
                     "Disallow: /?\n"
                     "Disallow: /addurl/image?\n"
                     "Disallow: /pagead/\n"
                     "Disallow: /relpage/\n"
                     "Disallow: /relcontent\n"
                     "Disallow: /sorry/\n"
                     "Disallow: /imgres\n"
                     "Disallow: /keyword/\n"
                     "Disallow: /u/\n"
                     "Disallow: /univ/\n"
                     "Disallow: /cobrand\n"
                     "Disallow: /custom\n"
                     "Disallow: /advanced_group_search\n"
                     "Disallow: /advanced_search\n"
                     "Disallow: /googlesite\n"
                     "Disallow: /preferences\n"
                     "Disallow: /setprefs\n"
                     "Disallow: /swr\n"
                     "Disallow: /url\n"
                     "Disallow: /default\n"
                     "Disallow: /m?\n"
                     "Disallow: /m/?\n"
                     "Disallow: /m/lcb\n"
                     "Disallow: /m/search?\n"
                     "Disallow: /wml?\n"
                     "Disallow: /wml/?\n"
                     "Disallow: /wml/search?\n"
                     "Disallow: /xhtml?\n"
                     "Disallow: /xhtml/?\n"
                     "Disallow: /xhtml/search?\n"
                     "Disallow: /xml?\n"
                     "Disallow: /imode?\n"
                     "Disallow: /imode/?\n"
                     "Disallow: /imode/search?\n"
                     "Disallow: /jsky?\n"
                     "Disallow: /jsky/?\n"
                     "Disallow: /jsky/search?\n"
                     "Disallow: /pda?\n"
                     "Disallow: /pda/?\n"
                     "Disallow: /pda/search?\n"
                     "Disallow: /sprint_xhtml\n"
                     "Disallow: /sprint_wml\n"
                     "Disallow: /pqa\n"
                     "Disallow: /palm\n"
                     "Disallow: /gwt/\n"
                     "Disallow: /purchases\n"
                     "Disallow: /hws\n"
                     "Disallow: /bsd?\n"
                     "Disallow: /linux?\n"
                     "Disallow: /mac?\n"
                     "Disallow: /microsoft?\n"
                     "Disallow: /unclesam?\n"
                     "Disallow: /answers/search?q=\n"
                     "Disallow: /local?\n"
                     "Disallow: /local_url\n"
                     "Disallow: /froogle?\n"
                     "Disallow: /products?\n"
                     "Disallow: /froogle_\n"
                     "Disallow: /product_\n"
                     "Disallow: /products_\n"
                     "Disallow: /print\n"
                     "Disallow: /books\n"
                     "Disallow: /patents?\n"
                     "Disallow: /scholar?\n"
                     "Disallow: /complete\n"
                     "Disallow: /sponsoredlinks\n"
                     "Disallow: /videosearch?\n"
                     "Disallow: /videopreview?\n"
                     "Disallow: /videoprograminfo?\n"
                     "Disallow: /maps?\n"
                     "Disallow: /mapstt?\n"
                     "Disallow: /mapslt?\n"
                     "Disallow: /maps/stk/\n"
                     "Disallow: /mapabcpoi?\n"
                     "Disallow: /translate?\n"
                     "Disallow: /ie?\n"
                     "Disallow: /sms/demo?\n"
                     "Disallow: /katrina?\n"
                     "Disallow: /blogsearch?\n"
                     "Disallow: /blogsearch/\n"
                     "Disallow: /blogsearch_feeds\n"
                     "Disallow: /advanced_blog_search\n"
                     "Disallow: /reader/\n"
                     "Disallow: /uds/\n"
                     "Disallow: /chart?\n"
                     "Disallow: /transit?\n"
                     "Disallow: /mbd?\n"
                     "Disallow: /extern_js/\n"
                     "Disallow: /calendar/feeds/\n"
                     "Disallow: /calendar/ical/\n"
                     "Disallow: /cl2/feeds/\n"
                     "Disallow: /cl2/ical/\n"
                     "Disallow: /coop/directory\n"
                     "Disallow: /coop/manage\n"
                     "Disallow: /trends?\n"
                     "Disallow: /trends/music?\n"
                     "Disallow: /notebook/search?\n"
                     "Disallow: /music\n"
                     "Disallow: /browsersync\n"
                     "Disallow: /call\n"
                     "Disallow: /archivesearch?\n"
                     "Disallow: /archivesearch/url\n"
                     "Disallow: /archivesearch/advanced_search\n"
                     "Disallow: /base/search?\n"
                     "Disallow: /base/reportbadoffer\n"
                     "Disallow: /base/s2\n"
                     "Disallow: /urchin_test/\n"
                     "Disallow: /movies?\n"
                     "Disallow: /codesearch?\n"
                     "Disallow: /codesearch/feeds/search?\n"
                     "Disallow: /wapsearch?\n"
                     "Disallow: /safebrowsing\n"
                     "Disallow: /reviews/search?\n"
                     "Disallow: /orkut/albums\n"
                     "Disallow: /jsapi\n"
                     "Disallow: /views?\n"
                     "Disallow: /c/\n"
                     "Disallow: /cbk\n"
                     "Disallow: /recharge/dashboard/car\n"
                     "Disallow: /recharge/dashboard/static/\n"
                     "Disallow: /translate_c?\n"
                     "Disallow: /s2/profiles/me\n"
                     "Allow: /s2/profiles\n"
                     "Disallow: /s2\n"
                     "Disallow: /transconsole/portal/\n"
                     "Disallow: /gcc/\n"
                     "Disallow: /aclk\n"
                     "Disallow: /cse?\n"
                     "Disallow: /tbproxy/\n"
                     "Disallow: /MerchantSearchBeta/\n"
                     "Disallow: /ime/\n"
                     "Disallow: /websites?\n"
                     "Disallow: /shenghuo/search?\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/?as_q=ethics&ie=UTF-8&ui=blg&bl_url=centrerion.blogspot.com&x=0&y=0&ui=blg", "reppy"))

    # Real world example with several similar disallow rules
    def test_legacy_test_3(self):
        robots_txt = ( "User-agent: *\n"
                     "Allow: /searchhistory/\n"
                     "Disallow: /news?output=xhtml&\n"
                     "Allow: /news?output=xhtml\n"
                     "Disallow: /search\n"
                     "Disallow: /groups\n"
                     "Disallow: /images\n"
                     "Disallow: /catalogs\n"
                     "Disallow: /catalogues\n"
                     "Disallow: /news\n"
                     "Disallow: /nwshp\n"
                     "Allow: /news?btcid=\n"
                     "Disallow: /news?btcid=*&\n"
                     "Allow: /news?btaid=\n"
                     "Disallow: /news?btaid=*&\n"
                     "Disallow: /?\n"
                     "Disallow: /addurl/image?\n"
                     "Disallow: /pagead/\n"
                     "Disallow: /relpage/\n"
                     "Disallow: /relcontent\n"
                     "Disallow: /sorry/\n"
                     "Disallow: /imgres\n"
                     "Disallow: /keyword/\n"
                     "Disallow: /u/\n"
                     "Disallow: /univ/\n"
                     "Disallow: /cobrand\n"
                     "Disallow: /custom\n"
                     "Disallow: /advanced_group_search\n"
                     "Disallow: /advanced_search\n"
                     "Disallow: /googlesite\n"
                     "Disallow: /preferences\n"
                     "Disallow: /setprefs\n"
                     "Disallow: /swr\n"
                     "Disallow: /url\n"
                     "Disallow: /default\n"
                     "Disallow: /m?\n"
                     "Disallow: /m/?\n"
                     "Disallow: /m/lcb\n"
                     "Disallow: /m/search?\n"
                     "Disallow: /wml?\n"
                     "Disallow: /wml/?\n"
                     "Disallow: /wml/search?\n"
                     "Disallow: /xhtml?\n"
                     "Disallow: /xhtml/?\n"
                     "Disallow: /xhtml/search?\n"
                     "Disallow: /xml?\n"
                     "Disallow: /imode?\n"
                     "Disallow: /imode/?\n"
                     "Disallow: /imode/search?\n"
                     "Disallow: /jsky?\n"
                     "Disallow: /jsky/?\n"
                     "Disallow: /jsky/search?\n"
                     "Disallow: /pda?\n"
                     "Disallow: /pda/?\n"
                     "Disallow: /pda/search?\n"
                     "Disallow: /sprint_xhtml\n"
                     "Disallow: /sprint_wml\n"
                     "Disallow: /pqa\n"
                     "Disallow: /palm\n"
                     "Disallow: /gwt/\n"
                     "Disallow: /purchases\n"
                     "Disallow: /hws\n"
                     "Disallow: /bsd?\n"
                     "Disallow: /linux?\n"
                     "Disallow: /mac?\n"
                     "Disallow: /microsoft?\n"
                     "Disallow: /unclesam?\n"
                     "Disallow: /answers/search?q=\n"
                     "Disallow: /local?\n"
                     "Disallow: /local_url\n"
                     "Disallow: /froogle?\n"
                     "Disallow: /products?\n"
                     "Disallow: /froogle_\n"
                     "Disallow: /product_\n"
                     "Disallow: /products_\n"
                     "Disallow: /print\n"
                     "Disallow: /books\n"
                     "Disallow: /patents?\n"
                     "Disallow: /scholar?\n"
                     "Disallow: /complete\n"
                     "Disallow: /sponsoredlinks\n"
                     "Disallow: /videosearch?\n"
                     "Disallow: /videopreview?\n"
                     "Disallow: /videoprograminfo?\n"
                     "Disallow: /maps?\n"
                     "Disallow: /mapstt?\n"
                     "Disallow: /mapslt?\n"
                     "Disallow: /maps/stk/\n"
                     "Disallow: /mapabcpoi?\n"
                     "Disallow: /translate?\n"
                     "Disallow: /ie?\n"
                     "Disallow: /sms/demo?\n"
                     "Disallow: /katrina?\n"
                     "Disallow: /blogsearch?\n"
                     "Disallow: /blogsearch/\n"
                     "Disallow: /blogsearch_feeds\n"
                     "Disallow: /advanced_blog_search\n"
                     "Disallow: /reader/\n"
                     "Disallow: /uds/\n"
                     "Disallow: /chart?\n"
                     "Disallow: /transit?\n"
                     "Disallow: /mbd?\n"
                     "Disallow: /extern_js/\n"
                     "Disallow: /calendar/feeds/\n"
                     "Disallow: /calendar/ical/\n"
                     "Disallow: /cl2/feeds/\n"
                     "Disallow: /cl2/ical/\n"
                     "Disallow: /coop/directory\n"
                     "Disallow: /coop/manage\n"
                     "Disallow: /trends?\n"
                     "Disallow: /trends/music?\n"
                     "Disallow: /notebook/search?\n"
                     "Disallow: /music\n"
                     "Disallow: /browsersync\n"
                     "Disallow: /call\n"
                     "Disallow: /archivesearch?\n"
                     "Disallow: /archivesearch/url\n"
                     "Disallow: /archivesearch/advanced_search\n"
                     "Disallow: /base/search?\n"
                     "Disallow: /base/reportbadoffer\n"
                     "Disallow: /base/s2\n"
                     "Disallow: /urchin_test/\n"
                     "Disallow: /movies?\n"
                     "Disallow: /codesearch?\n"
                     "Disallow: /codesearch/feeds/search?\n"
                     "Disallow: /wapsearch?\n"
                     "Disallow: /safebrowsing\n"
                     "Disallow: /reviews/search?\n"
                     "Disallow: /orkut/albums\n"
                     "Disallow: /jsapi\n"
                     "Disallow: /views?\n"
                     "Disallow: /c/\n"
                     "Disallow: /cbk\n"
                     "Disallow: /recharge/dashboard/car\n"
                     "Disallow: /recharge/dashboard/static/\n"
                     "Disallow: /translate_c?\n"
                     "Disallow: /s2/profiles/me\n"
                     "Allow: /s2/profiles\n"
                     "Disallow: /s2\n"
                     "Disallow: /transconsole/portal/\n"
                     "Disallow: /gcc/\n"
                     "Disallow: /aclk\n"
                     "Disallow: /cse?\n"
                     "Disallow: /tbproxy/\n"
                     "Disallow: /MerchantSearchBeta/\n"
                     "Disallow: /ime/\n"
                     "Disallow: /websites?\n"
                     "Disallow: /shenghuo/search?\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/archivesearch?q=stalin&scoring=t&hl=en&sa=N&sugg=d&as_ldate=1900&as_hdate=1919&lnav=hist2", "reppy"))

    # Real world example
    def test_legacy_test_4(self):
        robots_txt = ( "User-agent: scooter\n"
                     "Disallow: /\n"
                     "\n"
                     "User-agent: wget\n"
                     "User-agent: webzip\n"
                     "Disallow: /\n"
                     "\n"
                     "User-agent: *\n"
                     "Disallow:\n" )
        rules = self.parse(robots_txt)
        self.assertTrue(rules.allowed("/index.html", "reppy"))

    # Real world example
    def test_legacy_test_5(self):
        robots_txt =  ( "# Alexa\n"
                      "User-agent: ia_archiver\n"
                      "Disallow: /utils/date_picker/\n"
                      "# Ask Jeeves\n"
                      "User-agent: Teoma\n"
                      "Disallow: /utils/date_picker/\n"
                      "# Google\n"
                      "User-agent: googlebot\n"
                      "Disallow: /utils/date_picker/\n"
                      "# MSN\n"
                      "User-agent: MSNBot\n"
                      "Disallow: /utils/date_picker/\n"
                      "# Yahoo!\n"
                      "User-agent: Slurp\n"
                      "Disallow: /utils/date_picker/\n"
                      "# Baidu\n"
                      "User-agent: baiduspider\n"
                      "Disallow: /utils/date_picker/\n"
                      "# All the rest go away\n"
                      "User-agent: *\n"
                      "Disallow: /\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/", "reppy"))

    # Real world example with multiple consecutive user agent directives
    def test_legacy_test_6(self):
        robots_txt = ( "User-agent: reppy\n"
                     "User-agent:snowball\n"
                     "Disallow:/\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/", "reppy"))

    # Real world example, r.e. phpBB
    def test_legacy_test_7(self):
        robots_txt = ( "User-agent: Googlebot-Image\n"
                     "Disallow: /\n"
                     "\n"
                     "User-agent: *\n"
                     "Crawl-delay: 7\n"
                     "\n"
                     "Disallow: /faq.php\n"
                     "Disallow: /groupcp.php\n"
                     "Disallow: /login.php\n"
                     "Disallow: /memberlist.php\n"
                     "Disallow: /merge.php\n"
                     "Disallow: /modcp.php\n"
                     "Disallow: /posting.php\n"
                     "Disallow: /phpBB2/posting.php\n"
                     "Disallow: /privmsg.php\n"
                     "Disallow: /profile.php\n"
                     "Disallow: /search.php\n"
                     "Disallow: /phpBB2/faq.php\n"
                     "Disallow: /phpBB2/groupcp.php\n"
                     "Disallow: /phpBB2/login.php\n"
                     "Disallow: /phpBB2/memberlist.php\n"
                     "Disallow: /phpBB2/merge.php\n"
                     "Disallow: /phpBB2/modcp.php\n"
                     "Disallow: /phpBB2/posting.php\n"
                     "Disallow: /phpBB2/posting.php\n"
                     "Disallow: /phpBB2/privmsg.php\n"
                     "Disallow: /phpBB2/profile.php\n"
                     "Disallow: /phpBB2/search.php\n"
                     "\n"
                     "Disallow: /admin/\n"
                     "Disallow: /images/\n"
                     "Disallow: /includes/\n"
                     "Disallow: /install/\n"
                     "Disallow: /modcp/\n"
                     "Disallow: /templates/\n"
                     "Disallow: /phpBB2/admin/\n"
                     "Disallow: /phpBB2/images/\n"
                     "Disallow: /phpBB2/includes/\n"
                     "Disallow: /phpBB2/install/\n"
                     "Disallow: /phpBB2/modcp/\n"
                     "Disallow: /phpBB2/templates/\n"
                     "\n"
                     "Disallow: /trac/\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/phpBB2/posting.php?mode=reply&t=895", "reppy"))

    # Is this pertinent to reppy, or would this have been sanitized by
    # the time it reaches the parsing stage?
    def test_utf8bom(self):
        robots_txt = ( "\357\273\277User-agent: *\n"
                     "Disallow: /Product/List\n"
                     "Disallow: /Product/Search\n"
                     "Disallow: /Product/TopSellers\n"
                     "Disallow: /Product/UploadImage\n"
                     "Disallow: /WheelPit\n"
                     "Disallow: /iwwida.pvx\n" )
        rules = self.parse(robots_txt)
        self.assertFalse(rules.allowed("/WheelPit", "reppy"))

