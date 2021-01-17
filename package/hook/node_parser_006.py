'''
Nuke script parser
Alican Sesli
LUX Visual Effects
28.11.2019
'''

import os,sys
import re


from shutil import copy2

class nukeParser():
	'''	This script is to be used when replacing nodes and knobs from a .nk script when packaging a final shot and its assets.
			- the replaceFilesAndNodes() : executes a very specific operation on the script to do this...
		This can also be used to analyze an .nk script and return information such as node list, file inputs/outputs, knob and values.
		It will parse the .nk as txt file, find nodes and knobs and then functions can be run on them. Here are some useful functions for this.
			- getNodeStates() : returns a list of all nodes that are active and inactive
			- getNodeKnobs()  : returns a dict of all nodes, knobs and their values
			- getFileInputs() : returns a list of strings with file path information.
	'''

	def __init__(self, script):

		self.nk_script = script
		#self.nk_script = "Q:/Omens/OMS101/05_COMP/OMS101_015_080/OMS101_015_080_Comp_V011.nk"
		#self.nk_script = "Q:/Omens/OMS101/05_COMP/OMS101_062_160/OMS101_062_160_Comp_V025.nk"

		self.add_project_directory = r'project_directory "\[python \{nuke.script_directory()\}]"'

		self.re_nodes = r"[A-Z].* \{\n(.{3,}\n)*\}"
		self.re_nodes = re.compile(self.re_nodes, re.M)

		self.re_node_class = r"^[A-Z].* \{\n"
		self.re_node_class = re.compile(self.re_node_class, re.M)

		self.re_lux_write = r"^Group {\nname LUX_Write.*(\n.{3,})*\n\}\n"
		self.re_lux_write = re.compile(self.re_lux_write)

		self.re_group = r"^Group {\n((.{2,}\n)*\}\n)([^\}]+\}\n){1,}end_group"
		self.re_group = re.compile(self.re_group, re.M)

		self.re_name_knob = r"^name .*\n"
		self.re_name_knob = re.compile(self.re_name_knob)

		self.re_disable_knob = r"disable true"
		self.re_disable_knob = re.compile(self.re_disable_knob)

		self.re_file_knob = r"^file [a-zA-Z].*\n"
		self.re_file_knob = re.compile(self.re_file_knob, re.M)

		self.re_vfield_file_knob = r"^vfield_file [a-zA-Z].*\n"
		self.re_vfield_file_knob = re.compile(self.re_vfield_file_knob, re.M)

		self.re_first_knob = r"^first -?\d*\n"
		self.re_first_knob = re.compile(self.re_first_knob, re.M)

		self.re_last_knob = r"^last -?\d*\n"
		self.re_last_knob = re.compile(self.re_last_knob, re.M)

		self.re_first_frame_knob = r"^((first_frame)|(first)) -?\d*\n"
		self.re_first_frame_knob = re.compile(self.re_first_frame_knob, re.M)

		self.re_last_frame_knob = r"^((last_frame)|(last)) -?\d*\n"
		self.re_last_frame_knob = re.compile(self.re_last_frame_knob, re.M)

		self.re_fps_knob = r"^fps \d*\.?(\d)*\n"
		self.re_fps_knob = re.compile(self.re_fps_knob, re.M)

		self.re_format_knob = r"^format \".*\"\n"
		self.re_format_knob = re.compile(self.re_format_knob, re.M)

		self.re_knobs = r"^\S* .*$"
		self.re_knobs = re.compile(self.re_knobs, re.M)

		self.all_nodes_txt = ''

		with open(self.nk_script, "r") as file:

			self.all_nodes_txt = file.read()

		#self.do()

	def allNodes(self, *args, **kwargs):
		'''returns all nodes. output is slightly different than nukes output.
		returns [{ node:{ knob1:knobval1,knob2:knobval2 } },{ node2:{ knob1:knobval1,knob2:knobval2 } }, etc] old
		returns [{ node:{ knob1:knobval1,knob2:knobval2 }, ascii:'ascii node'},{ node2:{ knob1:knobval1,knob2:knobval2 },ascii:'ascii node' }, etc] new
		'''

		nodes = [node.group() for node in re.finditer(self.re_nodes, self.all_nodes_txt)]
		search_knobs = None
		nodename = None
		#has these knobs..
		if kwargs.get('knobs'):
			search_knobs = kwargs['knobs']


		#has the name..
		if kwargs.get('name'):
			nodename = kwargs['name']

		nclass = []
		for a in args:
			if type(a) is list:
				nclass+=a
			else:
				nclass.append(a)

		all_nodes = []

		for node in nodes:
			knobs = [knob.group() for knob in re.finditer(self.re_knobs, node)] #list of knobs and values as txt
			node_class = knobs[0].replace(' {','')

			if (nclass and node_class in nclass) or (not nclass):

				knobs = knobs[1::]
				node_knobs = {node_class:{},'ascii':node}

				for knob in knobs:
					knob_name = knob.split(' ')[0]
					knob_val = ' '.join(knob.split(' ')[1::])
					node_knobs[node_class][knob_name]=knob_val


				if (search_knobs and [i for i in node_knobs[node_class].keys() if i in search_knobs]) or (not search_knobs):

					if (node_knobs[node_class].get('name') == nodename) or (not nodename):
						
						all_nodes.append(node_knobs)
		#print all_nodes
		return all_nodes
	
	def toNode(self, nodename):
		'''Behaves like nuke.toNode('NodeName')'''
		node = self.allNodes(name=nodename)

		return node

	def nodeToASCII(self, node):
		'''converts a single node item to ascii
			returns a dict with new_ascii and ascii. 
				new_ascii = the node converted into ascii, 
				ascii = the unmodified ascii from node
		'''
		'''
		node=[{
		'Read': {
			'inputs': '0', 
			'xpos': '-40', 
			'last': '1052', 
			'name': 'Read1', 
			'tile_color': '0x44ba11ff', 
			'file_type': 'exr', 
			'localizationPolicy': 'off', 
			'ypos': '-33', 
			'file': 'Q:/Omens/OMS101/01_PLATES/OMS101_062_150/PLATE/PLATE_O/01_EXRS/OMS101_062_150.####.exr', 
			'origset': 'true', 
			'first': '1001'
		}}]

		'''
		a = ''

		node = node[0]
		#nclass = node.keys()[0]
		nclass = filter(lambda x: x != 'ascii',node.keys())[0]
		#print nclass

		a = '{} {{\n'.format(nclass)
		for knob in sorted(node[nclass]):
			a+= '{} {}\n'.format(knob, node[nclass][knob])
		a+='}'

		ret = {'new_ascii':a, 'ascii':node['ascii']}

		return ret

	def groupedNodes(self):
		''' returns all nodes inside of groups'''
		groups = [group.group() for group in re.finditer(self.re_group, self.all_nodes_txt)]
		nodes_in_group = []
		for group in groups:

			group_nodes = [node.group() for node in re.finditer(self.re_nodes, group)] #List of each node as txt
			#group_node_class_name = 
			grouped_node = {'Group':{},'ascii':group}
			
			for node in group_nodes:#[1::]:#Ignore the group container, just find the nodes inside of the group
				knobs = [knob.group() for knob in re.finditer(self.re_knobs, node)] #list of knobs and values as txt
				node_class = knobs[0].replace(' {','')
				#print node_class
				knobs = knobs[1::]
				node_knobs = {node_class:{}}
				#grouped_node[node_class] = node_knobs
				grouped_node['Group'][node_class] = node_knobs

				for knob in knobs:
					knob_name = knob.split(' ')[0]
					knob_val = ' '.join(knob.split(' ')[1::])
					#node_knobs[node_class][knob_name]=knob_val
					grouped_node['Group'][node_class][knob_name]=knob_val

			nodes_in_group.append(grouped_node)
		
		return nodes_in_group	


	def getNodeStates(self, node_dict_list):

		node_type_dict = {}
		active_node_type_dict = {}

		for nodes in node_dict_list:

			#for node in nodes:
			
			nclass = filter(lambda x: x != 'ascii',nodes.keys())[0]
			
			#print nclass
			
			if nclass not in node_type_dict:
				node_type_dict[nclass] = 1
				if nodes[nclass].get('disable') == None:
					active_node_type_dict[nclass] = 1
				else:
					active_node_type_dict[nclass] = 0
			else:
				node_type_dict[nclass] = node_type_dict[nclass]+1
				if nodes[nclass].get('disable') == None:
					active_node_type_dict[nclass] = active_node_type_dict[nclass]+1
				else:
					active_node_type_dict[nclass] = 0

		#print node_type_dict 
		#print active_node_type_dict

		message = ''

		message+= '\nAll nodes: '+ str(len(node_dict_list))+'\n'
		for node in sorted(node_type_dict.keys()):
			message+= node + ' {0}/{1}\n'.format(active_node_type_dict[node], node_type_dict[node])

		return message

	def getNodeKnobs(self, node_dict_list, *args):

		knobs = []
		#print args
		for k in args:
			if type(k) is list:
				knobs+=k
			else:
				knobs.append(k)

		node_list = []
		message = ''
		for nodes in node_dict_list:
			knobs_dict = {}
			#print nodes.keys()
			node = filter(lambda x: x != 'ascii',nodes.keys())[0]
			#node = nodes.keys()[0]
			#for node in nodes:
			#if ([i for i in nodes[node] if i in knobs]) or (not knobs):

			message+= node+'\n'

			for knob in nodes[node]:

				if (knob in knobs) or (not knobs):

					message+= ' '+knob+' '+str(nodes[node][knob])+'\n'
					knobs_dict[knob]=str(nodes[node][knob])

			node_list.append(knobs_dict)
		#if verbose:
		#	print message
		return node_list

	def getFileInputs(self, node_dict_list, detailed=False):

		file_list = []

		for nodes in node_dict_list:
			#for node in nodes:
			#node = nodes.keys()[0]
			#node = nodes[node]

			message = ''

			node = nodes[filter(lambda x: x != 'ascii',nodes.keys())[0]]


			if node.get('file'):
				if detailed:
					message += str(node.get('name')) +' '+ str(node.get('file')) +' '+ str(node.get('first')) +','+ str(node.get('last'))
				else:
					message += str(node.get('file'))

			elif node.get('vfield_file'):
				if detailed:
					message += str(node.get('name')) +' '+ str(node.get('vfield_file')) +' '+ str(node.get('first')) +','+ str(node.get('last'))
				else:
					message += str(node.get('vfield_file'))

			if message:
				file_list.append(message)

		return sorted(set(file_list))



	def saveModifiedNode(self, node):
		'''returns the script ascii after replacing an item
		modifies the self.all_nodes_txt with the modified node'''

		node = self.nodeToASCII(node)

		old = node['ascii']
		new = node['new_ascii']

		self.all_nodes_txt = self.all_nodes_txt.replace(old, new)

		return self.all_nodes_txt

	def replaceAscii(self, ascii_old, ascii_new):

		old = ascii_old
		new = ascii_new

		self.all_nodes_txt = self.all_nodes_txt.replace(old, new)

		return self.all_nodes_txt
 
	def replaceLUXWrites(self):
		
		for i in self.groupedNodes():
			#print i['ascii']

			#print i['Group']
			#print self.getNodeKnobs([i])
			#print [i['Group']]
			
			
			#print i['Group']['Group']['name']
			knobs = {
				'name':i['Group']['Group']['name'],
				'main_dir':i['Group']['Group']['main_dir'],
				'xpos':i['Group']['Group']['xpos'],
				'ypos':i['Group']['Group']['ypos']
				}
			#knobs = self.getNodeKnobs([i['Group']],'name','main_dir','xpos','ypos')
			#print '---',knobs

			#print '----',knobs.get('name')
			if 'LUX_Write' in i['Group']['Group']['name']:#knobs.get('name') :
				#print knobs.get('main_dir')
				#print i['ascii']
				#print self.groupToNoOp(knobs.get('main_dir'))
				#print i['Group']['Group']['main_dir']
				#print '########'
				self.replaceAscii(i['ascii'], self.groupToNoOp(knobs))

			#print '##########################'
		return self.all_nodes_txt
	
	def groupToNoOp(self, knobs):
		#'NoOp {{\ntile_color 0xffbf00ff\naddUserKnob {20 User}\naddUserKnob {2 file}\nfile ''\n}}'
		#print knobs
		#print 'asd'
		xpos = str(knobs.get('xpos'))
		ypos = str(knobs.get('ypos'))
		file = str(knobs.get('file'))
		name = str(knobs.get('name'))
		if file.lower()=='none':
			file = str(knobs.get('main_dir'))

		noop=[{
				'NoOp': {
					'inputs': '1', 
					'xpos': xpos, 
					'name': name, 
					'tile_color': '0xffbf00ff',  
					'ypos': ypos, 
					'addUserKnob': '{20 User}', 
					'addUserKnob': '{2 file}', 
					'file': file
				},
				'ascii': ''
				}]




		noop = self.nodeToASCII(noop)
		return noop['new_ascii']


	def modifyNode(self, node, **kwargs):
		#this will modify a nodes knob based on the kwargs

		#node = node[0][node[0].keys()[0]]
		#print kwargs
		#existing_knobs = node[0][filter(lambda x: x != 'ascii',node[0].keys())[0]].keys()
		for a in kwargs:
			knob = a
			val = kwargs[a]

			#if knob in existing_knobs: <---problematic when adding a value that is different from default. Default settings will not get saved to the nk file. 
			#	node[0][ filter(lambda x: x != 'ascii',node[0].keys())[0] ][knob] = val

			node[0][ filter(lambda x: x != 'ascii',node[0].keys())[0] ][knob] = val

		return node

	def scriptSaveAs(self, new_script):
		'''saves the ascii script into an nk file
			script must be ascii txt
			new_script must be path to the new file'''

		script = self.all_nodes_txt


		if not os.path.isdir(os.path.dirname(new_script)):
			os.makedirs(os.path.dirname(new_script))
		with open(new_script, "w+") as file:

			file.write(script)

		return new_script
	#Print node group dict

	def replaceFilesAndNodes(self):

		#self.replaceLUXWrites()

		all_nodes = self.allNodes()
		#read_node = self.toNode('Read1')
		input_nodes = self.allNodes('Read', 'OCIOFileTransform', 'Vectorfield', 'Camera2', 'ReadGeo2', knobs=['vfield_file', 'file'])
		output_nodes = self.allNodes('Write', 'NoOp', 'MatchGrade', 'WriteGeo', knobs=['outfile', 'file'])
		#print read_nodes

		

		#Root Info
		root_node = self.allNodes('Root')
		root = root_node[0]['Root']
		#print 'Root: {0}-{1} @ {2}fps'.format(root['first_frame'], root['last_frame'], root['fps'])
		
		#Nodes List
		print self.getNodeStates(all_nodes)

		#File Inputs
		for f in self.getFileInputs(input_nodes, detailed=False):
			#Needs to check to see if f is disabled!!!! we dont want to gather unused inputs.
			#print f
			pass
		for f in self.getFileInputs(output_nodes, detailed=False):
			#Needs to check to see if f is disabled!!!! we dont want to gather unused inputs.
			#print f
			pass
		#Knob List
		#self.getNodeKnobs(all_nodes,verbose=False)
		
		
		outs = []
		ins = []

		def _split_file_paths(_file):
			_file = _file.replace('\\','/')
			_file = _file.split('01_PLATES')[-1].split('02_INPUT')[-1].split('03_COORDINATION')[-1].split('04_3D')[-1].split('05_COMP')[-1].split('06_RENDERS')[-1].split('07_DAILIES')[-1].split('08_PFTrack')[-1].split('09_QT')[-1]
			_file = _file.split('/Sequences')[-1].split('/06_Image_Lib')[-1].split(':')[-1]
			_file = _file.replace('\\','/').replace('//','/')
			return _file

		#for i in input_nodes:
		#print self.getNodeKnobs(input_nodes, 'vfield_knob', 'file', 'name')
		inputs = self.getNodeKnobs(input_nodes, 'vfield_file', 'file', 'name')
		for i in inputs:
			#print i
			node = self.toNode(i['name'])
			if i.get('file'):
				file_path = i['file']
			elif i.get('vfield_file'):
				file_path = i['vfield_file']
			original_path = file_path
			#file_path = file_path.split('05_COMP')[-1].split('01_PLATES')[-1].split('06_RENDERS')[-1]
			file_path = _split_file_paths(file_path)
			#file_path = os.path.join('/SOURCED_ASSETS/',file_path)
			file_path = 'SOURCED_ASSETS/'+file_path

			file_path = file_path.replace('\\','/').replace('//','/')
			#print original_path
			#print file_path
			#print file_path
			if i.get('file'):
				node = self.modifyNode(node, file=file_path)
			elif i.get('vfield_file'):
				node = self.modifyNode(node, vfield_file=file_path)
			self.saveModifiedNode(node)
			#ins.append( {'original':original_path, 'new':file_path} )
			ins.append( {'original':r'{}'.format(original_path), 'new':r'{}'.format(file_path)} )


		outputs = self.getNodeKnobs(output_nodes, 'outfile', 'file', 'name')
		for i in outputs:
			#print i
			node = self.toNode(i['name'])
			if i.get('file'):
				file_path = i['file']
			elif i.get('outfile'):
				file_path = i['outfile']
			original_path = file_path
			#file_path = file_path.split('05_COMP')[-1].split('01_PLATES')[-1].split('06_RENDERS')[-1]
			file_path = _split_file_paths(file_path)
			#file_path = os.path.join('/SOURCED_ASSETS',file_path)
			file_path = 'SOURCED_ASSETS/'+file_path
			file_path = file_path.replace('\\','/').replace('//','/')
			
			#print original_path
			#print file_path
			if i.get('file'):
				node = self.modifyNode(node, file=file_path)
			elif i.get('outfile'):
				node = self.modifyNode(node, outfile=file_path)

			self.saveModifiedNode(node)

			#outs.append( {'original':original_path, 'new':file_path} )
			outs.append( {'original':r'{}'.format(original_path), 'new':r'{}'.format(file_path)} )
		file_dict = {'outputs': outs, 'inputs':ins }
		


		root_node = self.modifyNode(root_node, project_directory='"[python {nuke.script_directory()}]"')
		#print root_node
		self.saveModifiedNode(root_node)



		#MODIFY INDIVIDUAL NODES FILE PARAMETER
		#node = self.toNode('Read1')
		#node = self.modifyNode(node, name='bob')
		#node = self.modifyNode(node, first='1111')
		#self.saveModifiedNode(node)


		#SAVE THE SCRIPT
		#self.scriptSaveAs(self.all_nodes_txt,"Q:/Omens/OMS101/05_COMP/OMS101_062_150/OMS101_062_150_Comp_V099.nk")




		#x = self.nodeToNoOp()


		#print self.getNodeKnobs()

		'''
		node = self.toNode('Read1')
		node = self.modifyNode(node, name='bob')
		node = self.modifyNode(node, first='1111')
		new_script = self.saveModifiedNode(node)
		print self.scriptSaveAs(new_script,"Q:/Omens/OMS101/05_COMP/OMS101_062_150/OMS101_062_150_Comp_V099.nk")
		'''



		#w = write_nodes
		#print self.getNodeKnobs(self.allNodes('Group'), 'name','main_dir','version')
		#print self.getNodeKnobs(self.allNodes('NoOp'))

		'''

		ideal workflow
		node = self.toNode('Read1')
		node = node.modify(name='bob')
		node = node.toAscii()


		'''

		#print self.nodeToASCII(self.toNode('Read1'))

		#print len(self.groupedNodes())

		#for i in self.groupedNodes():
		#	print i.keys()
		#	print i['Group']['Group']['name']
		'''
		print_grps=1
		if print_grps:
			for group in self.groupedNodes():
				#print group.keys()
				for nodes in filter(lambda x: x != 'ascii',group.keys()):
					print nodes
					#print group[nodes].keys()
					for node in group[nodes].keys():
						print ' ',node
						for knob in group[nodes][node].keys():
							print '  ',knob, group[nodes][node][knob]

		'''
		#print '$$$$$$$$$'


		

		
		#print self.getNodeKnobs(self.toNode('Read1'),'name')

		
		return file_dict


