#!/usr/bin/python
#
# getgithublog.py
#
# Download security logs from a GitHub account
# Run this script from a crontab at regular interval to get new events
#
# Modules dependencies:
# - netsyslog
# - mechanize
# - BeautifulSoup
#
# Author: Xavier Mertens <xavier@rootshell.be>
# Copyright: GPLv3 (http://gplv3.fsf.org/)
# Feel free to use the code, but please share the changes you've made
# 

import os
import sys
import time
import mechanize
import ConfigParser
import socket
import netsyslog
import syslog
from optparse import OptionParser
from BeautifulSoup import BeautifulSoup
from mechanize._opener import urlopen
from logging.handlers import SysLogHandler

# Don't change this URL!
githubUrl = "https://github.com/settings/security"
debug = 0
syslogServer = ""

def readEventIndex(statusFile):
	try:
		fd = open(statusFile, "rb")
		data = fd.read()
		fd.close()
		if (data == ""):
			return(0)
		return(int(data))
	except IOError as e:
		if debug: print "Warning: Cannot open %s (%s)" % (statusFile, e.strerror)
		return(0)

def writeEventIndex(statusFile, index):
	try:
		fd = open(statusFile, "wb")
		fd.write("%d" % index)
		fd.close()
	except IOError as e:
		print "Cannot write %s (%s)" % (statusFile, e.strerror)

def writeLog(attributes):
	i = 0
        buf = ""
	for attr in attributes:
		if i > 0:
			buf += ","
		buf += attr
		i += 1
	if syslogServer != "":
		logger = netsyslog.Logger()
		logger.add_host(syslogServer)
		# Bug in netsyslog?
		buf = ": " + buf
		logger.log(syslog.LOG_USER, syslog.LOG_NOTICE, buf, pid=True)
	else:
		print buf

def main(argv):
	global debug
	global syslogServer

	parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
	parser.add_option('-u', '--user', dest='githubUser', type='string',
		help='github.com user name')
	parser.add_option('-p', '--password', dest='githubPass', type='string',
		help='github.com password')
	parser.add_option('-s', '--statusfile', dest='statusFile', type='string',
		help='status file for event history')
	parser.add_option('-S', '--syslog', dest='syslogServer', type='string',
		help='send Syslog messages to specified server')
	parser.add_option('-d', '--debug', action='store_true', dest='debug', \
		help='increase verbosity')
	(options, args) = parser.parse_args()

	if options.debug:
		debug = 1
		print "+++ Debug mode"

	if options.githubUser == None:
		print "Please use the -u switch to provide a github login"
		sys.exit(1)

	if options.githubPass == None:
		print "Please use the -p switch to provide a password"
		sys.exit(1)

	syslogServer = options.syslogServer
	try:
		socket.gethostbyname(syslogServer)
	except socket.error as e:
		print "Invalid Syslog server: %s" % e
		sys.exit(1)

	if options.debug: print "+++ Sending Syslog events to %s" % syslogServer

	if options.statusFile == None:
		statusFile = "~/.github.status"
	else:
		statusFile = options.statusFile
	if not os.path.isfile(statusFile):
		print "Status file %s does not exist" % statusFile
		sys.exit(1)
	if options.debug: print "+++ Using status file: %s" % statusFile

	request = mechanize.Request(githubUrl)
	try:
		if options.debug: print "+++ Connecting to github.com"
		response = mechanize.urlopen(request)
	except (mechanize.HTTPError,mechanize.URLError) as e:
		if isinstance(e, mechanize.HTTPError):
			print "Cannot fetch URL, returned code: %d" % e.code
			sys.exit(1)
		else:
			print "Cannot connect to URL: %s" % e.reason.args[1]
			sys.exit(1)

	forms = mechanize.ParseResponse(response, backwards_compat=False)

	form = forms[1]
	form["login"] = options.githubUser
	form["password"] = options.githubPass
	htmlData = urlopen(form.click()).read () 

	# Successful login or not?
	if htmlData.find("Incorrect username or password") != -1:
		print "Access denied, please check the provided credentials"
		sys.exit(1)

	# Maximum number of logins attemps?
	if htmlData.find("maximum number of login attempts") != -1:
		print "github.com said: maximum number of login attempts, try again later"
		sys.exit(1)

	if options.debug: print "+++ Authentication successful, collecing security logs"
	soup = BeautifulSoup(htmlData)
	ul=soup.find('ul', { "class" : "boxed-group-list security-history" })
	lis=ul.findAll('li')

	# Event Sample:
	# <li>
	#   <time class="js-relative-date" datetime="xxxx" title="xxxx">xxxx</time>
	#   <a href="#security-history-8" rel="facebox" class="mute">
	#     <strong>repo.add_member</strong>: Add xxxx to xxxx/xxxx
	#   </a>
	# <div id="security-history-8" style="display:none">
	#  <h2>repo.add_member: xxxx/xxxx</h2>
	#   <div class="markdown-body">
	#     <table class="security-history-detail">
	#       <tr><th>actor</th><td>xxxx</td></tr>
	#       <tr><th>actor_ip</th><td>xxxx</td></tr>
	#       <tr><th>created_at</th><td>xxxx</td></tr>
	#       <tr><th>repo</th><td>xxxx</td></tr>
	#       <tr><th>user</th><td>xxxx</td></tr>
	#     </table>
	#   </div>
	# </div>

	firstEpoch = readEventIndex(statusFile)
	if options.debug: print "+++ Last event epoch: %s" % firstEpoch
	newEpoch = 0
	eventCounter=0
	for li in lis:
		eventAttributes = []
		u = li.find('h2')
		eventName = u.string
		eventAttributes.append("\"event\":\"%s\"" % (eventName))
		trs = li.findAll('tr')
		for tr in trs:
			th = tr.find('th')
			td = tr.find('td')
			if th.string == 'created_at':
				# 2012-03-07 11:44:59
				pattern = '%Y-%m-%d %H:%M:%S'
				eventEpoch = int(time.mktime(time.strptime(td.string, pattern)))
			eventAttributes.append("\"%s\":\"%s\"" % (th.string, td.string))

		if (firstEpoch < eventEpoch):
			writeLog(eventAttributes)
		if (eventCounter == 0):
			newEpoch = eventEpoch
		eventCounter = eventCounter + 1

	writeEventIndex(statusFile, newEpoch)

if __name__ == '__main__':
	main(sys.argv[1:])
	sys.exit()
