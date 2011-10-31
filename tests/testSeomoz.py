#! /usr/bin/env python

'''These are unit tests derived from the REP parser from linkscape'''

import os
import sys

sys.path.append(os.path.abspath('..'))

import reppy
import random
import unittest

import logging
reppy.logger.setLevel(logging.FATAL)

class TestReppyRFC(unittest.TestCase):
	def test_www_seomoz_org(self):
		r = reppy.parse('''
			User-agent: *
			Disallow: /blogdetail.php?ID=537
			Disallow: /tracker

			Sitemap: http://www.seomoz.org/sitemap.xml.gz
			Sitemap: http://files.wistia.com/sitemaps/seomoz_video_sitemap.xml''')
		ua = 'dotbot'
		self.assertTrue(    r.allowed('/blog', ua))
		self.assertTrue(not r.allowed('/blogdetail.php?ID=537', ua))
		self.assertTrue(not r.allowed('/tracker', ua))
		ua = 'DoTbOt'
		self.assertTrue(    r.allowed('/blog', ua))
		self.assertTrue(not r.allowed('/blogdetail.php?ID=537', ua))
		self.assertTrue(not r.allowed('/tracker', ua))
		
	def test_allow_all(self):
		# Now test escaping entities
		r = reppy.parse('''
			User-agent: *
			Disallow:  ''')
		ua = 'dotbot'
		self.assertTrue(    r.allowed('/', ua))
		self.assertTrue(    r.allowed('/foo', ua))
		self.assertTrue(    r.allowed('/foo.html', ua))
		self.assertTrue(    r.allowed('/foo/bar', ua))
		self.assertTrue(    r.allowed('/foo/bar.html', ua))
		ua = 'oijsdofijsdofijsodifj'
		self.assertTrue(    r.allowed('/', ua))
		self.assertTrue(    r.allowed('/foo', ua))
		self.assertTrue(    r.allowed('/foo.html', ua))
		self.assertTrue(    r.allowed('/foo/bar', ua))
		self.assertTrue(    r.allowed('/foo/bar.html', ua))
		
	def test_disallow_all(self):
		# But not with foward slash
		r = reppy.parse('''
			User-agent: *
			Disallow: /''')
		ua = 'dotbot'
		self.assertTrue(not r.allowed('/', ua))
		self.assertTrue(not r.allowed('/foo', ua))
		self.assertTrue(not r.allowed('/foo.html', ua))
		self.assertTrue(not r.allowed('/foo/bar', ua))
		self.assertTrue(not r.allowed('/foo/bar.html', ua))
		ua = 'oijsdofijsdofijsodifj'
		self.assertTrue(not r.allowed('/', ua))
		self.assertTrue(not r.allowed('/foo', ua))
		self.assertTrue(not r.allowed('/foo.html', ua))
		self.assertTrue(not r.allowed('/foo/bar', ua))
		self.assertTrue(not r.allowed('/foo/bar.html', ua))
	
	def test_no_googlebot_folder(self):
		r = reppy.parse('''
			User-agent: Googlebot
			Disallow: /no-google/''')
		ua = 'googlebot'
		self.assertTrue(not r.allowed('/no-google/', ua))
		self.assertTrue(not r.allowed('/no-google/something', ua))
		self.assertTrue(not r.allowed('/no-google/something.html', ua))
		self.assertTrue(    r.allowed('/', ua))
		self.assertTrue(    r.allowed('/somethingelse', ua))
	
	def test_no_googlebot_file(self):
		r = reppy.parse('''
			User-agent: Googlebot
			Disallow: /no-google/blocked-page.html''')
		ua = 'googlebot'
		self.assertTrue(    r.allowed('/', ua))
		self.assertTrue(    r.allowed('/no-google/someotherfolder', ua))
		self.assertTrue(    r.allowed('/no-google/someotherfolder/somefile', ua))
		self.assertTrue(not r.allowed('/no-google/blocked-page.html', ua))
	
	def test_rogerbot_only(self):
		r = reppy.parse('''
			User-agent: *
			Disallow: /no-bots/block-all-bots-except-rogerbot-page.html

			User-agent: rogerbot
			Allow: /no-bots/block-all-bots-except-rogerbot-page.html''')
		ua = 'notroger'
		self.assertTrue(not r.allowed('/no-bots/block-all-bots-except-rogerbot-page.html', ua))
		self.assertTrue(    r.allowed('/', ua))
		ua = 'rogerbot'
		self.assertTrue(    r.allowed('/no-bots/block-all-bots-except-rogerbot-page.html', ua))
		self.assertTrue(    r.allowed('/', ua))
	
	def test_allow_certain_pages_only(self):
		r = reppy.parse('''
			User-agent: *
			Allow: /onepage.html
			Allow: /oneotherpage.php
			Disallow: /
			Allow: /subfolder/page1.html
			Allow: /subfolder/page2.php
			Disallow: /subfolder/''')
		ua = 'dotbot'
		self.assertTrue(not r.allowed('/', ua))
		self.assertTrue(not r.allowed('/foo', ua))
		self.assertTrue(not r.allowed('/bar.html', ua))
		self.assertTrue(    r.allowed('/onepage.html', ua))
		self.assertTrue(    r.allowed('/oneotherpage.php', ua))
		self.assertTrue(not r.allowed('/subfolder', ua))
		self.assertTrue(not r.allowed('/subfolder/', ua))
		self.assertTrue(not r.allowed('/subfolder/aaaaa', ua))
		self.assertTrue(    r.allowed('/subfolder/page1.html', ua))
		self.assertTrue(    r.allowed('/subfolder/page2.php', ua))
	
	def test_no_gifs_or_jpgs(self):
		r = reppy.parse('''
			User-agent: *
			Disallow: /*.gif$
			Disallow: /*.jpg$''')
		ua = 'dotbot'
		self.assertTrue(    r.allowed('/', ua))
		self.assertTrue(    r.allowed('/foo', ua))
		self.assertTrue(    r.allowed('/foo.html', ua))
		self.assertTrue(    r.allowed('/foo/bar', ua))
		self.assertTrue(    r.allowed('/foo/bar.html', ua))
		self.assertTrue(not r.allowed('/test.jpg', ua))
		self.assertTrue(not r.allowed('/foo/test.jpg', ua))
		self.assertTrue(not r.allowed('/foo/bar/test.jpg', ua))
		self.assertTrue(    r.allowed('/the-jpg-extension-is-awesome.html', ua))
		self.assertTrue(not r.allowed('/jpg.jpg', ua))
		self.assertTrue(not r.allowed('/foojpg.jpg', ua))
		self.assertTrue(not r.allowed('/bar/foojpg.jpg', ua))
		self.assertTrue(not r.allowed('/.jpg.jpg', ua))
		self.assertTrue(not r.allowed('/.jpg/.jpg', ua))
		self.assertTrue(not r.allowed('/test.gif', ua))
		self.assertTrue(not r.allowed('/foo/test.gif', ua))
		self.assertTrue(not r.allowed('/foo/bar/test.gif', ua))
		self.assertTrue(    r.allowed('/the-gif-extension-is-awesome.html', ua))
	
	def test_block_subdirectory_wildcard(self):
		r = reppy.parse('''
			User-agent: *
			Disallow: /private*/''')
		ua = 'dotbot'
		self.assertTrue(    r.allowed('/', ua))
		self.assertTrue(    r.allowed('/foo', ua))
		self.assertTrue(    r.allowed('/foo.html', ua))
		self.assertTrue(    r.allowed('/foo/bar', ua))
		self.assertTrue(    r.allowed('/foo/bar.html', ua))
		self.assertTrue(    r.allowed('/private', ua))
		self.assertTrue(    r.allowed('/privates', ua))
		self.assertTrue(    r.allowed('/privatedir', ua))
		self.assertTrue(not r.allowed('/private/', ua))
		self.assertTrue(not r.allowed('/private/foo', ua))
		self.assertTrue(not r.allowed('/private/foo/bar.html', ua))
		self.assertTrue(not r.allowed('/privates/', ua))
		self.assertTrue(not r.allowed('/privates/foo', ua))
		self.assertTrue(not r.allowed('/privates/foo/bar.html', ua))
		self.assertTrue(not r.allowed('/privatedir/', ua))
		self.assertTrue(not r.allowed('/privatedir/foo', ua))
		self.assertTrue(not r.allowed('/privatedir/foo/bar.html', ua))
	
	def test_block_urls_with_question_marks(self):
		r = reppy.parse('''
			User-agent: *
			Disallow: /*?''')
		ua = 'dotbot'
		self.assertTrue(    r.allowed('/', ua))
		self.assertTrue(    r.allowed('/foo', ua))
		self.assertTrue(    r.allowed('/foo.html', ua))
		self.assertTrue(    r.allowed('/foo/bar', ua))
		self.assertTrue(    r.allowed('/foo/bar.html', ua))
		self.assertTrue(not r.allowed('/?', ua))
		self.assertTrue(not r.allowed('/foo?q=param', ua))
		self.assertTrue(not r.allowed('/foo.html?q=param', ua))
		self.assertTrue(not r.allowed('/foo/bar?q=param', ua))
		self.assertTrue(not r.allowed('/foo/bar.html?q=param&bar=baz', ua))
	
	def test_no_question_except_at_end(self):
		r = reppy.parse('''
			User-agent: *
			Allow: /*?$
			Disallow: /*?''')
		ua = 'dotbot'
		self.assertTrue(    r.allowed('/', ua))
		self.assertTrue(    r.allowed('/foo', ua))
		self.assertTrue(    r.allowed('/foo.html', ua))
		self.assertTrue(    r.allowed('/foo/bar', ua))
		self.assertTrue(    r.allowed('/foo/bar.html', ua))
		self.assertTrue(    r.allowed('/?', ua))
		self.assertTrue(    r.allowed('/foo/bar.html?', ua))
		self.assertTrue(not r.allowed('/foo?q=param', ua))
		self.assertTrue(not r.allowed('/foo.html?q=param', ua))
		self.assertTrue(not r.allowed('/foo/bar?q=param', ua))
		self.assertTrue(not r.allowed('/foo/bar.html?q=param&bar=baz', ua))
	
	def test_wildcard_edge_cases(self):
		r = reppy.parse('''
			User-agent: *
			Disallow: /*one
			Disallow: /two*three
			Disallow: /irrelevant/four*five
			Disallow: /six*
			Disallow: /foo/*/seven*/eight*nine
			Disallow: /foo/*/*ten$

			Disallow: /*products/default.aspx
			Disallow: /*/feed/$''')
		ua = 'dotbot'
		self.assertTrue(    r.allowed('/', ua))
		self.assertTrue(    r.allowed('/foo', ua))
		self.assertTrue(    r.allowed('/foo.html', ua))
		self.assertTrue(    r.allowed('/foo/bar', ua))
		self.assertTrue(    r.allowed('/foo/bar.html', ua))
		self.assertTrue(not r.allowed('/one', ua))
		self.assertTrue(not r.allowed('/aaaone', ua))
		self.assertTrue(not r.allowed('/aaaaoneaaa', ua))
		self.assertTrue(not r.allowed('/oneaaaa', ua))
		self.assertTrue(not r.allowed('/twothree', ua))
		self.assertTrue(not r.allowed('/twoaaathree', ua))
		self.assertTrue(not r.allowed('/twoaaaathreeaaa', ua))
		self.assertTrue(not r.allowed('/twothreeaaa', ua))
		self.assertTrue(not r.allowed('/irrelevant/fourfive', ua))
		self.assertTrue(not r.allowed('/irrelevant/fouraaaafive', ua))
		self.assertTrue(not r.allowed('/irrelevant/fouraaafiveaaaa', ua))
		self.assertTrue(not r.allowed('/irrelevant/fourfiveaaa', ua))
		self.assertTrue(not r.allowed('/six', ua))
		self.assertTrue(not r.allowed('/sixaaaa', ua))
		self.assertTrue(not r.allowed('/foo/aaa/seven/eightnine', ua))
		self.assertTrue(not r.allowed('/foo/aaa/seventeen/eightteennineteen', ua))
		self.assertTrue(not r.allowed('/foo/aaa/ten', ua))
		self.assertTrue(not r.allowed('/foo/bbb/often', ua))
		self.assertTrue(    r.allowed('/foo/aaa/tenaciousd', ua))
		self.assertTrue(not r.allowed('/products/default.aspx', ua))
		self.assertTrue(not r.allowed('/author/admin/feed/', ua))
	
	def test_allow_edge_cases(self):
		r = reppy.parse('''
			User-agent: *
			Disallow:	/somereallylongfolder/
			Allow:		/*.jpg

			Disallow:	/sales-secrets.php
			Allow: 		/sales-secrets.php

			Disallow:	/folder
			Allow:		/folder/

			Allow:		/folder2
			Disallow:	/folder2/''')
		ua = 'dotbot'
		self.assertTrue(not r.allowed('/somereallylongfolder/', ua))
		self.assertTrue(not r.allowed('/somereallylongfolder/aaaa', ua))
		self.assertTrue(not r.allowed('/somereallylongfolder/test.jpg', ua))
		self.assertTrue(    r.allowed('/sales-secrets.php', ua))
		self.assertTrue(    r.allowed('/folder/page', ua))
		self.assertTrue(    r.allowed('/folder/page2', ua))
	
	def test_redundant_allow(self):
		r = reppy.parse('''
			User-agent: *
			Disallow: /en/
			Disallow: /files/documentation/
			Disallow: /files/
			Disallow: /de/careers/
			Disallow: /images/

			Disallow: /print_mode.yes/
			Disallow: /?product=lutensit&print_mode=yes&googlebot=nocrawl
			Allow: /
			Disallow: /search/''')
		ua = 'dotbot'
		self.assertTrue(not r.allowed('/print_mode.yes/', ua))
		self.assertTrue(not r.allowed('/print_mode.yes/foo', ua))
		self.assertTrue(not r.allowed('/search/', ua))
		self.assertTrue(not r.allowed('/search/foo', ua))
	
	def test_legacy(self):
		r = reppy.parse('''
			user-agent: *  #a comment!
			disallow: /Blerf
			disallow: /Blerg$
			disallow: /blerf/*/print.html$#a comment
			disallow: /blerf/*/blim/blerf$
			disallow: /plerf/*/blim/blim$
				user-agent: BLERF
			    DisALLOW: 	blerfPage
			blerf:blah''')
		ua = 'dotbot'
		self.assertTrue(not r.allowed('/Blerf/blah', ua))
		self.assertTrue(    r.allowed('/Blerg/blah', ua))
		self.assertTrue(    r.allowed('/blerf/blah', ua))
		self.assertTrue(not r.allowed('/Blerg', ua))
		self.assertTrue(not r.allowed('/blerf/some/subdirs/print.html', ua))
		self.assertTrue(    r.allowed('/blerf/some/subdirs/print.html?extra=stuff', ua))
		self.assertTrue(not r.allowed('/blerf/some/sub/dirs/blim/blim/blerf', ua))
		self.assertTrue(not r.allowed('/plerf/some/sub/dirs/blim/blim', ua))
		
		r = reppy.parse('''
			User-agent: *
			Allow: /searchhistory/
			Disallow: /news?output=xhtml&
			Allow: /news?output=xhtml
			Disallow: /search
			Disallow: /groups
			Disallow: /images
			Disallow: /catalogs
			Disallow: /catalogues
			Disallow: /news
			Disallow: /nwshp
			Allow: /news?btcid=
			Disallow: /news?btcid=*&
			Allow: /news?btaid=
			Disallow: /news?btaid=*&
			Disallow: /?
			Disallow: /addurl/image?
			Disallow: /pagead/
			Disallow: /relpage/
			Disallow: /relcontent
			Disallow: /sorry/
			Disallow: /imgres
			Disallow: /keyword/
			Disallow: /u/
			Disallow: /univ/
			Disallow: /cobrand
			Disallow: /custom
			Disallow: /advanced_group_search
			Disallow: /advanced_search
			Disallow: /googlesite
			Disallow: /preferences
			Disallow: /setprefs
			Disallow: /swr
			Disallow: /url
			Disallow: /default
			Disallow: /m?
			Disallow: /m/?
			Disallow: /m/lcb
			Disallow: /m/search?
			Disallow: /wml?
			Disallow: /wml/?
			Disallow: /wml/search?
			Disallow: /xhtml?
			Disallow: /xhtml/?
			Disallow: /xhtml/search?
			Disallow: /xml?
			Disallow: /imode?
			Disallow: /imode/?
			Disallow: /imode/search?
			Disallow: /jsky?
			Disallow: /jsky/?
			Disallow: /jsky/search?
			Disallow: /pda?
			Disallow: /pda/?
			Disallow: /pda/search?
			Disallow: /sprint_xhtml
			Disallow: /sprint_wml
			Disallow: /pqa
			Disallow: /palm
			Disallow: /gwt/
			Disallow: /purchases
			Disallow: /hws
			Disallow: /bsd?
			Disallow: /linux?
			Disallow: /mac?
			Disallow: /microsoft?
			Disallow: /unclesam?
			Disallow: /answers/search?q=
			Disallow: /local?
			Disallow: /local_url
			Disallow: /froogle?
			Disallow: /products?
			Disallow: /froogle_
			Disallow: /product_
			Disallow: /products_
			Disallow: /print
			Disallow: /books
			Disallow: /patents?
			Disallow: /scholar?
			Disallow: /complete
			Disallow: /sponsoredlinks
			Disallow: /videosearch?
			Disallow: /videopreview?
			Disallow: /videoprograminfo?
			Disallow: /maps?
			Disallow: /mapstt?
			Disallow: /mapslt?
			Disallow: /maps/stk/
			Disallow: /mapabcpoi?
			Disallow: /translate?
			Disallow: /ie?
			Disallow: /sms/demo?
			Disallow: /katrina?
			Disallow: /blogsearch?
			Disallow: /blogsearch/
			Disallow: /blogsearch_feeds
			Disallow: /advanced_blog_search
			Disallow: /reader/
			Disallow: /uds/
			Disallow: /chart?
			Disallow: /transit?
			Disallow: /mbd?
			Disallow: /extern_js/
			Disallow: /calendar/feeds/
			Disallow: /calendar/ical/
			Disallow: /cl2/feeds/
			Disallow: /cl2/ical/
			Disallow: /coop/directory
			Disallow: /coop/manage
			Disallow: /trends?
			Disallow: /trends/music?
			Disallow: /notebook/search?
			Disallow: /music
			Disallow: /browsersync
			Disallow: /call
			Disallow: /archivesearch?
			Disallow: /archivesearch/url
			Disallow: /archivesearch/advanced_search
			Disallow: /base/search?
			Disallow: /base/reportbadoffer
			Disallow: /base/s2
			Disallow: /urchin_test/
			Disallow: /movies?
			Disallow: /codesearch?
			Disallow: /codesearch/feeds/search?
			Disallow: /wapsearch?
			Disallow: /safebrowsing
			Disallow: /reviews/search?
			Disallow: /orkut/albums
			Disallow: /jsapi
			Disallow: /views?
			Disallow: /c/
			Disallow: /cbk
			Disallow: /recharge/dashboard/car
			Disallow: /recharge/dashboard/static/
			Disallow: /translate_c?
			Disallow: /s2/profiles/me
			Allow: /s2/profiles
			Disallow: /s2
			Disallow: /transconsole/portal/
			Disallow: /gcc/
			Disallow: /aclk
			Disallow: /cse?
			Disallow: /tbproxy/
			Disallow: /MerchantSearchBeta/
			Disallow: /ime/
			Disallow: /websites?
			Disallow: /shenghuo/search?''')
		self.assertTrue(not r.allowed('/?as_q=ethics&ie=UTF-8&ui=blg&bl_url=centrerion.blogspot.com&x=0&y=0&ui=blg', ua))
		self.assertTrue(not r.allowed('/archivesearch?q=stalin&scoring=t&hl=en&sa=N&sugg=d&as_ldate=1900&as_hdate=1919&lnav=hist2', ua))
		
		r = reppy.parse('''
			User-agent: scooter
			Disallow: /

			User-agent: wget
			User-agent: webzip
			Disallow: /

			User-agent: *
			Disallow:''')
		self.assertTrue(    r.allowed('/index.html', ua))
		
		r = reppy.parse('''
			# Alexa
			User-agent: ia_archiver
			Disallow: /utils/date_picker/
			# Ask Jeeves
			User-agent: Teoma
			Disallow: /utils/date_picker/
			# Google
			User-agent: googlebot
			Disallow: /utils/date_picker/
			# MSN
			User-agent: MSNBot
			Disallow: /utils/date_picker/
			# Yahoo!
			User-agent: Slurp
			Disallow: /utils/date_picker/
			# Baidu
			User-agent: baiduspider
			Disallow: /utils/date_picker/
			# All the rest go away
			User-agent: *
			Disallow: /''')
		self.assertTrue(not r.allowed('/', ua))
		
		r = reppy.parse('''
			User-agent: dotbot
			User-agent:snowball
			Disallow:/''')
		self.assertTrue(not r.allowed('/', ua))
		
		r = reppy.parse('''
			User-agent: Googlebot-Image
			Disallow: /
			User-agent: *
			Crawl-delay: 7
			Disallow: /faq.php
			Disallow: /groupcp.php
			Disallow: /login.php
			Disallow: /memberlist.php
			Disallow: /merge.php
			Disallow: /modcp.php
			Disallow: /posting.php
			Disallow: /phpBB2/posting.php
			Disallow: /privmsg.php
			Disallow: /profile.php
			Disallow: /search.php
			Disallow: /phpBB2/faq.php
			Disallow: /phpBB2/groupcp.php
			Disallow: /phpBB2/login.php
			Disallow: /phpBB2/memberlist.php
			Disallow: /phpBB2/merge.php
			Disallow: /phpBB2/modcp.php
			Disallow: /phpBB2/posting.php
			Disallow: /phpBB2/posting.php
			Disallow: /phpBB2/privmsg.php
			Disallow: /phpBB2/profile.php
			Disallow: /phpBB2/search.php
			Disallow: /admin/
			Disallow: /images/
			Disallow: /includes/
			Disallow: /install/
			Disallow: /modcp/
			Disallow: /templates/
			Disallow: /phpBB2/admin/
			Disallow: /phpBB2/images/
			Disallow: /phpBB2/includes/
			Disallow: /phpBB2/install/
			Disallow: /phpBB2/modcp/
			Disallow: /phpBB2/templates/
			Disallow: /trac/''')
		self.assertTrue(not r.allowed('/phpBB2/posting.php?mode=reply&t=895', ua))
		
		r = reppy.parse('''
			User-agent: *
			Disallow: /Product/List
			Disallow: /Product/Search
			Disallow: /Product/TopSellers
			Disallow: /Product/UploadImage
			Disallow: /WheelPit
			Disallow: /iwwida.pvx''')
		self.assertTrue(not r.allowed('/WheelPit', ua))

if __name__ == '__main__':
	unittest.main()
