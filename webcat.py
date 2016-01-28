#!/usr/bin/env python
#
# webcat.py - URL categorization script
#
# Author: Xavier Mertens <xavier@rootshell.be>
# Copyright: GPLv3 (http://gplv3.fsf.org)
# Fell free to use the code, but please share the changes you've made
#
# Todo
# - Add proxy support
#

import os
import sys
import stat
import argparse
import errno
import urllib2
import json
import time
import ast
from xml.etree.cElementTree import fromstring
from json import dumps

# Configuration
categoriesFile = '/var/tmp/categories.txt'
categoriesUrl = 'http://sitereview.bluecoat.com/rest/categoryList?alpha=true'

# Get one here: http://www1.k9webprotection.com/get-k9-web-protection-free
k9License = 'Replace_by_your_own_license'

def fetchCategories(name):
	""" --------------------------------------- """
	""" Fetch categories and create local cache """
	""" --------------------------------------- """
	if not name:
		return None

	try:
		u = urllib2.build_opener()
		u.addheaders = [('User-agent', 'webcat.py/1.0 (https://blog.rootshell.be)')]
		r = u.open(categoriesUrl)
		data = json.load(r)
		d = dict([('%02x' % c['num'], c['name']) for c in data])
	except urllib2.HTTPError, e:
		sys.stderr.write('Cannot fetch categories, HTTP error: %s\n' % str(e.code))
	except urllib2.URLError, e:
		sys.stderr.write('Cannot fetch categories, URL error: %s\n' % str(e.reason))
	try:
		f = open(name, 'wb')
		f.write(dumps(d))
	except Exception, e:
		f.close()
		sys.stderr.write('Cannot save categories: %s\n' % e)
	return d

def loadCategories(name):
	""" --------------------------------- """
	""" Load categories from a cache file """
	""" --------------------------------- """
	if not name:
		return None
	d = {}
	try:
		f = open(name, 'r')
		data = f.read()
		d = ast.literal_eval(data)
		
	except Exception, e:
		f.close()
		sys.stderr.write('Cannot load categories: %s (use -F for force a fetch)\n' % e)
		exit(1)
	return d

def _chunks(s):
	# Original: https://github.com/allfro/sploitego/blob/master/src/sploitego/webtools/bluecoat.py
	return [s[i:i + 2] for i in range(0, len(s), 2)]

def main():
	parser = argparse.ArgumentParser(
		description = "Categorize URL using BlueCoat K9")
	parser.add_argument('urls', metavar='URL', nargs='*',
		help = 'the URL(s) to check. Format: fqdn[:port]')
	parser.add_argument('-f', '--file',
		dest = 'cacheFile',
		help = 'Categories local cache file (default: %s)' % categoriesFile,
		metavar = 'CACHEFILE')
	parser.add_argument('-F', '--force',
		action = 'store_true',
		dest = 'force',
		help = 'force a fetch of categories',
		default = False)
	args = parser.parse_args()

	if not args.cacheFile:
		args.cacheFile = categoriesFile

	# Read URLs from STDIN?
	if args.urls and args.urls[0] == '-':
		del args.urls[:]
		for u in sys.stdin:
			args.urls.append(u.rstrip())
		
	if not os.path.exists(args.cacheFile) or \
		(time.time() - os.stat(args.cacheFile)[stat.ST_MTIME]) > 7200 or \
		args.force:
		webCats = fetchCategories(args.cacheFile)
	else:
		webCats = loadCategories(args.cacheFile)

	for url in args.urls:
		if url.count(':') > 0:
			(hostname, port) = url.split(':')
		else:
			hostname = url
			port = '80'
		r = urllib2.urlopen('http://sp.cwfservice.net/1/R/%s/K9-00006/0/GET/HTTP/%s/%s///' % (k9License, hostname, port))
		if r.code == 200:
			e = fromstring(r.read())
			domc = e.find('DomC')
			dirc = e.find('DirC')
			if domc is not None:
				cats = _chunks(domc.text)
				sys.stdout.write('%s,%s\n' % (hostname, [webCats.get(c.lower(), 'Unknown') for c in cats][0]))
			elif dirc is not None:
				cats = _chunks(dirc.text)
				sys.stdout.write('%s,%s\n' % (hostname, [webCats.get(c.lower(), 'Unknown') for c in cats][0]))
		else:
			sys.stderr.write('Cannot get category for %s\n' % hostname)
	exit(0)

if __name__ == '__main__':
	main()
