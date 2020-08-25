#!/usr/bin/python3
#
#
# check_misp_data.py - Returns the number of new events/attributes in a Nagios plugin format
#
# Author: Xavier Mertens <xavier@rootshell.be>
# Copyright: GPLv3 (http://gplv3.fsf.org/)
# Feel free to use the code, but please share the changes you've made
#

import argparse
import requests
import json
import sys

NAGIOS_OK = 0
NAGIOS_WARNING = 1
NAGIOS_CRITICAL = 2
NAGIOS_UNKNOWN =  3

misp_useragent = "MISP Nagios Plugin"
misp_verifycert = False
misp_cachefile = "/var/tmp/misp-cache.json"

if not misp_verifycert:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_data_cached():
    try:
        with open(misp_cachefile) as json_file:
            cache = json.load(json_file)
            return (int(cache['events']), int(cache['attributes']), int(cache['users']), int(cache['orgs']))
    except:
        # Cannot read cache, return 0's
        return (0,0,0,0)

def update_data_cached(events, attributes, users, orgs):
    cache = {}
    cache['events'] = events
    cache['attributes'] = attributes
    cache['users'] = users
    cache['orgs'] = orgs
    try:
        with open(misp_cachefile, 'w') as outfile:
            json.dump(cache, outfile)
        return(True)
    except:
        return(False)

def main():
    # Default thresholds
    mispWarning = 100
    mispCritical = 200
    new_events = new_attributes = new_users = new_orgs = 0

    parser = argparse.ArgumentParser(description="Nagios compatible plugin to monitor MISP events/attributes")
    parser.add_argument('-u', '--url',
        dest = "mispURL",
        help = "MISP URL",
        metavar = 'MISPURL')
    parser.add_argument('-k', '--key',
        dest = "mispKey",
        help = "MISP API Key",
        metavar = 'MISPKEY')
    parser.add_argument('-w', '--warning',
        dest = "mispWarning",
        help = "MISP Warning Threshold",
        metavar = 'MISPWARN')
    parser.add_argument('-c', '--critical',
        dest = "mispCritical",
        help = "MISP Critical Threshold",
        metavar = 'MISPCRIT')
    args = parser.parse_args()

    try:
        headers = {'Authorization': '{misp_key}'.format(misp_key=args.mispKey),
                   'Accept': 'application/json',
                   'content-type': 'application/json',
                   'User-Agent': '{misp_useragent}'.format(misp_useragent=misp_useragent)}
        res = requests.get("{misp_url}/users/statistics.json".format(misp_url=args.mispURL), headers=headers, verify=misp_verifycert).json()
        stats = res.get('stats')
        new_events = int(stats.get('event_count_month'))
        new_attributes = int(stats.get('attribute_count_month'))
        new_orgs = int( stats.get('org_count'))
        new_users = int(stats.get('user_count'))
    except:
        new_events = new_attributes = new_users = new_orgs = None

    (cached_events, cached_attributes, cached_users, cached_orgs) = get_data_cached()
    events = new_events - cached_events
    attributes = new_attributes - cached_attributes
    users = new_users - cached_users
    orgs = new_orgs - cached_orgs

    format_str = "{status} - New events: {events} New attributes: {attributes} New users: {users} New orgs: {orgs}|events={events};attributes={attributes};users={users};orgs={orgs}"

    # Cache data for next invocation
    if not update_data_cached(new_events, new_attributes, new_users, new_orgs):
        print("UNKNOWN - Cannot cache data")
        exit(NAGIOS_UNKNOWN)

    try:
        if attributes > int(args.mispCritical):
            print(format_str.format(status="CRITICAL",events=events,attributes=attributes,users=users,orgs=orgs))
            rc = NAGIOS_CRITICAL
        elif attributes > int(args.mispWarning):
            print(format_str.format(status="WARNING",events=events,attributes=attributes,users=users,orgs=orgs))
            rc = NAGIOS_WARNING
        else:
            print(format_str.format(status="OK",events=events,attributes=attributes,users=users,orgs=orgs))
            rc = NAGIOS_OK
    except:
        print("UNKOWN - Cannot fetch stats")
        rc = NAGIOS_UNKNOWN

    exit(rc)

if __name__ == "__main__":
        main()
