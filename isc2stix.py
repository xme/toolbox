#!/usr/bin/python
#
# Convert the ISC top-100 malicious IP into a STIX 1.2 XML object
#
# Author: Xavier Mertens <xavier@rootshell.be>
# Copyright: GPLv3 (http://gplv3.fsf.org/)
# Feel free to use the code, but please share the changes you've made
# 
import xmltodict
import urllib2
from cybox.objects.address_object import Address
from stix.core import STIXPackage, STIXHeader
from stix.indicator.indicator import Indicator

def main():
    url = 'https://isc.sans.edu/api/topips/records/100'
    ua = 'ISC2Stix/1.0 (https://blog.rootshell.be/)'
    headers = { 'User-Agent' : ua }

    try:
        req = urllib2.Request(url, None, headers)
        res = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        print "HTTPError: " + str(e.code)
    except urllib2.URLError, e:
        print "URLError: " + str(e.reason)

    doc = xmltodict.parse(res.read())

    # Create the STIX Package
    package = STIXPackage()

    # Create the STIX Header and add a description.
    header = STIXHeader()
    #header.title = "SANS ISC Top-100 Malicious IP Addresses"
    #header.description = "Source: " + url
    package.stix_header = header

    for entry in doc['topips']['ipaddress']:
        bytes = entry['source'].split('.')

        indicator = Indicator()
        indicator.title = "SANS ISC Malicious IP"
        indicator.add_indicator_type("IP Watchlist")

        ip = Address()
        ip.address_value = "%d.%d.%d.%d" % (int(bytes[0]), int(bytes[1]), int(bytes[2]) , int(bytes[3]))
        ip.category = 'ipv4-addr'
        ip.condition = 'Equals'
        indicator.add_observable(ip)

        package.add_indicator(indicator)

    print(package.to_xml())

if __name__ == '__main__':
    main()