#!/usr/bin/python
'''

Script to collect IP reputation data from the ISC database
(see https://isc.sans.edu/api/)
Can be invoked manually or from an OSSEC active-response setup

@author:        Xavier Mertens <xavier@rootshell.be>
@copyright:     AGPLv3 (http://www.gnu.org/licenses/agpl.html)

To be done:
- [DONE] Implement proxy support for HTTPS requests
- [DONE] Setup yaml config file for runtime parameters
- [TODO] Log the call to active-response.log 
- [DONE] Parameter: number of days in cache
- [TODO] Log to ELK?
'''

import json
import os
import sys
import optparse
import logging.handlers
from datetime import datetime
try:
	import yaml
except:
	exit('ERROR: Cannot import yaml library!')
try:
	import urllib2
except:
	exit('ERROR: Cannot import urllib2 Python library!')
try:
	import sqlite3
except:
	exit('ERROR: Cannot import sqlite3 Python library')

def parseconfig(c):
	'''
	Parse the YAML configuration file
	'''
	global yamlconfig
	try:
		yamlconfig = yaml.load(file(c))
	except yaml.YAMLError, e:
		logger.error('Error in configuration file:')
		if hasattr(e, 'problem_mark'):
			mark = e.problem_mark
			logger.error('Position: (%s:%s)' % (mark.line+1, mark.column+1))
			exit(1)

def stripspaces(j):
	'''
	Remove heading and trailing spaces from JSON data
	'''
	for e in j:
		if j[e]:
			j[e] = j[e].strip()
	return j

def populate(j):
	'''
	Populate JSON data with missing information from ISC
	'''
	if not 'count' in j:
		j['count'] = 0
	if not 'attacks' in j:
		j['attacks'] = 0
	if not 'trend' in j:
		j['trend'] = '0'
	if not 'maxdate' in j:
		j['maxdate']= "1970-01-01"
	if not 'mindate' in j:
		j['mindate']= "1970-01-01"
	if not 'updated' in j:
		j['updated']= datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
	if not 'abusecontact' in j:
		j['abusecontact']= ""
	if not 'comment' in j or not j['comment']:
		j['comment'] = ""
	return j

class SqliteDB():
	'''
	Sqlite3 database management class
	'''
	def __init__(self, dbfile):
		self.dbfile = dbfile
		self.db_conn = None
		self.c = None

	def check(self):
		try:
			self.db_conn = sqlite3.connect(self.dbfile)
			self.c = self.db_conn.cursor()
		except sqlite3.DatabaseError, e:
			exit('ERROR: Cannot open the database file %s: %s' % (self.dbfile, e))
		try:
			self.c.execute('''
				CREATE TABLE IF NOT EXISTS ip (
					ip TEXT,
					count INTEGER,
					attacks	INTEGER,
					trend TEXT,
					maxdate TEXT,
					mindate TEXT,
					updated TEXT,
					country TEXT,
					asnumber TEXT,
					asname TEXT,
					network TEXT,
					abusecontact TEXT,
					comment TEXT
				)''')
			self.db_conn.commit()
		except sqlite3.DatabaseError, e:
			exit('ERROR: Cannot create table %s: %s' % (self.dbfile, e))

	def isvalid(self, ip):
		output = False
		data = { 'ip': ip } # Key
		self.c.execute('''SELECT ip, count, attacks, trend, maxdate, mindate, updated, country,
				asnumber, asname, network, abusecontact, comment
				FROM ip WHERE ip=:ip''', data)
		r = self.c.fetchone()
		if r and r[0]:
			output = {}
			output['count'] = int(r[1])
			output['attacks'] = int(r[2])
			output['trend'] = r[3]
			output['maxdate'] = r[4]
			output['mindate'] = r[5]
			output['updated'] = r[6]
			output['country'] = r[7]
			output['as'] = r[8]
			output['asname'] = r[9]
			output['network'] = r[10]
			output['abusecontact'] = r[11]
			output['comment'] = r[12]
		return output

	def save(self, j):
		j = stripspaces(j)
		data = { 'ip': j['number'] }
		logger.debug('Saving {i}'.format(i=data['ip']))
		self.c.execute('SELECT COUNT(ip) FROM ip WHERE ip=:ip', data)
		r = self.c.fetchone()
		if r and r[0]:
			self.update(j)
		else:
			self.insert(j)

	def insert(self, j):
		data = populate(j)
		try:
			self.c.execute('INSERT INTO ip VALUES (:number, :count, :attacks, :trend, :maxdate, :mindate, :updated, :country, :as, :asname, :network, :abusecontact, :comment)', data)
			self.db_conn.commit()
		except sqlite3.DatabaseError, e:
			exit('ERROR: Cannot insert IP {ip}: {error}'.format(ip=j['number'], error=e))

	def update(self, j):
		data = populate(j)
		try:
			self.c.execute('''UPDATE ip SET count = :count,
					attacks = :attacks,
					trend = :trend,
					maxdate = :maxdate,
					mindate = :mindate,
					updated = :updated,
					country = :country,
					asnumber = :as,
					asname = :asname,
					network = :network,
					abusecontact = :abusecontact,
					comment = :comment
					WHERE ip = :ip''', data)
			self.db_conn.commit()
		except sqlite3.DatabaseError, e:
			exit('ERROR: Cannot update IP {ip}: {error}'.format(ip=j['ip'], error=e))

