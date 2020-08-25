#!/usr/bin/python3
#
#
# check_misp_workers.py - Returns the number of ok/dead workers in a Nagios plugin format
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

if not misp_verifycert:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    # Default thresholds
    mispWarning = 1
    mispCritical = 2
    workers_ok = workers_dead = 0

    parser = argparse.ArgumentParser(description="Nagios compatible plugin to monitor MISP workers")
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
        res = requests.get("{misp_url}/servers/getWorkers".format(misp_url=args.mispURL), headers=headers, verify=misp_verifycert).json()
        for el in res:
            worker = res.get(el)
            if type(worker) is dict:
                if 'ok' in worker:
                    if worker.get('ok') is True:
                        workers_ok += len(worker.get('workers'))
                    else:
                        workers_dead += 1
    except:
        workers_ok = None
        workers_dead = None

    format_str = "{status} - {workers} workers dead|workers_ok={workers_ok};workers_dead={workers_dead}"

    try:
        if workers_dead < int(args.mispWarning):
            print(format_str.format(status="OK",workers=workers_dead,workers_ok=workers_ok,workers_dead=workers_dead))
            rc = NAGIOS_OK
        elif workers_dead < int(args.mispCritical):
            print(format_str.format(status="WARNING",workers=workers_dead,workers_ok=workers_ok,workers_dead=workers_dead))
            rc = NAGIOS_WARNING
        else:
            print(format_str.format(status="CRITICAL",workers=workers_dead,workers_ok=workers_ok,workers_dead=workers_dead))
            rc = NAGIOS_CRITICAL
    except:
        print("UNKOWN - Cannot fetch workers status")
        rc = NAGIOS_UNKNOWN

    exit(rc)

if __name__ == "__main__":
        main()
