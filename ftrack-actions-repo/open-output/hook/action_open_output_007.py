import logging
import ftrack_api
import os
import re
import sys
import subprocess

try:
    import ftrack
except:
    pass
import getpass

import datetime

import io

import traceback
from shutil import copyfile
from subprocess import *
import sys


#sys.path.append("X:/apps/Scripts/FTRACK/ftrack_hooks/slate_assets_hook/hook")
sys.path.append("X:/apps/Scripts/FTRACK/python-lib")
sys.path.append("X:/apps/Scripts/FTRACK/python-lib/lux_utils")
from lux_utils.get_latest_from import get_latest_from

import fileinput

import re


os.environ["PYTHONHOME"] = r"C:\Python27"
os.environ["PYTHONPATH"] = r"C:\Python27\Lib"

# setup ftrack environment
try:
    sys.path.insert(0,"L:/HAL/LIVEAPPS/apps/Scripts/FTRACK/ftrack_events/resources")
    import credentials

    os.environ["FTRACK_SERVER"]  = credentials.server_url
    os.environ["FTRACK_API_KEY"] = credentials.api_key

except ImportError:
    print("No \"config\" found.")

def striprtf(text):
   pattern = re.compile(r"\\([a-z]{1,32})(-?\d{1,10})?[ ]?|\\'([0-9a-f]{2})|\\([^a-z])|([{}])|[\r\n]+|(.)", re.I)
   # control words which specify a "destionation".
   destinations = frozenset((
      'aftncn','aftnsep','aftnsepc','annotation','atnauthor','atndate','atnicn','atnid',
      'atnparent','atnref','atntime','atrfend','atrfstart','author','background',
      'bkmkend','bkmkstart','blipuid','buptim','category','colorschememapping',
      'colortbl','comment','company','creatim','datafield','datastore','defchp','defpap',
      'do','doccomm','docvar','dptxbxtext','ebcend','ebcstart','factoidname','falt',
      'fchars','ffdeftext','ffentrymcr','ffexitmcr','ffformat','ffhelptext','ffl',
      'ffname','ffstattext','field','file','filetbl','fldinst','fldrslt','fldtype',
      'fname','fontemb','fontfile','fonttbl','footer','footerf','footerl','footerr',
      'footnote','formfield','ftncn','ftnsep','ftnsepc','g','generator','gridtbl',
      'header','headerf','headerl','headerr','hl','hlfr','hlinkbase','hlloc','hlsrc',
      'hsv','htmltag','info','keycode','keywords','latentstyles','lchars','levelnumbers',
      'leveltext','lfolevel','linkval','list','listlevel','listname','listoverride',
      'listoverridetable','listpicture','liststylename','listtable','listtext',
      'lsdlockedexcept','macc','maccPr','mailmerge','maln','malnScr','manager','margPr',
      'mbar','mbarPr','mbaseJc','mbegChr','mborderBox','mborderBoxPr','mbox','mboxPr',
      'mchr','mcount','mctrlPr','md','mdeg','mdegHide','mden','mdiff','mdPr','me',
      'mendChr','meqArr','meqArrPr','mf','mfName','mfPr','mfunc','mfuncPr','mgroupChr',
      'mgroupChrPr','mgrow','mhideBot','mhideLeft','mhideRight','mhideTop','mhtmltag',
      'mlim','mlimloc','mlimlow','mlimlowPr','mlimupp','mlimuppPr','mm','mmaddfieldname',
      'mmath','mmathPict','mmathPr','mmaxdist','mmc','mmcJc','mmconnectstr',
      'mmconnectstrdata','mmcPr','mmcs','mmdatasource','mmheadersource','mmmailsubject',
      'mmodso','mmodsofilter','mmodsofldmpdata','mmodsomappedname','mmodsoname',
      'mmodsorecipdata','mmodsosort','mmodsosrc','mmodsotable','mmodsoudl',
      'mmodsoudldata','mmodsouniquetag','mmPr','mmquery','mmr','mnary','mnaryPr',
      'mnoBreak','mnum','mobjDist','moMath','moMathPara','moMathParaPr','mopEmu',
      'mphant','mphantPr','mplcHide','mpos','mr','mrad','mradPr','mrPr','msepChr',
      'mshow','mshp','msPre','msPrePr','msSub','msSubPr','msSubSup','msSubSupPr','msSup',
      'msSupPr','mstrikeBLTR','mstrikeH','mstrikeTLBR','mstrikeV','msub','msubHide',
      'msup','msupHide','mtransp','mtype','mvertJc','mvfmf','mvfml','mvtof','mvtol',
      'mzeroAsc','mzeroDesc','mzeroWid','nesttableprops','nextfile','nonesttables',
      'objalias','objclass','objdata','object','objname','objsect','objtime','oldcprops',
      'oldpprops','oldsprops','oldtprops','oleclsid','operator','panose','password',
      'passwordhash','pgp','pgptbl','picprop','pict','pn','pnseclvl','pntext','pntxta',
      'pntxtb','printim','private','propname','protend','protstart','protusertbl','pxe',
      'result','revtbl','revtim','rsidtbl','rxe','shp','shpgrp','shpinst',
      'shppict','shprslt','shptxt','sn','sp','staticval','stylesheet','subject','sv',
      'svb','tc','template','themedata','title','txe','ud','upr','userprops',
      'wgrffmtfilter','windowcaption','writereservation','writereservhash','xe','xform',
      'xmlattrname','xmlattrvalue','xmlclose','xmlname','xmlnstbl',
      'xmlopen',
   ))
   # Translation of some special characters.
   specialchars = {
      'par': '\n',
      'sect': '\n\n',
      'page': '\n\n',
      'line': '\n',
      'tab': '\t',
      'emdash': '\u2014',
      'endash': '\u2013',
      'emspace': '\u2003',
      'enspace': '\u2002',
      'qmspace': '\u2005',
      'bullet': '\u2022',
      'lquote': '\u2018',
      'rquote': '\u2019',
      'ldblquote': '\201C',
      'rdblquote': '\u201D',
   }
   stack = []
   ignorable = False       # Whether this group (and all inside it) are "ignorable".
   ucskip = 1              # Number of ASCII characters to skip after a unicode character.
   curskip = 0             # Number of ASCII characters left to skip
   out = []                # Output buffer.
   for match in pattern.finditer(text.decode()):
      word,arg,hex,char,brace,tchar = match.groups()
      if brace:
         curskip = 0
         if brace == '{':
            # Push state
            stack.append((ucskip,ignorable))
         elif brace == '}':
            # Pop state
            ucskip,ignorable = stack.pop()
      elif char: # \x (not a letter)
         curskip = 0
         if char == '~':
            if not ignorable:
                out.append('\xA0')
         elif char in '{}\\':
            if not ignorable:
               out.append(char)
         elif char == '*':
            ignorable = True
      elif word: # \foo
         curskip = 0
         if word in destinations:
            ignorable = True
         elif ignorable:
            pass
         elif word in specialchars:
            out.append(specialchars[word])
         elif word == 'uc':
            ucskip = int(arg)
         elif word == 'u':
            c = int(arg)
            if c < 0: c += 0x10000
            if c > 127: out.append(chr(c)) #NOQA
            else: out.append(chr(c))
            curskip = ucskip
      elif hex: # \'xx
         if curskip > 0:
            curskip -= 1
         elif not ignorable:
            c = int(hex,16)
            if c > 127: out.append(chr(c)) #NOQA
            else: out.append(chr(c))
      elif tchar:
         if curskip > 0:
            curskip -= 1
         elif not ignorable:
            out.append(tchar)
   return ''.join(out)




