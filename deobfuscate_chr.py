#!/usr/bin/python
#
# Decode VBA Macro based on chr() obfuscation
# Xavier Mertens <xavier@rootshell.be>
#

import re
import sys

def do_chr(m):
	if m.group(0):
		return eval(re.sub(r'[cC][hH][rR][wW\$]*\(([\d\+\-\s.]*)\)',r'chr(int(\1))', m.group(0)))	
	return ""
	
for line in sys.stdin.readlines():
	line = re.sub(r'[cC][hH][rR][wW\$]*\(([\d+\+\-\s\.]*)\)', do_chr, line)
	line = re.sub(" & ", "", line)
	print line.rstrip()
exit
