#!/usr/bin/python
#
# xls_hidden.py
#
# Author: Xavier Mertens <xavier@rootshell.be>
# Copyright: GPLv3 (http://gplv3.fsf.org)
# Fell free to use the code, but please share the changes you've made
#

import sys
import argparse

try:
	import xlrd
except:
	print "xlrd Python module is required"
	exit(1)

def inspectSheet(sheet, quiet):
	try:
		xls = xlrd.open_workbook(sheet, formatting_info=1)
	except:
		print "Cannot parse file %s (bad format?)" % sheet
		exit(1)

	fonts = xls.font_list
	sheets = xls.nsheets
	names  = xls.sheet_names()
	print "Number of sheets: %s" % sheets
	for i in range(sheets):
		print "--- Processing sheet %d (%s) ---" % (i, names[i].encode('utf-8'))
		s = xls.sheet_by_index(i)
		for row in range(s.nrows):
			col = 0
			for cell in s.row(row):
				if cell.value:
					fmt = xls.xf_list[cell.xf_index]
					if fmt.background.background_colour_index == fonts[fmt.font_index].colour_index:
						status = "[C]"
						found_cell = True
					if s.rowinfo_map[row].hidden:
						status = "[H]"
						found_cell = True
					else:
						status = "   "
						found_cell = False
					if quiet:
						if found_cell:
							print "[%5d/%5d] %s '%s'" % (row,col,status,str(cell.value).encode('utf-8'))
					else:
						print "[%5d/%5d] %s '%s'" % (row,col,status,str(cell.value).encode('utf-8'))
				col+=1

def main():
	parser = argparse.ArgumentParser(
		description = "Search for hidden cells in Excel sheets")
	parser.add_argument('file', metavar='file', nargs='*',
		help = 'the Excel sheet to check.')
	parser.add_argument('-q', '--quiet',
	                action = 'store_true',
        	        dest = 'quiet',
                	help = 'display only hidden cells',
	                default = False)
	args = parser.parse_args()

	for f in args.file:
		inspectSheet(f, args.quiet)

if __name__ == '__main__':
	main()