def grabPattern(string, pattern):
    #returns the first matching pattern group in string
    #grabPattern('some string for sure', r"(\d{3})")
    _pattern = re.compile(pattern, re.I)
    _match = _pattern.search(string)
    try:
        _match = _match.group()
        return _match
    except AttributeError:
        return ''
    
def removePattern(string, pattern):
    #removes the result of first pattern from the string
    #removePattern('some string for sure', r"(\d{3})")
    _pattern = re.compile(pattern, re.I)
    _match = _pattern.search(string)

    try:
        _match = _match.group()
        _match = string.replace(_match,'')
        return _match

    except AttributeError:
        return ''


class OpenOutput(object):
    '''Custom action.'''

    label = 'Open Output'
    identifier = 'open.output.custom.version'
    description = 'This will open various versions of the output of a task'
    #icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/937300-200.png'
    #description = 'Launch Output'
    icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/937300-200.png'
    variant = 'Custom Version'

    def __init__(self, session):
        '''Initialise action.'''
        super(OpenOutput, self).__init__()
        self.session = session
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def register(self):

        try:
            ftrack.EVENT_HUB.subscribe(
                'topic=ftrack.action.discover and source.user.username={0}'.format(
                    getpass.getuser()
                ),
                self.discover
            )

            ftrack.EVENT_HUB.subscribe(
                'topic=ftrack.action.launch and source.user.username={0} '
                'and data.actionIdentifier={1}'.format(
                    getpass.getuser(), self.identifier
                ),
                self.launch
            )
        except:
            self.session.event_hub.subscribe(
                'topic=ftrack.action.discover',
                self.discover
            )


            self.session.event_hub.subscribe(
                'topic=ftrack.action.launch and data.actionIdentifier={0}'.format(
                    self.identifier),
                self.launch
            )
    '''
    def register(self):

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                getpass.getuser()
            ),
            self.discover
        )

        ftrack.EVENT_HUB.subscribe(
            'topic=ftrack.action.launch and source.user.username={0} '
            'and data.actionIdentifier={1}'.format(
                getpass.getuser(), self.identifier
            ),
            self.launch
        )
    '''
    def discover(self, event):
        '''Return action config if triggered on a single asset version.'''
        data = event['data']

        # If selection contains more than one item return early since
        # this action can only handle a single version.
        selection = data.get('selection', [])
        self.logger.info('Got selection: {0}'.format(selection))
        #if len(selection) != 1 or selection[0]['entityType'] != 'assetversion':
        #    return

        return {
            'items': [{
                'label': self.label,
                'description': self.description,
                'actionIdentifier': self.identifier,
                'icon': self.icon,
                'variant': self.variant
            }]
        }

    def launch(self, event):
        '''Callback method for custom action.'''

        data = event['data']

        selection = data.get('selection', [])

        entityTypes = ['Project', 'Episode', 'Sequence', 'Shot', 'Task']

        dept_folders = ['01_PLATES','02_INPUT','03_COORDINATION','04_3D','05_COMP','06_RENDERS','07_DAILIES','08_PFTrack','09_QT']

        session = ftrack_api.Session()

        #if os.path.isdir(template_files_dir):
        #    template_files = [i for i in os.listdir(template_files_dir) if i[-3:] == '.nk']

        master_dict = []

        index = 0

        #gather shot items from selection
        for entity in selection:

            num = 0
            sel_type = entityTypes[num]
            item = session.query('select name from {0} where id is {1}'.format(sel_type, entity['entityId'])).first()

            episodic = False

            while item == None:

                num += 1
                sel_type = entityTypes[num]
                item = session.query('select name from {0} where id is {1}'.format(sel_type, entity['entityId'])).first()

            #project_id = item['project_id']

            #proj = session.query('select custom_attributes from Project where id is "{0}"'.format(project_id)).first()

            object_name = item['name']
            
            item_type = item['object_type']['name']

            #if its a shot, get the frame duration and shot specific attributes
            if item_type == 'Shot':
                task = [i for i in item['descendants'] if (i['object_type']['name'] == 'Task') and (i['name'] == 'Compositing')][0]
                shot = item
                pass
            #if its a task, get the frame duration from its ancestor
            if item_type == 'Task':
                shot = [i for i in item['ancestors'] if i['object_type']['name'] == 'Shot'][0]
                task = item
                pass

            shot_name = shot['name']
            task_name = task['name']

            item_title = shot_name + ' ' + task_name

            #from shot
            duration = int(max(1,shot['custom_attributes']['Duration (frames)']))
            first_frame = int(shot['custom_attributes']['first_frame'])
            last_frame = int(shot['custom_attributes']['last_frame'])
            base_path = shot['custom_attributes']['base_path']
            
            #from task
            out_path = task['custom_attributes']['out_path']
            out_path = out_path.replace('\\','/')

            status = task['status']['name']
            description = shot['description']

            item_info = {
                'index' : index,
                'item_title' : item_title,
                'shot_name' : shot_name,
                'task_name' : task_name,
                'duration' : duration,
                'first_frame' : first_frame,
                'last_frame' : last_frame,
                'base_path' : base_path,
                'out_path' : out_path,
                'status' : status,
                'description' : description,
                'image_file': '',
                'metad_file': '',
                'asset_name' : '',
                'versions': [],
                'success': False
            }

            if os.path.isdir(out_path):
                #print 'Slating: ',shot_name
                outputs = os.listdir(out_path)
                #print outputs
                shot_folders = []
                for output in outputs:
                    if (removePattern(output, r"_v(\d{3})$") == shot_name) or (removePattern(output, r"(_[a-zA-Z]*)*_[vV](\d{3})$") == shot_name):
                        if len(os.listdir(os.path.join(out_path, output))) > 0: 
                                shot_folders.append(output)

                shot_folders.sort()
                shot_folders.reverse()

                item_info['versions'] = shot_folders

                #folders_to_search = []#full paths to each shot comp versions
                #last_found_versions = {}
                for folder in shot_folders:
                    
                    full_path = os.path.join(out_path, folder)
                    full_path = full_path.replace('\\','/').replace('//','/')#Q:\TEMP_PROJECT\05_COMP\TEM_001_010\02_OUTPUT\03_comp\TEM_001_010_V007

                    #(jpg_path,dpx_path,exr_path) = full_path
                    jpg_path = full_path
                    dpx_path = full_path
                    exr_path = full_path

                    if task_name == 'Compositing':
                        jpg_path = os.path.join(full_path, 'JPEG')
                        dpx_path = os.path.join(full_path, 'DPX')
                        exr_path = os.path.join(full_path, 'EXR')

                    found_image_folders = []
                    file_types = {}
                    image_file = ''
                    metad_file = ''
                    frame_duration = last_frame - first_frame 
                    

                    if os.path.isdir(jpg_path):
                        imgs = [i for i in os.listdir(jpg_path) if grabPattern(i, shot_name+r"(_[a-zA-Z]*)*_[vV](\d{3})\.\d") != '']
                        if len(imgs) >= 1:#frame_duration:#duration:
                            found_image_folders.append(jpg_path)
                            imgs.sort()
                            file_types['JPEG'] = os.path.join(jpg_path,imgs[0])

                    if os.path.isdir(dpx_path):
                        imgs = [i for i in os.listdir(dpx_path) if grabPattern(i, shot_name+r"(_[a-zA-Z]*)*_[vV](\d{3})\.\d") != '']
                        if len(imgs) >= 1:#frame_duration:#duration:
                            found_image_folders.append(dpx_path)
                            imgs.sort()
                            file_types['DPX'] = os.path.join(dpx_path,imgs[0])

                    if os.path.isdir(exr_path):
                        imgs = [i for i in os.listdir(exr_path) if grabPattern(i, shot_name+r"(_[a-zA-Z]*)*_[vV](\d{3})\.\d") != '']
                        if len(imgs) >= 1:#frame_duration:#duration:
                            found_image_folders.append(exr_path)
                            imgs.sort()
                            file_types['EXR'] = os.path.join(exr_path,imgs[0])

                    if 'JPEG' in file_types:
                        image_file = file_types['JPEG']

                    if 'EXR' in file_types:
                        metad_file = file_types['EXR']

                    if 'DPX' in file_types:
                        metad_file = file_types['DPX']

                    if image_file == '':
                        if metad_file != '':
                            image_file = metad_file

                    if metad_file == '':
                        if image_file != '':
                            metad_file = image_file

                    if image_file != '' and metad_file != '':

                        metad_file = metad_file.replace('\\','/').replace('//','/')
                        image_file = image_file.replace('\\','/').replace('//','/')

                        pad_pattern = grabPattern(metad_file, '\.\d+\.')
                        pads = len(pad_pattern)-2 #-2 to subtract the two dots.
                        new_pad = '#'*pads
                        new_pad = '.'+new_pad+'.'

                        metad_file = metad_file.replace(pad_pattern, new_pad)
                        image_file = image_file.replace(pad_pattern, new_pad)

                        item_info['metad_file'] = metad_file
                        item_info['image_file'] = image_file
                        item_info['asset_name'] = folder
                        #slate_output = os.path.join(project_path, project_name, episode_name, "07_DAILIES/SLATED_OUTPUTS/<TEMPLATE_DESCRIPTOR>", folder+'.mov')
                        #slate_output = 'c:\\program files\\bob.mov'
                        default_base_output = os.path.join(base_path, "07_DAILIES/SLATED_OUTPUTS")
                        item_info['default_base_output'] = default_base_output

                        slate_output = default_base_output

                        slate_output = slate_output.replace('\\','/').replace('//','/')
                        #item_info['slate_output'] = slate_output
                        #print '###################', slate_output
                        item_info['success'] = True
                        break

            else:
                #print 'No outputs rendered: ',shot_name
                pass

            #print shot_info
            #add to master_dict[] if no other dicts with the same 'item_title' value doesnt exist
            add_to_dict = True
            for i in master_dict:
                if i.get('item_title') == item_info.get('item_title'):
                    add_to_dict = False
            if add_to_dict:
                master_dict.append(item_info)
                index += 1
            pass


        shot_items = []

        template_file_entry = {'label': '', 'value':''}
        template_items = []


        for shot in master_dict:

            #project_name = shot['project_name']
            #shot_name = shot['shot_name']
            #image_file = shot['image_file']
            #metad_file = shot['metad_file']
            #output = shot['slate_output']
            duration = shot['duration']
            description = shot['description']
            description = description.encode('utf-8')
            #description = striprtf(description)
            #description = ''
            #success = shot['success']
            asset_name = shot['asset_name']
            index = shot['index']
            version_items = []
            frame_range = '{0}-{1}'.format( str(shot['first_frame']) , str(shot['last_frame']) )
            text = 'Could not locate rendered files.....\r'
            success_msg = 'FAILED'
            if shot['success']:
                success_msg = shot['status']#'SUCCESSFUL'
                text = '''
    Frame Range     : {2} ({3} Frames)\r
    Image sequence  : {0}\r\r
    Description     : {4}\r
'''.format(shot['image_file'],shot['metad_file'],frame_range,duration,description)
            text = text+'<hr>'

            vers_ext = ''
            if asset_name!='':
                vers_ext = '_'+asset_name.split('_')[-1]

            for i in shot['versions']:
                    new_entry =  {}#{dict(template_file_entry)}
                    new_entry['label'] = i
                    new_entry['value'] = i
                    version_items.append(new_entry)

            title = {
                    'value': '<b>{0}{1}</b> : {3}<i>{2}</i>'.format(shot['item_title'], vers_ext, success_msg, '&nbsp;'*2),
                    'type': 'label'
                }

            message = {
                    'value': text,
                    'type': 'label'
                }

            framerange = {
                    'label': 'Frame Range',
                    'type': 'text',
                    'value':frame_range,#'<Project><Episode>_<Sequence>_<Shot>_<Custom Text>_v<Version>',
                    'name': 'framerange_{0}'.format(index)
                }

            if len(version_items) == 0:
                version_items.append( {'label':'None Found..', 'value':None} )

            versions = {
                    'label': 'Version',
                    'type': 'enumerator',
                    'value': version_items[0].get('label'),
                    'data' : version_items,
                    'name': 'version_{0}'.format(index)
                }

            shot_items.append(title)
            shot_items.append(versions)
            #shot_items.append(framerange)
            shot_items.append(message)
            

        totalSelectedItems = 0
        totalSlatedItems = 0
        retSuccess = {
            'success': True,
            'message': 'Slating {0}/{1} items!'.format(totalSlatedItems,totalSelectedItems)
        }

        retUI = {'items': shot_items}

        if 'values' in data:

            # Do something with the values or return a new form.
            values = data['values']

            commit = False
            
            self.logger.info(u'Got values: {0}'.format(values))


            #totalSlatedItems = 0

            #create a new dict from teh asset infos from the UI
            #grab the index from the name of each parameter
            #and add it to the items with matching indexes
            shot_related_params = []
            for value in values:
                if ('_' in value) :
                    if (value.split('_')[-1]).isdigit():
                        shot_related_params.append(value)

            for item in master_dict:
      
                #print item
                #print item
                for p in shot_related_params:
                    p_index = int(p.split('_')[-1])
                    if item['index'] == p_index:
                        if p.split('_')[0] == 'version':
                            item['version'] = values[p]
                        if p.split('_')[0] == 'framerange':
                            first_last = values[p].split('-')
                            item['first_frame'] = str(first_last[0])
                            item['last_frame'] = str(first_last[-1])
                            item['duration'] = str(int(first_last[-1]) - int(first_last[0]) + 1)


                if item['success']:

                    #totalSlatedItems += 1

                    item['image_file'] = item['image_file'].replace(item['asset_name'],item['version'])
                    item['metad_file'] = item['metad_file'].replace(item['asset_name'],item['version'])
                    #item['slate_output'] = item['slate_output'].replace(item['asset_name'],item['version'])

                    item['asset_name'] = item['version']


                    exe = '"C:/Program Files/djv-1.1.0-Windows-64/bin/djv_view.exe"'
                    exe = '"\\\\qumulo\\LiveApps\\apps\\DJV\\DJV-1.3.0-win64\\bin\\djv_view.exe"'
                    if not os.path.isfile(exe.replace('"', '')):
                        #return early
                        return {
                            'success': False,
                            'message': 'Couldnt find DJ_View <br>exe : {0}'.format(exe)
                        }
                    #file = image_asset
                    file = item['image_file']
                    args = exe + ' ' + file
                    subprocess.Popen(args, shell=False)



            retSuccess = {
                'success': True,
                'message': 'Opening outputs'
            }
            '''
            if not totalSlatedItems:
                retSuccess['success'] = False
            '''
            return retSuccess

        return retUI

        
def register(session, **kw):
    '''Register plugin.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    action = OpenOutput(session)
    action.register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()