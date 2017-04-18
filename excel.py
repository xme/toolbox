# -*- coding: utf-8 -*-
from viper.common.abstracts import Module
from viper.core.database import Database
from viper.core.session import __sessions__
from viper.core.storage import get_sample_path
from viper.common.objects import MispEvent
from viper.common.constants import VIPER_ROOT
from viper.core.config import Config

try:
    import xlrd
    HAVE_XLRD = True
except:
    HAVE_XLRD = False

class Excel(Module):
	cmd = 'excel'
	description = 'This module searches for hidden data in Excel sheets'
	authors = ['Xavier Mertens <xavier@rootshell.be>']

	def __init__(self):
		super(Excel, self).__init__()

	def run(self):
	        super(Excel, self).run()

		# Check if there is an open session.
        	if not __sessions__.is_set():
			# No session opened.
			return

		if not HAVE_XLRD:
			self.log('error', "Missing dependency, install xlrd (`pip install xlrd`)")
			return
        
		try:
			xls = xlrd.open_workbook(__sessions__.current.file.path, formatting_info=1)
		except:
			self.log('error', 'Cannot parse file %s (bad format?)' % __sessions__.current.file.path)
			return

		fonts = xls.font_list
		sheets = xls.nsheets
		names  = xls.sheet_names()
		for i in range(sheets):
			#self.log('info', 'Sheet %d (%s)' % (i, names[i].encode('utf-8')))
			self.log('info', 'Sheet %d' % i)

			header = ['Row', 'Col', 'Status', 'Value']
			s = xls.sheet_by_index(i)
			rows = []
			for row in range(s.nrows):
                		col = 0
                		for cell in s.row(row):
                		        if cell.value:
                	        	        fmt = xls.xf_list[cell.xf_index]
                	        	        if fmt.background.background_colour_index == fonts[fmt.font_index].colour_index:
                	        	                status = "Same Color"
                	        	        if s.rowinfo_map[row].hidden:
                	        	                status = "Hidden"
                	        	        else:
                	        	                status = "   "
						#rows.append([row, col, status, str(cell.value).encode('utf-8')])
						rows.append([row, col, status, str(cell.value)])
					col+=1
			self.log('table', dict(header=header,rows=rows))
