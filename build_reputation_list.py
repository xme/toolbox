#!/usr/bin/python
#
# Extract suspicious IP addresses from Snort rules files
# to build IP reputation lists
#
# Author: Xavier Mertens <xavier@rootshell.be>
# Copyright: GPLv3 (http://gplv3.fsf.org/)
# Feel free to use the code, but please share the changes you've made
# 
import os
import re

# Replace with your locale rules repository
rulesDir = '/data/suricata/etc/suricata/rules'
regex = re.compile("\[(\d+\.\d+\.\d+\.\d+[,]*)+\]");
for filename in os.listdir(rulesDir):
	fd = open(rulesDir + "/" + filename, "r+")
	for line in fd:
		ips = regex.findall(line)
		for ip in ips:
			print ip
