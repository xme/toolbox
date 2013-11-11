#!/usr/bin/python
import argparse
import ConfigParser
import os
import pycurl
import signal
import sys
import StringIO
from base64 import b64encode
from optparse import OptionParser

global debug
global configFile
debug = 0
configFile = './post.conf'

def handler(signal, frame):
	print "CTRL-C detected!"
	sys.exit(0)

def main(argv):
	global dataFile
	global configFile
	global requestSoapAction
	requestSoapAction = ""

	parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
	parser.add_option('-c', '--config', dest='configFile', type='string', \
		help='Specify the configuration file')
	parser.add_option('-f', '--file', dest='dataFile', type='string', \
		help='Data to post to target')
	parser.add_option('-u', '--url', dest='URL', type='string', \
		help='Target URL')
	parser.add_option('-d', '--debug', action='store_true', dest='debug', \
                help='Increase verbosiry', default='False')
	(options, args) = parser.parse_args()

	if options.debug == True:
		print "+++ Debug mode"
		debug = 1

	if options.configFile == None:
                if not os.path.isfile(configFile):
                        print '+++ Cannot open ' + configFile + '. Use the -c switch to provide a valid configuration.'
                        sys.exit(1)
        else:
                configFile = options.configFile

	try:
		config = ConfigParser.ConfigParser()
		config.read(configFile)

		# Mandatory parameters
		proxyHost = config.get('proxy', 'host')
		proxyPort = config.get('proxy', 'port')
		proxyProtocol = config.get('proxy', 'protocol')
		requestUA = config.get('request', 'user-agent')
		requestType = config.get('request', 'content-type')
		requestUser = config.get('request', 'username')
		requestPass = config.get('request', 'password')
		if debug:
			print '+++ Using Configuration file:', configFile
			print "+++ Using proxy: %s:%s" % (proxyHost, proxyPort)
			print "+++ User-Agent:", requestUA
			print "+++ Content-Type:", requestType
	except:
		print '+++ Cannot process config file', configFile
		sys.exit(1)

	# Optional parameters
	try:
		requestSoapAction = config.get('request', 'soapaction')
		if debug: print "+++ Using SoapAction: %s" % requestSoapAction
	except:
		pass

	if options.dataFile == None:
		print "+++ A filename must be provided using the -f switch."
		sys.exit(1)
	else:
		dataFile = options.dataFile
		try:
			f = open(dataFile, 'rb')
			filesize = os.path.getsize(dataFile)
		except:
			print '+++ Cannot open datafile', dataFile
			sys.exit(1)
		
	if debug: print '+++ Using data file:', dataFile

	if options.URL == None:
		print "+++ An URL must be provided using the -u switch."
		sys.exit(1)

	urlApi = options.URL
	print '+++ Using target URL:', urlApi
		
	c = pycurl.Curl()
	c.setopt(c.PROXY, proxyProtocol + '://' + proxyHost + ':' + proxyPort)
	c.setopt(c.URL, urlApi)
	c.setopt(pycurl.SSL_VERIFYPEER, 0)  
	c.setopt(pycurl.SSL_VERIFYHOST, 0)
	c.setopt(pycurl.USERAGENT, requestUA)
	c.setopt(pycurl.POST, 1)

	# Add authentication details
	c.setopt(pycurl.USERPWD, "%s:%s" % (requestUser, requestPass))

	# Add custom headers
	headers = []
	if requestType:
		headers.append("Content-Type: %s" % requestType)
	if requestSoapAction:
		headers.append("SOAPAction: %s" % requestSoapAction)

	c.setopt(pycurl.HTTPHEADER, headers)

	c.setopt(pycurl.POSTFIELDS, f.read())
	b = StringIO.StringIO()
	c.setopt(pycurl.WRITEFUNCTION, b.write)
	try:
		c.perform()
		print "+++ Results:"
		print b.getvalue()
	except pycurl.error, e:
		errorCode, errorText = e.args
		print "+++ ERROR: Code: %s, Text: %s" % (errorCode, errorText)

if __name__ == '__main__':
	signal.signal(signal.SIGINT, handler)
	main(sys.argv[1:])
	sys.exit()