if __name__ == '__main__':
	global db
	global logger

	ossecized = False	# Running from OSSEC

	parser = optparse.OptionParser("usage: %prog <IP-address> [options]")
	parser.add_option('-v', action='store_true', dest='verbose',
				help='enable verbose output')
	parser.add_option('-c', action='store_true', dest='config',
				help='specify a configuration file')
	(options, args) = parser.parse_args()


	if not options.config:
		# Load the default configuration in /etc/isc-ipreputation.conf
		if os.path.isfile('/etc/isc-ipreputation.conf'):
			options.config = '/etc/isc-ipreputation.conf'
	if not os.path.isfile(options.config):
		exit('ERROR: Cannot read configuration file {c}!'.format(c=options.config))

	logger = logging.getLogger('isc-ipreputation')
	logger.setLevel(logging.INFO)
	#hdlr = logging.StreamHandler(sys.stdout)
	hdlr = logging.FileHandler('/var/log/ipreputation.log')
	formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(message)s')
	hdlr.setFormatter(formatter)
	logger.addHandler(hdlr)

	parseconfig(options.config)

	if options.verbose or yamlconfig['logging']['debug']:
		logger.setLevel(logging.DEBUG)
		logger.addHandler(logging.StreamHandler(sys.stdout))

        logger.addHandler(logging.handlers.SysLogHandler(facility=logging.handlers.SysLogHandler.LOG_LOCAL0))

	# Detect if we are spawned by OSSEC (ossec-execd)
	try:
		import psutil
		p = psutil.Process(pid=os.getppid())
		if p.name == "ossec-execd":
			ossecized = True
	except:
		pass

	if ossecized:
		if len(sys.argv) < 4:
			exit('ERROR: Requires at least 3 args if invoked from OSSEC')
		else:
			# We just need the offending IP address from OSSEC
			IP = sys.argv[3]
	else:
		IP = sys.argv[1]

	# Skip blacklisted IP addresses
	if yamlconfig['network']['exclude-ip']:
		import re
		m = re.search(yamlconfig['network']['exclude-ip'], IP)
		if m:
			logger.debug('Skipping blacklisted IP: {i}'.format(i=IP))
			exit(0)

	# Initialize the db
	db = SqliteDB(yamlconfig['database']['path'])
	db.check()

	# TTL days (expired local data)
	if not yamlconfig['network']['ttl-days']:
		yamlconfig['network']['ttl-days'] = 5 # Default value
		
	# Do we have accurate data for this IP? 
	do_fetch = False
	jsondata = db.isvalid(IP)
	if jsondata:
		delta = datetime.now() - datetime.strptime(jsondata['updated'], '%Y-%m-%d %H:%M:%S')
		if int(delta.days) > yamlconfig['network']['ttl-days']:
			logger.debug('Expired data for IP {i} (Age: {d}), fetching again'.format(i=IP, d=delta))
			do_fetch = True
		# For debugging purposes
		# do_fetch = True
	else:
		logger.debug('No data found, fetching from ISC')
		do_fetch = True

	if do_fetch:
		saveddata = None
		if jsondata:
			saveddata = jsondata # Save our local results
		try:
			# Fetch IP data from ISC
			if yamlconfig['http']['proxy']:
				logger.debug('Using proxy: {p}'.format(p=yamlconfig['http']['proxy']))
				proxy = urllib2.ProxyHandler({'https': yamlconfig['http']['proxy']})
				opener = urllib2.build_opener(proxy)
				urllib2.install_opener(opener)
			if yamlconfig['http']['user-agent']:
				logger.debug('Using user-agent: {u}'.format(u=yamlconfig['http']['user-agent']))
				req = urllib2.Request('https://isc.sans.edu/api/ip/' + IP + '?json',
					 headers= { 'User-Agent' : yamlconfig['http']['user-agent'] })
			else:
				req = urllib2.Request('https://isc.sans.edu/api/ip/' + IP + '?json')
			r = urllib2.urlopen(req)
			jsondata = json.loads(r.read())['ip']
			r.close()
		except URLError as e:
			exit('ERROR: Cannot get info for {ip}: {error}'.format(ip=IP, error=e))
		if jsondata:
			jsondata = populate(jsondata)
			jsondata['ip'] = IP
			if saveddata:
				# Compute trending index
				if saveddata['count'] == 0:
					count_trend = jsondata['count']
				else:
					# To fix: if count < 100 -> BUG! (Division by zero)
					#count_trend = (int(jsondata['count'])/(int(saveddata['count']) / 100))-100
					count_trend = jsondata['count']
				if saveddata['attacks'] == 0:
					attacks_trend = jsondata['attacks']
				else:
					# To fix: if attacks < 100 -> BUG! (Division by zero)
					#attacks_trend = (int(jsondata['attacks'])/(int(saveddata['attacks']) / 100))-100
					attacks_trend = jsondata['attacks']
				jsondata['trend'] = str(int(count_trend) + int(attacks_trend))
			db.save(jsondata)
			# Format the result string
			logger.info('IP={i}, AS={a}("{an}"), Network={nw}, Country={co}, Count={nc}, AttackedIP={na}, Trend={t}, FirstSeen={fs}, LastSeen={ls}, Updated={u}'.format(
				i=IP, 
				a=jsondata['as'],
				an=jsondata['asname'],
				nw=jsondata['network'],
				co=jsondata['country'],
				nc=jsondata['count'],
				na=jsondata['attacks'],
				t=jsondata['trend'],
				fs=jsondata['mindate'],
				ls=jsondata['maxdate'],
				u=jsondata['updated']
				))
	#print json.dumps(jsondata, indent=4, sort_keys=True)
	exit
