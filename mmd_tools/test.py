# -*- coding: utf-8 -*-
from . import import_pmx

import re
import os 

#test_dir:all pmx will import in test_dir
#scale:import_scale
def test_import_pmx(test_dir = './test_dir',scale = 0.2):
	importer = import_pmx.PMXImporter()
	pmxMatch = re.compile(r'.\.pmx$') 
	for dpath,dnames,fnames in os.walk(test_dir):
		for fname in fnames:
			try:
				if pmxMatch.search(fname): 
					print(fname)
					print(os.path.join(dpath,fname))
					try :
						importer.execute(filepath=os.path.join(dpath,fname),scale=scale)
						print("no error at" + fname)
					except:
						("import is failed at" + fname)
			except Exception as e:
				print("something gone wrong " + fname)
				print(str(type(e)))
				print(e)