class copyNukeFiles():
	'''
	This way copies the _input file into the folder of the _output
	example inputs:
	_input  = 'Q:/Omens/OMS101/05_COMP/OMS101_062_150/02_OUTPUT/01_precomp/OMS101_062_150_CUTREF_v01/OMS101_062_150_CUTREF_v01.####.jpeg'
	_output = 'Q:/Omens/OMS101/03_COORDINATION/Comppackage_2019-11-26/OMS101_062_150/SOURCED_ASSETS/OMS101_062_150/02_OUTPUT/01_precomp/OMS101_062_150_CUTREF_v01/OMS101_062_150_CUTREF_v01.####.jpeg'
	
	or

	This way copies the folder's ingredients while preserving hiearchy structure 
	example inputs:
	_input  = 'Q:/Omens/OMS101/05_COMP/OMS101_062_150/02_OUTPUT/01_precomp/face_anim_proj/face_anim_proj_V001/' <--with '/' at the end
	_output = 'Q:/Omens/OMS101/03_COORDINATION/Comppackage_2019-11-26/OMS101_062_150/SOURCED_ASSETS/OMS101_062_150/02_OUTPUT/01_precomp/face_anim_proj/face_anim_proj_V001/' <--with '/' at the end

	both input and output should be same type. They are either both folders, or both files. Dont mix and match. 

	'''


	def __init__(self, _input, _output):

		self.input = _input
		self.output = _output
		self.image_types = ['exr', 'dpx', 'jpg', 'jpeg', 'tif', 'tiff', 'tga', 'targa', 'png', 'hdr', 'mov']

		self.copyAsset()

		pass

	def copyAsset(self):


		in_folder_path = os.path.dirname(self.input)
		out_folder_path= os.path.dirname(self.output)
		file_name = os.path.basename(self.input)
		file_title = file_name.split('.')[0]
		file_type = file_name.split('.')[-1]
		
		print 'in  :',self.input
		print 'out :',self.output
		print 'in path :', in_folder_path
		print 'out_path:', out_folder_path
		print 'file    :', file_name
		print 'ext     :', file_type
		print 'title   :', file_title
		
		if file_name:# copying a file
			files = sorted([os.path.join(in_folder_path,i) for i in os.listdir(in_folder_path) if (i.split('.')[-1] == file_type) and i.split('.')[0] == file_title])

			#print files

			#print os.listdir(in_folder_path)
			if not os.path.isdir(out_folder_path):
				os.makedirs(out_folder_path)
			for i in files:
				final_file = os.path.join(out_folder_path, os.path.basename(i)).replace('\\','/').replace('//','/')
				if not os.path.isfile(final_file):
					print i, '>>>', final_file
					copy2(i, out_folder_path)

		else: # copying from a folder

			for root, dirs, files in os.walk(in_folder_path):
				files = sorted([ root.replace('\\','/')+'/'+f for f in files if (f.split('.')[-1] in self.image_types) and (f.split('.')[0] == in_folder_path.split('/')[-1])])

				r_folder = root.replace(in_folder_path,out_folder_path)
				if not os.path.isdir(r_folder):
					os.makedirs(r_folder)

				for f in files:
					final_file = f.replace(in_folder_path,out_folder_path).replace('\\','/').replace('//','/')
					if not os.path.isfile(final_file):
						#print o
						print f, '>>>', final_file
						copy2(f, final_file)
				#files = [i.replace(in_folder_path,out_folder_path) for i in files]
				#print files

			pass







