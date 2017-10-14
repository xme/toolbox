#!/usr/bin/python3
#
# Extract cells from XLS sheets
#
# Usage:
#
# ./xlsxtr.py --cols=start1-[end1],startN-[endN] --rows=start1-[end1],startN-[endN]
#             [--workbook|-w <name>]
#             [--prefix|-p]
#             [--help|-h]
#             <-|file>
#
# Author: Xavier Mertens <xavier@rootshell.be>
# Copyright: GPLv3 (http://gplv3.fsf.org)
# Fell free to use the code, but please share the changes you've made
#
# Todo
# -
#

import os
from optparse import OptionParser

try:
        from openpyxl import load_workbook
except:
        print("[!] Please install openpyxl")
        exit(1)

def processFile(file, options):
	""" ----------------------------- """
	""" Read cells from an Excel file """
	""" ----------------------------- """

	max = 65535
	if options.max:
		max = options.max

	try:
		xls = load_workbook(filename = file, read_only=True)
		wb = xls.get_sheet_names()
	except:
		print("[!] Cannot read '%s' (not XLSX format?)" % file)
		return False

	if options.workbook not in wb:
		print("[!] Workbook '%s' does not exist. Found workbooks: %s" % (options.workbook, wb))
		return False
	try:
		sheet_ranges = xls[options.workbook]
	except:
		print("[!] Cannot open workbook '%s'" % options.workbook)
		return False

	colRanges = options.cols.split(',')
	rowRanges = options.rows.split(',')

	for c in colRanges:
		c_range = c.split('-')
		c = c_min = ord(c_range[0])

		for r in rowRanges:
			if len(c_range) == 1:			# 'A'
				c_max = c_min
			elif len(c_range[1]) == 0:		# 'A-'
				c_max = max
			else: 					# A-B
				c_max = ord(c_range[1])
			r_range = r.split('-')
			r = r_min = int(r_range[0])
			if len(r_range) == 1:
				r_max = r_min
			elif len(r_range[1]) == 0:
				r_max = max
			else:
				r_max = int(r_range[1])

			while c <= c_max:
				while r <= r_max:
					cell = chr(c) + str(r)
					data = sheet_ranges[cell].value
					if data == None and options.stop == True:
						return True
					if options.prefix == True:
						print('%s=%s' % (cell, data))
					else:
						print(data)
					r = r +1
				r = r_min
				c = c + 1
			c = c_min
	return True

def main():
	parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
	parser.add_option('-w', '--workbook', dest='workbook', type='string', \
		help='Workbook to extract data from')
	parser.add_option('-c', '--cols', dest='cols', type='string', \
		help='Read columns (Format: "A", "A-" or "A-B")')
	parser.add_option('-r', '--rows', dest='rows', type='string', \
		help='Read rows (Format: "1", "1-" or "1-10")')
	parser.add_option('-m', '--max', dest='max', type='int', \
		help='Process maximum rows')
	parser.add_option('-p', '--prefix', action='store_true', dest='prefix', \
                help='Display cell name', default='False')
	parser.add_option('-s', '--stop', action='store_true', dest='stop', \
                help='Stop processing when empty cell is found', default='False')
	(options, args) = parser.parse_args()

	for a in args:
		processFile(a, options)

if __name__ == '__main__':
	main()
	exit(0)