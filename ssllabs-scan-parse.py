#!/usr/bin/python
import json
import md5
import sys
import time
from pprint import pprint

with sys.stdin as json_data:
        try:
                data = json.load(json_data)
        except:
                print "Error: no JSON data received!"
                exit(1)
for site in data:
        endpoints = site['endpoints']
        certExp = time.ctime(int(endpoints[0]['details']['cert']['notAfter']/1000))
        certRaw = endpoints[0]['details']['chain']['certs'][0]['raw']
        certMD5 = md5.new(certRaw).hexdigest()
        print "Site: %s:%s, Grade: %s, CertIssuer: %s, CertExpiration: %s CertMD5: %s" % (
                site['host'],
                site['port'],
                endpoints[0]['grade'],
                endpoints[0]['details']['cert']['issuerLabel'],
                time.ctime(int(endpoints[0]['details']['cert']['notAfter']/1000)),
                certMD5
        )
