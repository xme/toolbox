#!/usr/bin/python
#
# Search for credential dumps on <redacted>.
# 
# Author: Xavier Mertens <xavier@rootshell.be>
# Copyright: GPLv3 (http://gplv3.fsf.org/)
# Feel free to use the code, but please share the changes you've made
#
# Usage: ./checkcredentials.py
#
# Create a checkcredentials.conf in the same directory with one domain / line
#

import difflib
import hashlib
import os.path
import urllib2
import sys
import json

# Private API key
apiKey='<redacted>'

try:
        content = open('checkcredentials.conf').read().splitlines()
except IOError as e:
        print 'Cannot read checkcredentials.conf: %s (%s)' % (e.strerror, e.errno)
        exit(-1)

for domain in content:
        url = 'https://<redacted>/api/domain/%s?apikey=%s' % (domain, apiKey)
        try:
                response = urllib2.urlopen(url)
                data = json.loads(response.read())
                newJson = json.dumps(data, indent = 4)
        except urllib2.HTTPError as e:
                print '%s: HTTP Error: %s' % (domain, str(e.code))
        except urllib2.URLError as e:
                print '%s: URL Error: %s' % (domain, str(e.reason))

        m = hashlib.md5()
        m.update(newJson)
        newHash = m.hexdigest()

        oldDump = '%s.dump' % domain
        if os.path.isfile(oldDump):
                try:
                        oldJson = open(oldDump).read()
                        oldHash = hashlib.md5(oldJson).hexdigest()
                except IOError as e:
                        print 'Cannot read %s.dump: %s (%s)' % (domain, e.strerror, e.errno)
                        continue

                if newHash != oldHash:
                        print "New credentials leaked for %s:" % domain
                        diff = difflib.context_diff(oldJson.splitlines(1), newJson.splitlines(1), fromfile='Old Hash', tofile='New Hash')
                        print ''.join(diff)
        try:
                w = open(oldDump, 'w')
                w.write(newJson)
                w.close()
        except IOError as e:
                print "Cannot save %s.dump: %s (%s)" % (e.strerror, e.errno)
