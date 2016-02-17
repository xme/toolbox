#!/usr/bin/python
#
# pum.py - PaloAlto URL Manager
# (Tested against PA 7.0.1)
#
# TODO
# - Implement save & commit (using a flag?) [done]
# - Add proxy support
# - Check return code and handler potential errors [done]
# - Read list of URLs from stdin [done]
#
# Author: Xavier Mertens <xavier@rootshell.be>
# Copyright: GPLv3 (http://gplv3.fsf.org/)
# Feel free to use the code, but please share the changes you've made
#

import os
import sys
import argparse
import errno
import ConfigParser
import urllib2
import ssl
import xml.etree.ElementTree as ET
from urlparse import urlparse

verbose = False
config = {
	'sslCheck': True,
	'proxyHost': '',
	'proxyPort': '',
	'proxyUser': '',
	'proxyPass': '',
}

def getHTTP(url):
	""" ------------------------ """
	""" Fetch an URL via urllib2 """
	""" ------------------------ """
	if not url:
		return

	# Python 2.7 requires a ssl security context for self-signed certificates
	context = None
	if not config['sslCheck']:
		context = (hasattr(ssl, '_create_unverified_context')
			and ssl._create_unverified_context() or None)
	try:
		if context:
			r = urllib2.urlopen(url, context=context)
		else:
			r = urllib2.urlopen(url)
	except urllib2.URLError as e:
		sys.stderr.write("HTTP request failed: %s\n" % e.reason)
		return
	return(r.read())
	
def commitChanges(fw, key, partial):
	""" --------------------------------- """
	""" Commit the firewall configuration """
	""" --------------------------------- """
	if not fw or not key or not urlCategory:
		return

	if partial:
		if verbose: sys.stdout.write("+++ Saving firewall changes (partial)\n")
		req = "https://%s/api/?type=commit&action=partial&key=%s&cmd=<commit><partial><policy-and-objects></policy-and-objects></partial></commit>" % (fw, key)
	else:
		if verbose: sys.stdout.write("+++ Saving firewall changes (full)\n")
		req = "https://%s/api/?type=commit&key=%s&cmd=<commit></commit>" % (fw, key)
	data = getHTTP(req)
	if not data:
		return
	xml = ET.fromstring(data)
	# Sample
	# ------
	# <response code="19" status="success">
	# <result><msg><line>Commit job enqueued with jobid 4</line></msg><job>4</job></result></response>
	result = xml.find('msg')
	err_code = xml.get('code')
	err_status = xml.get('status')
	for i in xml.iter(tag='line'):
		err_msg = i.text.rstrip()
	if err_status != "sucess":
		sys.stdout.write("ERROR: Cannot commit: %s (code=%s)\n" % (err_msg, err_code))
	return

def listURLFromCategory(fw, key, urlCategory):
	""" ---------------------------------- """
	""" Fetch the URLs from a URL category """
	""" ---------------------------------- """
	if not fw or not key or not urlCategory:
		return

	if verbose: sys.stdout.write("+++ Fetching list of URLs for %s/%s\n" % (fw,urlCategory))

	req = "https://%s/api?/type=config&action=get&key=%s&xpath=/config/devices/entry/vsys/entry[@name=\"vsys1\"]/profiles/custom-url-category/entry[@name=\"%s\"]/list" % (fw, key, urlCategory)
	data = getHTTP(req)
	if not data:
		return
	root = ET.fromstring(data)
	# print ET.tostring(root)
	# Sample:
	# <response code="19" status="success"><result count="1" total-count="1">
	#  <list admin="api_admin" time="2015/12/22 10:01:46">
	#    <member admin="admin" time="2015/12/22 09:38:27">xxx</member>
	#    <member admin="admin" time="2015/12/22 09:38:27">aaa</member>
	#  </list>
	# </result></response>
	for child in root.iter('member'):
		print "{:19s} | {:s} | {:s} | {:s}".format(child.get('time'), fw, urlCategory, child.text)
	return

def addURLToCategory(fw, key, urlCategory, url):
	""" ------------------------------------------- """
	""" Add the specified URL from the URL category """
	""" ------------------------------------------- """
	if not url or not fw or not key or not urlCategory:
		return

	req = "https://%s/api?/type=config&action=set&key=%s&xpath=/config/devices/entry/vsys/entry[@name=\"vsys1\"]/profiles/custom-url-category/entry[@name=\"%s\"]/list&element=<member>%s</member>" % (fw, key, urlCategory, url)
	data = getHTTP(req)
	if not data:
		return
	xml = ET.fromstring(data)
	# print ET.tostring(xml)
	# CHECK RETURN CODE HERE
	if verbose: sys.stdout.write("+++ Added %s in %s\n" % (url, urlCategory))
	return

