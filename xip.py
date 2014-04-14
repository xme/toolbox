#!/usr/bin/python
#
# xip.py
#
# Expands a list of IP addresses and pass them to a specified command
#
# Author: Xavier Mertens <xavier@rootshell.be>
# Copyright: GPLv3 (http://gplv3.fsf.org/)
# Feel free to use the code, but please share the changes you've made
#
# ip2bin(), dec2bin() and bin2ip() come from CIDR Block Converter
# Copyright (c) 2007 Brandon Sterne
# Licensed under the MIT license.
# http://brandon.sternefamily.net/files/mit-license.txt
#
# Target specification:
# [-]192.168.0.0/24
# [-]192.168.0.0-10
#
import os.path
import sys, re
import shlex
import ConfigParser
import subprocess as sub
import time
from optparse import OptionParser

debug = 0

included_ip = []
excluded_ip = []

# convert an IP address from its dotted-quad format to its
# 32 binary digit representation
def ip2bin(ip):
    b = ""
    inQuads = ip.split(".")
    outQuads = 4
    for q in inQuads:
        if q != "":
            b += dec2bin(int(q),8)
            outQuads -= 1
    while outQuads > 0:
        b += "00000000"
        outQuads -= 1
    return b

# convert a decimal number to binary representation
# if d is specified, left-pad the binary number with 0s to that length
def dec2bin(n,d=None):
    s = ""
    while n>0:
        if n&1:
            s = "1"+s
        else:
            s = "0"+s
        n >>= 1
    if d is not None:
        while len(s)<d:
            s = "0"+s
    if s == "": s = "0"
    return s

# convert a binary string into an IP address
def bin2ip(b):
    ip = ""
    for i in range(0,len(b),8):
        ip += str(int(b[i:i+8],2))+"."
    return ip[:-1]

def expandNetworks(c):
	# Multiple CIDR can be separated by commas
	networks = c.split(",")
	for n in networks:
		# Format: x.x.x.x/x
		p = re.compile("^[-]*([0-9]{1,3}\.){0,3}[0-9]{1,3}(/[0-9]{1,2}){1}$")
		if p.match(n):
			prefix, subnet = n.split("/")
			if prefix[0] == "-":
				destination = excluded_ip
				prefix = prefix[1:]
			else:
				destination = included_ip
			quads = prefix.split(".")
			for q in quads:
				if (int(q) < 0) or (int(q) > 255):
					print "Error: quad "+str(q)+" wrong size."
					return False
			if (int(subnet) < 1) or (int(subnet) > 32):
				print "Error: subnet "+str(subnet)+" wrong size."
				return False
			startip = ip2bin(prefix)
			mask = int(subnet)
			if mask == 32:
				destination.append(bin2ip(startip))
			else:
				ipPrefix = startip[:-(32-mask)]
				for i in range(2**(32-mask)):
					destination.append(bin2ip(ipPrefix+dec2bin(i, (32-mask))))
		else:
			# Format: x.x.x.x-x
			p = re.compile("^[-]*([0-9]{1,3}\.){0,3}[0-9]{1,3}(-[0-9]{1,3}){1}$")
			if p.match(n):
				s = n.split("-")
				if len(s) == 2:
					startip = s[0]
					lastbyte = s[1]
					destination = included_ip
				else:
					startip = s[1]
					lastbyte = s[2]
					destination = excluded_ip
				quads = startip.split(".")
				for q in quads:
					if (int(q) < 0) or (int(q) > 255):
						print "Error: quad "+str(q)+" wrong size."
						return False
				if (int(lastbyte) < 1) or (int(lastbyte) > 255):
					print "Error: Last byte "+str(subnet)+" wrong size."
					return False
				n = int(quads[3])
				while n <= int(lastbyte):
					str = "%s.%s.%s.%d" % (quads[0], quads[1], quads[2], n)
					destination.append(str)
					n = n + 1
	# Return the number of IP addresses expanded
	return len(included_ip) - len(excluded_ip)

def printUsage():
    print "Usage: ./cidr.py <prefix>/<subnet>\n  e.g. ./cidr.py 10.1.1.1/28" + \
          "\n  e.g. ./cidr.py 192.168.1/24"
    
def main():
	global debug

	parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
	parser.add_option('-i', '--ip-addresses', dest='ipaddresses', type='string',
			help='IP Addresses subnets to expand')
	parser.add_option('-c', '--command', dest='command', type='string',
			help='Command to execute for each IP ("{}" will be replaced by the IP)')
	parser.add_option('-o', '--output', dest='output', type='string',
			help='Send commands output to a file')
	parser.add_option('-s', '--split', action='store_true', dest='split',
			help='Split outfile files per IP address')
	parser.add_option('-d', '--debug', action='store_true', dest='debug',
			help='Debug output')
	(options, args) = parser.parse_args()

	if options.debug:
		debug = 1
		print "+++ Debug mode"

	if options.ipaddresses == None:
		print "Please use the -i switch to provide IP addresses"
		sys.exit(1)

	if options.command == None:
		print "Please use the -c switch to provide a command"
		sys.exit(1)

	if options.command.find("{}") == -1:
		print "Please use {} in the command arguments to specify the IP address"
		sys.exit(1)

	n = expandNetworks(options.ipaddresses)
	if debug:
		print "+++ %d IP addresses expanded" % n

	if options.output and os.path.isfile(options.output):
		print "File %s already exists!" % options.output
		sys.exit(1)

	for ip in included_ip:
		if not ip in excluded_ip:
			# Replace {} with IP address
			c = options.command.replace("{}", ip)
			if debug:
				print "+++ Starting: %s" % c
			a = shlex.split(c)
			p = sub.Popen(a, stdout=sub.PIPE, stderr=sub.PIPE)
			output, errors = p.communicate()
			e = p.returncode
			if debug:
				print "+++ Command RC: %d" % e
			if options.output:
				if options.split:
					if debug:
						print "+++ Spliting output files per IP address"
					ext = ip.replace(".", "_")
					file= options.output + "_" + ext
				else:
					file = options.output
				with open(file, "a") as f:
					if debug:
						f.write("--- Started PID %d: %s (%s) ---\n" % 
							(p.pid, c, time.asctime()))
					if output:
						f.write(output)
					if errors:
						f.write(errors)
					if debug:
						f.write("--- Stopped with exit code: %d (%s) ---\n" % (e, time.asctime()))
					f.close()
			else:
				if output:
					print output.rstrip()
				if errors:
					print errors.rstrip()
	if debug and options.output:
		if options.split:
			print "+++ Commands output saved to %s_x_x_x_x" % options.output
		else:
			print "+++ Commands output saved to %s" % options.output

if __name__ == "__main__":
    main()