def replace_nuke(_nuke_script, _replaced_script):


	package_path    = os.path.dirname(_replaced_script)
	nuke_script     = _nuke_script
	new_script_name = os.path.basename(_replaced_script)
	new_script_path = _replaced_script

	parser = nukeParser(nuke_script)
	file_list = parser.replaceFilesAndNodes()
	parser.scriptSaveAs(new_script_path)

	return file_list




def copy_files(io_list):
	_i = io_list[0]
	_o = io_list[1]
	copyNukeFiles(_i,_o)


def all_in_one():


	progress = 0.0
	progress_inc = 0.0
	file_list_len = 0

	nuke_script = 'Q:/Omens/OMS101/05_COMP/OMS101_062_150/OMS101_062_150_Comp_V004.nk'
	replaced_script = 'Q:/Omens/OMS101/03_COORDINATION/Comppackage_2019-11-26/OMS101_062_150/OMS101_062_150_Comp_V004.nk'
	package_path = os.path.dirname(replaced_script)


	file_list = replace_nuke(nuke_script, replaced_script)





	for i in file_list:
		file_list_len+= len(file_list[i])



	print 'inputs'
	for i in  file_list['inputs']:
		#print i['original'], '---->', i['new']
		_i = i['original']
		_o = (package_path+'/'+i['new']).replace('//','/').replace('\\','/')
		copyNukeFiles(_i,_o)
		

	print 'outputs'
	for o in  file_list['outputs']:
		#print o['original'], '---->', o['new']
		_i = o['original']
		_o = (package_path+'/'+o['new']).replace('//','/').replace('\\','/')
		copyNukeFiles(_i,_o)




if len(sys.argv)>1:
	package_items = eval(sys.argv[1])

	print package_items
	copy_files(package_items)