def deleteURLFromCategory(fw, key, urlCategory, url):
	""" ---------------------------------------------- """
	""" Remove the specified URL from the URL category """
	""" ---------------------------------------------- """
	if not fw or not key or not url or not urlCategory:
		return

	req = "https://%s/api/?type=config&action=delete&key=%s&xpath=/config/devices/entry/vsys/entry[@name=\"vsys1\"]/profiles/custom-url-category/entry[@name=\"%s\"]/list/member[text()=\"%s\"]" % (fw, key, urlCategory, url)
	data = getHTTP(req)
	if not data:
		return
        xml = ET.fromstring(data)
        # CHECK RETURN CODE HERE
	if verbose: sys.stdout.write("+++ Removed %s from %s\n" % (url, urlCategory))
	return

def main():
	global config
	global verbose
	global firewall
	global urlCategory

	parser = argparse.ArgumentParser(
		description="Manage custom URL categories in a Palo Alto Networks firewall")
	parser.add_argument('urls', metavar='URL', nargs='*',
                   help='the URL(s) to add/remove (format is IP/FQDN)')
	parser.add_argument('-f', '--firewall', metavar='FIREWALL', nargs='+',
		dest = 'firewallHost',
		help = 'firewall IP address or hostname')
	parser.add_argument('-c', '--config',
		dest = 'configFile',
		help = 'configuration file (default: /etc/pum.conf)',
		metavar = 'CONFIGFILE')
	parser.add_argument('-u', '--url-category',
		dest = 'urlCategory',
		help = 'custom URL category to manage',
		metavar = 'URLCATEGORY')
	parser.add_argument('-n', '--no-ssl-verification',
		action = 'store_true',
		dest = 'sslCheck',
		help = 'ignore SSL certificate errors',
		default = False)
	parser.add_argument('-v', '--verbose',
		action = 'store_true',
		dest = 'verbose',
		help = 'enable verbose output',
		default = False)
	parser.add_argument('-s', '--save',
		action = 'store_true',
		dest = 'commit',
		help = 'commit the configuration (save)',
		default = False)
	parser.add_argument('-p', '--partial',
		action = 'store_true',
		dest = 'partial',
		help = 'perform a partial commit (objects only)',
		default = False)
	group = parser.add_mutually_exclusive_group()
	group.add_argument('-l', '--list',
		action = 'store_true',
		dest = 'commandList',
		help = 'list URLs from the custom URL category',
		default = False)
	group.add_argument('-a', '--add',
		action = 'store_true',
		dest = 'commandAdd',
		help = 'add the URL(s) to the custom URL category',
		default = False)
	group.add_argument('-d', '--delete',
		action = 'store_true',
		dest = 'commandDelete',
		help = 'remove the URL(s) from the custom URL category',
		default = False)
	args = parser.parse_args()

	if args.verbose:
		verbose = True
		sys.stdout.write("+++ Verbose output enabled\n")

	# If the URL provided is a dash ("-") we read the URLs from STDIN
	# and populare the list.
	if args.urls and args.urls[0] == "-": 
		del args.urls[:]
		for u in sys.stdin:
			args.urls.append(u.rstrip())

	# ----------------------------------------
	# Main loop - processing all the firewalls
	# ----------------------------------------
	for fw in args.firewallHost:
		if verbose: sys.stdout.write("+++ Processing firewall %s\n" % fw)
	
		if not args.configFile:
			# Overwrie default configuration
			args.configFile = '/etc/pum.conf'

		# Process configuration file
		try:
			c = ConfigParser.ConfigParser()
			c.read(args.configFile)
			try:
				apiKey = c.get(fw, 'apikey')
				urlCategory = c.get(fw, 'urlcategory')
			except:
				sys.stderr.write("Cannot read configuration for %s (%s)\n" % (fw, args.configFile))
				exit(1)
		except OSError, e:
			sys.stderr.write('Cannot read config file %s: %s' % (args.configFile, e.errno))
			exit(1)

		if args.urlCategory:
			# Overwrite default configuration
			urlCategory = args.urlCategory

		if args.sslCheck:
			config['sslCheck'] = False
			if verbose: sys.stdout.write("+++ WARNING: SSL certificate check disabled\n")

		if args.commandList:
			listURLFromCategory(fw, apiKey, urlCategory)
		else:
			for url in args.urls:
				# Validate the URL format
				# URls must be:
				# www.hostname.tld[/bar]
				# x.x.x.x[/foo]
				# No "http(s)://"!
				url = url.lower().rstrip()
				if not url.startswith('http:'):
					url = 'http://' + url
				d = urlparse(url)
				if not d.netloc:
					sys.stderr.write("Bad URL format: %s (rejected)\n" % url)
					continue
				if args.commandAdd:
					addURLToCategory(fw, apiKey, urlCategory, d.netloc)
				else:
					deleteURLFromCategory(fw, apiKey, urlCategory, d.netloc)

		if args.commit:
			commitChanges(fw, apiKey, args.partial)

	exit(0)

if __name__ == "__main__":
	main()
