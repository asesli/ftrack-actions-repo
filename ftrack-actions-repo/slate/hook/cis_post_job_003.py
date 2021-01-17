import os, sys

import re
from System.IO import *
from Deadline.Scripting import *


def __main__( *args ):


	deadlinePlugin = args[0]
	job = deadlinePlugin.GetJob()
	outputDirectories = job.OutputDirectories
	outputFilenames = job.OutputFileNames


	outputDirectory = outputDirectories[0]
	outputFilename  = outputFilenames[0]

	out_file = os.path.join(outputDirectory,outputFilename)
	out_file = out_file.replace('\\', '/')


	meta_script = out_file.split('/')
	meta_script.insert(-1, 'scripts')
	meta_script = '/'.join(meta_script).split('.')[0]+'__meta_chapters__.txt'


	mov = out_file
	meta = meta_script


	sys.path.append("X:/apps/Scripts/FTRACK/python-lib/site-packages")
	sys.path.append("X:/apps/Scripts/FTRACK/python-lib")
	sys.path.append("//qumulo/Libraries/HAL/LUX_SLATE/nuke_templates")
	import cis_parser

	#args = sys.argv
	#mov = args[-2]
	#meta = args[-1]


	cis = cis_parser.Nuke_CIS()
	baked_file = cis.bake_meta_into_file(mov, meta, ret=True)