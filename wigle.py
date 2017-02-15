#!/usr/bin/python
# 
# Geolocate a list of SSID's using the Wigle API
#

import urllib2, os, re, json
from time import sleep

with open('wigle.data') as f:
    content = f.readlines()

content = [x.strip() for x in content] 

print_header = True

for SSID in content:
	print "Processing %s" % SSID
	url = 'https://api.wigle.net/api/v2/network/search?first=0&freenet=false&paynet=false&ssid=%s&api_key=k' % SSID.replace(' ', '%20')

	try:
		opener = urllib2.build_opener()
		# Use your Wigle API key
		opener.addheaders = [('Accept', 'application/json'), ('Authorization', 'Basic xxxxxxxxxxxxxxxxxx')]
		response = opener.open(url)
	except:
		print "ERROR: Cannot fetch data for %s" % SSID

	obj = json.loads(response.read())
	if obj['results']:
		try:
			f = open('wigle.csv', 'a')
			if print_header:
				f.write('SSID,Lat,Lon\n')
				print_header = False
		except:
			print 'ERROR: Cannot open wigle.csv'
		for result in obj['results']:
			f.write('%s,%s,%s\n' % (SSID, str(result['trilat']), str(result['trilong'])))
		f.close()
	sleep(1)