'''
Cuts-In-Sequence Ftrack Hook
Alican Sesli - LUX VFX - 03.12.2019
Creates a CIS based on selected shots/tasks or single sequence
    v21: Added user key for naming conventions, fixed @ last frame error.
    v22: artists and coord team directory adjustments
    v23: added 3k to the formats
'''
import logging
import ftrack_api
import os
import re
import sys

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


sys.path.append("X:/apps/Scripts/FTRACK/ftrack_hooks/slate_assets_hook/hook")
sys.path.append("X:/apps/Scripts/FTRACK/python-lib")

from lux_utils.get_latest_from import get_latest_from

import fileinput


os.environ["PYTHONHOME"] = r"C:\Python27"
os.environ["PYTHONPATH"] = r"C:\Python27\Lib"

FTRACK_URL = 'https://domain.ftrackapp.com'
FTRACK_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

os.environ['FTRACK_SERVER'] = FTRACK_URL
os.environ['FTRACK_API_KEY'] = FTRACK_KEY

#Translates the text fields to a format nuke can understand
def translate(_text, _values, _item):

    #shot/asset specific items
    #item = _item
    #master return dialog 
    #values = _values
    #'<None>','<Date>','<ShotCode>','<FrameRange>','<Description>','<Custom>', '<AssetName>'
    sequence_num = _item['shot_name'].split('_')[1]
    shot_num = _item['shot_name'].split('_')[-1]
    episode_num = removePattern(_item['episode_name'], r'\D*')
    episode_num = episode_num.replace('_','').replace(' ','')
    version_num = _item['version'].lower().split('_v')[-1]
    tag_replace = _text#.lower()
    tag_replace = tag_replace.replace('<', '{')
    tag_replace = tag_replace.replace('>', '}')
    user = getpass.getuser()
    if user not in ['luxrj', 'jenniferk', 'luxryan']:

        tdir = "L:/User/{}/".format(user)
        _item['default_base_output'] = tdir

        if not os.path.isdir(tdir):
            os.makedirs(tdir)

    format_name = _item['format']
    format_name = format_name.split(' ')[7::]
    format_name = ' '.join(format_name)

    now = datetime.datetime.now()
    #date_str = now.strftime("%Y-%m-%d-%H%M")
    time = now.strftime("%H%M")

    tag_replace = tag_replace.format(
        none='',
        project=_item['project_code'],
        firstframe=str(_item['first_frame']),
        lastframe=str(_item['last_frame']),
        framecounter='[frame] ( ' + str(_item['first_frame'])+' - '+str(_item['last_frame']) + ' )',
        framerange=str(_item['first_frame'])+' - '+str(_item['last_frame']),
        projectname=_item['project_name'],
        duration="[expression [value [value label].last]-[value [value label].first]+1]",
        episode=episode_num,
        episodename=_item['episode_name'],
        sequence=sequence_num,
        sequencename=_values['sequencename'],
        shot=shot_num,
        version=version_num,
        task=_item['task_name'],
        #slatename=_item['slate_name'],
        format=format_name,
        defaultoutput=_item['default_base_output'],
        description=_values['description_text'],
        custom=_values['custom_text'],
        shotname="[join [lrange [split [lrange [split [value [value label].file] '/'] end end ] '_'] 0 2] _]",#_item['shot_name'],
        assetname=_item['asset_name'],
        codec=_item['codec'],
        colorspacein=_item['colorspace_in'],
        colorspaceout=_item['colorspace_out'],
        logo='logo',
        imagename="[lrange [split [lrange [split [value [value label].file] '/'] end end ] '.'] 0 0]",
        status=_item['status'],
        lens=_item['lens'],
        slatetype=_item['slate_type'],
        timecode="[python {nuke.toNode(nuke.toNode('Text_Slate_Project_Title')['label'].value()).metadata()['input/timecode']}]",
        time=time,
        user=user,
        date=_values['date'])
    _text = tag_replace

    return _text

#Craetes a nuke slate file from a pre existing nuke template
def CreateNukeSlateFile(_slatefile, _template, _items):
    copyfile(_template, _slatefile)
    print 'Slate file created: ', _slatefile
    # modify the nuke newly copied nk file.
    
    def _replaceAll(_slatefile,searchExp,replaceExp):
        try:
            slate_file.close()
        except:
            pass

        slate_file = fileinput.input(_slatefile, inplace=1)

        for line in slate_file:
            if searchExp in line:
                line = line.replace(searchExp,replaceExp)
            sys.stdout.write(line)
        slate_file.close()


    _replaceAll(_slatefile, 'nuke_library_items', str(_items))

#Creates a job_info and pugin_info files
def CreateNukeJob( _file, _frames, _asset, _outputImage, _user, _job_info, _plugin_info, _post_job_script):

    
    global scriptDialog

    version = 10.5
    
    # Check the Nuke files.
    sceneFiles = [_file]
    if( len( sceneFiles ) == 0 ):
        scriptDialog.ShowMessageBox( "No Nuke file specified", "Error" )
        return

    # Check if a valid frame range has been specified.
    frames = _frames

    successes = 0
    failures = 0
    #print _asset
    # Submit each scene file separately.
    for sceneFile in sceneFiles:
        jobName = _asset + " CIS Submission"
        comments = [_outputImage.split('/')[-1], '('+_frames+')']
        comment = ' '.join(comments)
        if len(sceneFiles) > 1:
            jobName = jobName + " [" + Path.GetFileName( sceneFile ) + "]"
        
        #print jobName
        # Create job info file.
        #jobInfoFilename = Path.Combine( GetDeadlineTempPath(), "nuke_job_info.job" )

        #jobInfoFilename = "Q:/Temp/Ali/tits/" + "nuke_job_info.job"
        jobInfoFilename =  _job_info
        try:
            writer.close()
        except:
            pass

        with open(jobInfoFilename, 'w') as writer:
            writer.write( "Plugin=Nuke\n" )
            writer.write( "Name=%s\n" % jobName )
            writer.write( "Comment=%s\n" % comment )
            writer.write( "Department=%s\n" % "" )
            writer.write( "Pool=%s\n" % "dds" )
            writer.write( "SecondaryPool=%s\n" % "" )
            writer.write( "Group=%s\n" % "" )
            writer.write( "Priority=%s\n" % 50 )
            writer.write( "TaskTimeoutMinutes=%s\n" % 0 )
            writer.write( "EnableAutoTimeout=%s\n" % False )
            writer.write( "ConcurrentTasks=%s\n" % 1 )
            writer.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % True )
            writer.write( "OutputFilename0=%s\n" % _outputImage)
            #writer.write( "ForceReloadPlugin=%s" % scriptDialog.GetValue( "ForceReloadPluginBox" ) )
            writer.write( "ForceReloadPlugin=%s\n" % False )
            writer.write( "MachineLimit=%s\n" % 0 )
            writer.write( "Whitelist=%s\n" % '' )
            writer.write( "LimitGroups=%s\n" % '' )
            writer.write( "JobDependencies=%s\n" % '' )
            writer.write( "OnJobComplete=%s\n" % 'Nothing' )
            writer.write( "Frames=%s\n" % frames )
            writer.write( "ChunkSize=%s\n" % 9999 )
            writer.write( "PostJobScript=%s\n" % _post_job_script )
        


        #pluginInfoFilename = "Q:/Temp/Ali/tits/" + "nuke_plugin_info.job"
        pluginInfoFilename = _plugin_info
        try:
            writer.close()
        except:
            pass
        with open(pluginInfoFilename, 'w') as writer:
            writer.write( "SceneFile=%s\n" % sceneFile )
            writer.write( "Version=%s\n" % version )
            writer.write( "Threads=%s\n" % 0 )
            writer.write( "RamUse=%s\n" % 0 )
            writer.write( "NukeX=%s\n" % True )
            writer.write( "BatchMode=%s\n" % False )
            writer.write( "BatchModeIsMovie=%s\n" % True )
            writer.write( "ContinueOnError=%s\n" % False )
            writer.write( "RenderMode=%s\n" % "Use Scene Sttings" )
            writer.write( "EnforceRenderOrder=%s\n" % False )
            writer.write( "Views=%s\n" % '' )
            writer.write( "WriteNode=%s\n" % 'Write_Output' )
            writer.write( "StackSize=%s\n" % 0 )
            writer.write( "UseGpu=%s\n" % False )
            writer.write( "PerformanceProfiler=%s\n" % False )
            writer.write( "PerformanceProfilerDir=%s\n" % '' )


        

        #Submit to Deadline

#Submits the .nk and .job(s) to deadline
def SubmitJobToDeadline(job_info, plugin_info, plugin_file):

    dl_command  = 'L:/DeadlineRepository10/bin/Windows/64bit/deadlinecommand.exe'
    args = [ dl_command , job_info , plugin_info , plugin_file ]
    command = ' '.join(args)
    p = Popen(command,stdout=PIPE,stderr=PIPE,shell=True)
    '''
    stdout,stderr=p.communicate()

    if stderr:
        print "STDERR : ", stderr
    else:
        print "STDOUT : ", stdout
    '''

#grabs a regex pattern
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

#removes a regex pattern    
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

#returns a mov duration in frames using ffmpeg
def get_duration_frames(file, fps):
    ffprobe = '//qumulo/LiveApps/utils/ffmpeg/bin/ffprobe'
    command = '{} -i {} -show_entries format=duration -of compact=p=0:nk=1 -v 0'.format(ffprobe, file)
    p = Popen(command,stdout=PIPE,stderr=PIPE,shell=True)
    stdout,stderr=p.communicate()

    return float(stdout)*float(fps)



class LuxCIS(object):
    '''Custom action.'''

    label = 'Create CIS'
    identifier = 'create.cis'
    description = 'Creates a sequence CIS from selected items'
    icon = 'https://static.thenounproject.com/png/2160687-200.png'

    def __init__(self, session):
        '''Initialise action.'''
        super(LuxCIS, self).__init__()
        self.session = session
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )


        self.proj = None
        self.master_dict = None 

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
                'icon': self.icon
            }]
        }

    def get_items(self,items, session):

        m_dict = []

        index = 0
        items = [item for item in items if item['object_type']['name'] in ['Shot', 'Task']]

        #print 'get_items():',items,'\r\n'
        for item in items:
            '''
            print item['name'],task_type
            if item['name'] != task_type:
                continue
            '''
            #print item['object_type']['name']
            #print self.item_type
            item_type = item['object_type']['name']
            #print  '####'
            #print item['custom_attributes']['out_path']
            #if its a shot, get the frame duration and shot specific attributes
            if item_type == 'Shot':
                task = [i for i in item['descendants'] if (i['object_type']['name'] == 'Task') and (i['name'] == 'Compositing')][0]
                shot = item
                #print item['custom_attributes']['first_frame']
                #print item['custom_attributes']['last_frame']
                #print task['name']
                pass
            #if its a task, get the frame duration from its ancestor
            if item_type == 'Task':
                shot = [i for i in item['ancestors'] if i['object_type']['name'] == 'Shot'][0]
                task = item
                #print task['name']
                #shot_name = shot['name']
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
            #slate = shot['custom_attributes']['slate']
            lens = shot['custom_attributes']['lens_info']

            #tag related
            #find it by backtracking the TASK entity

            project_id = item['project_id']
            self.proj = session.query('select custom_attributes from Project where id is "{0}"'.format(project_id)).first()
            project_name = self.proj['name']#[i for i in item['ancestors'] if i['object_type']['name'] == 'Project'][0]['name']
            try:
                episode_name = [i for i in item['ancestors'] if i['object_type']['name'] == 'Episode'][0]['name']
            except:
                episode_name = ''
                pass
            #print [i for i in item['ancestors']]#get the project code

            project_code = self.proj['name']
            project_name = self.proj['full_name']

            item_info = {
                'index' : index,
                'project_name' : project_name,
                'project_code' : project_code,
                'episode_name' : episode_name,
                'item_title' : item_title,
                'shot_name' : shot_name,
                'task_name' : task_name,
                'duration' : duration,
                'first_frame' : first_frame,
                'last_frame' : last_frame,
                'base_path' : base_path,
                'out_path' : out_path,
                'status' : status,
                #'slate' : slate,
                'lens' : lens,
                'format' : '',
                'codec' : '',
                'tags' : [],
                'image_file': '',
                'metad_file': '',
                #'matte_file': '',
                'asset_name' : '',
                'slate_output': '',
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
                    matte_path = full_path

                    if task_name == 'Compositing':
                        jpg_path = os.path.join(full_path, 'JPEG')
                        dpx_path = os.path.join(full_path, 'DPX')
                        exr_path = os.path.join(full_path, 'EXR')
                        matte_path = os.path.join(full_path, 'matte')
                    found_image_folders = []
                    file_types = {}
                    image_file = ''
                    metad_file = ''
                    matte_file = ''
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

                        default_base_output = os.path.join(base_path, "09_QT/CIS")

                        item_info['default_base_output'] = default_base_output

                        slate_output = default_base_output

                        slate_output = slate_output.replace('\\','/').replace('//','/')
                        item_info['slate_output'] = slate_output
                        #print '###################', slate_output
                        item_info['success'] = True
                        break

            else:
                #print 'No outputs rendered: ',shot_name
                pass

            #print shot_info
            #add to master_dict[] if no other dicts with the same 'item_title' value doesnt exist
            add_to_dict = True
            for i in m_dict:
                if i.get('item_title') == item_info.get('item_title'):
                    add_to_dict = False
            if add_to_dict:
                #if item['name'] == task_type:
                m_dict.append(item_info)
                index += 1

            pass

        return m_dict

    def main_proc(self, eventdata, items, session):


        try:
            master_dict = self.get_items(items,session)
        except TypeError:
            retFail = {
                'success': False,
                'message': 'Try Again, CIS succesfully failed for no reason! @ master dict'
            }
            return retFail


        if (len(master_dict) != 0):
            self.master_dict = master_dict


        #print '\r\n\r\n\r##',self.master_dict,'\r\n\r\n\r'

        shot_items = []


        seq = session.query('select name, custom_attributes from Sequence where descendants any(name="{0}")'.format(self.master_dict[0]['shot_name'])).first()
        seq_name      = seq['name']
        seq_base_cis  = seq['custom_attributes']['base_cis']
        seq_base_edl  = seq['custom_attributes']['base_edl']
        seq_base_path = seq['custom_attributes']['base_path']
        seq_fps       = seq['custom_attributes']['fps']
        seq_edl_file  = seq['custom_attributes']['edl_file']
        seq_cis_file  = seq['custom_attributes']['cis_file']



        #Populate the templates dropdown
        template_files_dir = "L:/HAL/LUX_SLATE/nuke_templates"
        if os.path.isdir(template_files_dir):
            template_files = [i for i in os.listdir(template_files_dir) if (i[-3:] == '.nk') and ('_CIS_' in i)]

        template_items = []
        for i in template_files:
            new_entry =  {}
            new_entry['label'] = i
            new_entry['value'] = i
            template_items.append(new_entry)



        #Populate the CIS file dropdown
        seq_base_cis_dir = seq_base_cis
        cis_files = []
        if os.path.isdir(seq_base_cis_dir):
            cis_files = [i for i in os.listdir(seq_base_cis_dir) if (i.lower()[-4:] == '.mov') and (seq_name.upper() in i.upper())]
        if len(cis_files)<1:
            cis_files.append('No CIS files found! Render out a base CIS!')
        cis_items = []
        for i in cis_files:
            new_entry =  {}
            new_entry['label'] = i
            new_entry['value'] = i
            cis_items.append(new_entry)



        #Populate the EDL file dropdown
        seq_base_edl_dir = seq_base_edl
        edl_files = []
        if os.path.isdir(seq_base_edl_dir):
            edl_files = [i for i in os.listdir(seq_base_edl_dir) if (i.lower()[-4:] == '.edl') and (seq_name.upper() in i.upper())]
        if len(edl_files)<1:
            edl_files.append('No EDL files found! Export out an EDL!')
        edl_items = []
        for i in edl_files:
            new_entry =  {}
            new_entry['label'] = i
            new_entry['value'] = i
            edl_items.append(new_entry)


        for shot in self.master_dict:
            #print shot['task_name']
            #print event['data']['cis_task_types']
            #print '#'
            #project_name = shot['project_name']
            #shot_name = shot['shot_name']
            #image_file = shot['image_file']
            #metad_file = shot['metad_file']
            #output = shot['slate_output']
            #duration = shot['duration']
            #sequencename = seq_name
            success = shot['success']
            asset_name = shot['asset_name']
            index = shot['index']
            version_items = []
            frame_range = '{0}-{1}'.format( str(shot['first_frame']) , str(shot['last_frame']) )
            text = 'Could not locate rendered files.....\r'
            success_msg = 'FAILED'
            if shot['success']:
                success_msg = 'SUCCESSFUL'

                #text = '''Offline sequence : {0}\n\rOnline sequence  : {1}\n\rSlate Location   : {2}\n\r'''.format(shot['image_file'],shot['metad_file'],shot['slate_output'])
                text = '''Image sequence : {0}\n\r'''.format(shot['image_file'])
                text = '''{0}\n\r'''.format(shot['image_file'])
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
            'message': 'Creating a CIS from {0}/{1} items!'.format(totalSlatedItems,totalSelectedItems)
        }

        cis_txt_items = sorted(['{none}','{date}', '{time}', '{framecounter}', '{project}', '{projectname}', '{episode}', '{timecode}', '{episodename}', '{sequence}', '{sequencename}', '{imagename}', '{user}', '{shot}', '{shotname}', '{version}', '{task}', '{assetname}', '{description}','{slatename}', '{custom}', '{lens}', '{status}', '{codec}', '{format}', '{firstframe}', '{lastframe}', '{duration}','{logo}','{colorspacein}','{colorspaceout}', 'Lux Visual Effects'])
        cis_txt_positions = []
        for item in cis_txt_items:
            #cis_txt_dct = {'label':item, 'value':item.split('<')[-1].split('>')[0]}
            cis_txt_dct = {'label':item, 'value':item}
            cis_txt_positions.append(cis_txt_dct)

        cis_codecs_raw = ['', 'rle \tAnimation', 'apcn\tApple ProRes 422', 'apch\tApple ProRes 422 HQ', 'apcs\tApple ProRes 422 LT', 'apco\tApple ProRes 422 Proxy', 'ap4h\tApple ProRes 4444', 'ap4x\tApple ProRes 4444 XQ', 'AV1x\tAvid 1:1x', 'AVdn\tAvid DNxHD Codec', 'AVdh\tAvid DNxHR Codec', 'AVdv\tAvid DV Codec', 'AVd1\tAvid DV100 Codec', 'AVj2\tAvid JPEG 2000 Codec', 'AVDJ\tAvid Meridien Compressed', 'AVUI\tAvid Meridien Uncompressed', 'AVup\tAvid Packed Codec', 'AVrp\tAvid RGBPacked Codec', 'WRLE\tBMP', 'cvid\tCinepak', 'yuv2\tComponent Video', 'dvcp\tDV - PAL', 'dvc \tDV/DVCPRO - NTSC', 'dvpp\tDVCPRO - PAL', 'smc \tGraphics', 'h261\tH.261', 'h263\tH.263', 'avc1\tH.264', 'mjp2\tJPEG 2000', 'mp1v\tMPEG-1 Video', 'mp4v\tMPEG-4 Video', 'mjpa\tMotion JPEG A', 'mjpb\tMotion JPEG B', 'raw \tNone', 'png \tPNG', 'jpeg\tPhoto - JPEG', '8BPS\tPlanar RGB', 'SVQ1\tSorenson Video', 'SVQ3\tSorenson Video 3', 'tga \tTGA', 'tiff\tTIFF', 'v210\tUncompressed 10-bit 4:2:2', 'rpza\tVideo']
        cis_codecs = []
        for item in cis_codecs_raw:
            if '\t' not in item:
                item = '\t'+item
            cis_codec_dct = {'label':item.split('\t')[1], 'value':item.split('\t')[0]}
            cis_codecs.append(cis_codec_dct)


        cis_colorspaces_raw = ['', 'default\tdefault', 'linear\tlinear', 'sRGB\tsRGB', 'rec709\trec709', 'Cineon\tCineon', 'Gamma1.8\tGamma1.8', 'Gamma2.2\tGamma2.2', 'Gamma2.4\tGamma2.4', 'Gamma2.6\tGamma2.6', 'Panalog\tPanalog', 'REDLog\tREDLog', 'ViperLog\tViperLog', 'AlexaV3LogC\tAlexaV3LogC', 'PLogLin\tPLogLin', 'SLog\tSLog', 'SLog1\tSLog1', 'SLog2\tSLog2', 'SLog3\tSLog3', 'CLog\tCLog', 'Log3G10\tLog3G10', 'Log3G12\tLog3G12', 'HybridLogGamma\tHybridLogGamma', 'Protune\tProtune', 'BT1886\tBT1886', 'st2084\tst2084']
        cis_colorspaces = []
        for item in cis_colorspaces_raw:
            if '\t' not in item:
                item = '\t'+item
            cis_colorspace_dct = {'label':item.split('\t')[1], 'value':item.split('\t')[0]}
            cis_colorspaces.append(cis_colorspace_dct)

        list_of_resolutions = [
            ['PC_Video  640 x 480','640 480 0 0 640 480 1 PC_Video'],
            ['NTSC  720 x 486 0.91','720 486 0 0 720 486 0.91 NTSC'],
            ['PAL  720 x 576 1.09','720 576 0 0 720 576 1.09 PAL'],
            ['NTSC_16:9  720 x 486 1.21','720 486 0 0 720 486 1.21 NTSC_16:9'],
            ['PAL_16:9  720 x 576 1.46','720 576 0 0 720 576 1.46 PAL_16:9'],
            ['HD_720  1280 x 720','1280 720 0 0 1280 720 1 HD_720'],
            ['HD_1080  1920 x 1080','1920 1080 0 0 1920 1080 1 HD_1080'],
            ['UHD_4K  3840 x 2160','3840 2160 0 0 3840 2160 1 UHD_4K'],
            ['1K_Super_35(full-ap)  1024 x 778','1024 778 0 0 1024 778 1 1K_Super_35(full-ap)'],
            ['1K_Cinemascope  914 x 778 2.0','914 778 0 0 914 778 2 1K_Cinemascope'],
            ['2K_Super_35(full-ap)  2048 x 1556','2048 1556 0 0 2048 1556 1 2K_Super_35(full-ap)'],
            ['2K_Cinemascope  1828 x 1556 2.0','1828 1556 0 0 1828 1556 2 2K_Cinemascope'],
            ['2K_DCP  2048 x 1080','2048 1080 0 0 2048 1080 1 2K_DCP'],
            ['4K_Super_35(full-ap)  4096 x 3112','4096 3112 0 0 4096 3112 1 4K_Super_35(full-ap)'],
            ['4K_Cinemascope  3656 x 3112 2.0','3656 3112 0 0 3656 3112 2 4K_Cinemascope'],
            ['4K_DCP  4096 x 2160','4096 2160 0 0 4096 2160 1 4K_DCP'],
            ['square_256  256 x 256','256 256 0 0 256 256 1 square_256'],
            ['square_512  512 x 512','512 512 0 0 512 512 1 square_512'],
            ['square_1K  1024 x 1024','1024 1024 0 0 1024 1024 1 square_1K'],
            ['square_2K  2048 x 2048','2048 2048 0 0 2048 2048 1 square_2K'],
            ['square_128  128 x 128','128 128 0 0 128 128 1 square_128'],
            ['square_4K  4096 x 4096','4096 4096 0 0 4096 4096 1 square_4K'],
            ['square_8K  8192 x 8192','8192 8192 0 0 8192 8192 1 square_8K'],
            ['HALF_HD  960 x 540','960 540 0 0 960 540 1 HALF_HD'],
            ['FCP  720 x 480 0.89','720 480 0 0 720 480 0.9 FCP'],
            ['BBC  2048 x 1165','2048 1165 0 0 2048 1165 1 BBC'],
            ['BBC_HALF  1024 x 582','1024 582 0 0 1024 582 1 BBC_HALF'],
            ['DCI_2K  2048 x 1080','2048 1080 0 0 2048 1080 1 DCI_2K'],
            ['DCI_2K_16:9  2048 x 1152','2048 1152 0 0 2048 1152 1 DCI_2K 16:9'],
            ['ANA_2K 2.66:1 2288 x 858','2288 858 0 0 2288 858 1 ANA_2K'],
            ['QHD+ 16:9 3200 x 1800','3200 1800 0 0 3200 1800 1 QHD+ 16:9'],
            ['4K_ANA 4096 x 3416', '4096 3416 0 0 4096 3416 2 4K_ANA'],
            ['4K_ANA_S 4096 x 3416', '4096 3416 0 0 4096 3416 1 4K_ANA_S'],
            ['3K 2880 x 1620', '2880 1620 0 0 2880 1620 1 3K']
        ]
        
        default_data_type = ['default\tdefault']
        mov_settings = ['----------\t----------', "{'file_type': 'mov', 'mov64_dnxhd_codec_profile': 'DNxHD 444 10-bit 440Mbit'}\tmov - DNxHD 444 10-bit 440Mbit", "{'file_type': 'mov', 'mov64_dnxhd_codec_profile': 'DNxHD 422 10-bit 220Mbit'}\tmov - DNxHD 422 10-bit 220Mbit", "{'file_type': 'mov', 'mov64_dnxhd_codec_profile': 'DNxHD 422 8-bit 220Mbit'}\tmov - DNxHD 422 8-bit 220Mbit", "{'file_type': 'mov', 'mov64_dnxhd_codec_profile': 'DNxHD 422 8-bit 145Mbit'}\tmov - DNxHD 422 8-bit 145Mbit", "{'file_type': 'mov', 'mov64_dnxhd_codec_profile': 'DNxHD 422 8-bit 36Mbit'}\tmov - DNxHD 422 8-bit 36Mbit"]
        exr_settings = ['----------\t----------', "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'none'}\texr - 16 bit half - none", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'Zip (1 scanline)'}\texr - 16 bit half - Zip (1 scanline)", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'Zip (16 scanlines)'}\texr - 16 bit half - Zip (16 scanlines)", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'PIZ Wavelet (32 scanlines)'}\texr - 16 bit half - PIZ Wavelet (32 scanlines)", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'RLE'}\texr - 16 bit half - RLE", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'B44'}\texr - 16 bit half - B44", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'B44A'}\texr - 16 bit half - B44A", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'DWAA'}\texr - 16 bit half - DWAA", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'DWAB'}\texr - 16 bit half - DWAB", '----------\t----------', "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'none'}\texr - 32 bit float - none", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'Zip (1 scanline)'}\texr - 32 bit float - Zip (1 scanline)", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'Zip (16 scanlines)'}\texr - 32 bit float - Zip (16 scanlines)", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'PIZ Wavelet (32 scanlines)'}\texr - 32 bit float - PIZ Wavelet (32 scanlines)", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'RLE'}\texr - 32 bit float - RLE", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'B44'}\texr - 32 bit float - B44", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'B44A'}\texr - 32 bit float - B44A", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'DWAA'}\texr - 32 bit float - DWAA", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'DWAB'}\texr - 32 bit float - DWAB"]
        dpx_settings = ['----------\t----------', "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'user-defined'}\tdpx - 8 bit - user-defined", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'printing density'}\tdpx - 8 bit - printing density", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'linear'}\tdpx - 8 bit - linear", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'log'}\tdpx - 8 bit - log", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'unspecified video'}\tdpx - 8 bit - unspecified video", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'SMPTE 240M'}\tdpx - 8 bit - SMPTE 240M", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'CCIR 709-1'}\tdpx - 8 bit - CCIR 709-1", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'CCIR 601-2 system B/G'}\tdpx - 8 bit - CCIR 601-2 system B/G", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'CCIR 601-2 system M'}\tdpx - 8 bit - CCIR 601-2 system M", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'NTSC'}\tdpx - 8 bit - NTSC", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'PAL'}\tdpx - 8 bit - PAL", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'Z linear'}\tdpx - 8 bit - Z linear", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'Z homogeneous'}\tdpx - 8 bit - Z homogeneous", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': '(auto detect)'}\tdpx - 8 bit - (auto detect)", '----------\t----------', "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'user-defined'}\tdpx - 10 bit - user-defined", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'printing density'}\tdpx - 10 bit - printing density", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'linear'}\tdpx - 10 bit - linear", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'log'}\tdpx - 10 bit - log", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'unspecified video'}\tdpx - 10 bit - unspecified video", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'SMPTE 240M'}\tdpx - 10 bit - SMPTE 240M", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'CCIR 709-1'}\tdpx - 10 bit - CCIR 709-1", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'CCIR 601-2 system B/G'}\tdpx - 10 bit - CCIR 601-2 system B/G", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'CCIR 601-2 system M'}\tdpx - 10 bit - CCIR 601-2 system M", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'NTSC'}\tdpx - 10 bit - NTSC", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'PAL'}\tdpx - 10 bit - PAL", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'Z linear'}\tdpx - 10 bit - Z linear", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'Z homogeneous'}\tdpx - 10 bit - Z homogeneous", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': '(auto detect)'}\tdpx - 10 bit - (auto detect)", '----------\t----------', "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'user-defined'}\tdpx - 12 bit - user-defined", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'printing density'}\tdpx - 12 bit - printing density", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'linear'}\tdpx - 12 bit - linear", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'log'}\tdpx - 12 bit - log", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'unspecified video'}\tdpx - 12 bit - unspecified video", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'SMPTE 240M'}\tdpx - 12 bit - SMPTE 240M", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'CCIR 709-1'}\tdpx - 12 bit - CCIR 709-1", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'CCIR 601-2 system B/G'}\tdpx - 12 bit - CCIR 601-2 system B/G", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'CCIR 601-2 system M'}\tdpx - 12 bit - CCIR 601-2 system M", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'NTSC'}\tdpx - 12 bit - NTSC", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'PAL'}\tdpx - 12 bit - PAL", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'Z linear'}\tdpx - 12 bit - Z linear", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'Z homogeneous'}\tdpx - 12 bit - Z homogeneous", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': '(auto detect)'}\tdpx - 12 bit - (auto detect)", '----------\t----------', "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'user-defined'}\tdpx - 16 bit - user-defined", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'printing density'}\tdpx - 16 bit - printing density", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'linear'}\tdpx - 16 bit - linear", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'log'}\tdpx - 16 bit - log", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'unspecified video'}\tdpx - 16 bit - unspecified video", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'SMPTE 240M'}\tdpx - 16 bit - SMPTE 240M", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'CCIR 709-1'}\tdpx - 16 bit - CCIR 709-1", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'CCIR 601-2 system B/G'}\tdpx - 16 bit - CCIR 601-2 system B/G", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'CCIR 601-2 system M'}\tdpx - 16 bit - CCIR 601-2 system M", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'NTSC'}\tdpx - 16 bit - NTSC", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'PAL'}\tdpx - 16 bit - PAL", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'Z linear'}\tdpx - 16 bit - Z linear", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'Z homogeneous'}\tdpx - 16 bit - Z homogeneous", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': '(auto detect)'}\tdpx - 16 bit - (auto detect)"]
        jpg_settings = ['----------\t----------', "{'file_type': 'jpeg', '_jpeg_sub_sampling': '4:1:1'}\tjpeg - 4:1:1", "{'file_type': 'jpeg', '_jpeg_sub_sampling': '4:2:2'}\tjpeg - 4:2:2", "{'file_type': 'jpeg', '_jpeg_sub_sampling': '4:4:4'}\tjpeg - 4:4:4"]
        png_settings = ['----------\t----------', "{'file_type': 'png', 'datatype': '8 bit'}\tpng - 8 bit", "{'file_type': 'png', 'datatype': '16 bit'}\tpng - 16 bit"]
        tga_settings = ['----------\t----------', "{'file_type': 'targa', 'compression': 'none'}\ttarga - none", "{'file_type': 'targa', 'compression': 'RLE'}\ttarga - RLE"]
        tif_settings = ['----------\t----------', "{'file_type': 'tiff', 'datatype': '8 bit', 'compression': 'none'}\ttiff - 8 bit - none", "{'file_type': 'tiff', 'datatype': '8 bit', 'compression': 'PackBits'}\ttiff - 8 bit - PackBits", "{'file_type': 'tiff', 'datatype': '8 bit', 'compression': 'LZW'}\ttiff - 8 bit - LZW", "{'file_type': 'tiff', 'datatype': '8 bit', 'compression': 'Deflate'}\ttiff - 8 bit - Deflate", '----------\t----------', "{'file_type': 'tiff', 'datatype': '16 bit', 'compression': 'none'}\ttiff - 16 bit - none", "{'file_type': 'tiff', 'datatype': '16 bit', 'compression': 'PackBits'}\ttiff - 16 bit - PackBits", "{'file_type': 'tiff', 'datatype': '16 bit', 'compression': 'LZW'}\ttiff - 16 bit - LZW", "{'file_type': 'tiff', 'datatype': '16 bit', 'compression': 'Deflate'}\ttiff - 16 bit - Deflate", '----------\t----------', "{'file_type': 'tiff', 'datatype': '32 bit float', 'compression': 'none'}\ttiff - 32 bit float - none", "{'file_type': 'tiff', 'datatype': '32 bit float', 'compression': 'PackBits'}\ttiff - 32 bit float - PackBits", "{'file_type': 'tiff', 'datatype': '32 bit float', 'compression': 'LZW'}\ttiff - 32 bit float - LZW", "{'file_type': 'tiff', 'datatype': '32 bit float', 'compression': 'Deflate'}\ttiff - 32 bit float - Deflate"]
        all_data_types = default_data_type + mov_settings + exr_settings + dpx_settings + jpg_settings + png_settings + tga_settings + tif_settings
        
        data_type_settings = []
        for item in all_data_types:
            data_type_dct = {'label':item.split('\t')[1], 'value':item.split('\t')[0]}
            data_type_settings.append(data_type_dct)

        cis_formats = []
        for item in list_of_resolutions:
            cis_res_dct = {'label':item[0], 'value':item[1]}
            cis_formats.append(cis_res_dct)


        cis_overlays_dict = eval(self.proj['custom_attributes']['cis_overlays_dict'])

        cis_settings = [{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': 'My String',
                    'type': 'hidden',
                    'value': 'B',
                    'name': 'form_type'
                },{
                    'value': '<i><b>CIS SETTINGS</b></i>',
                    'type': 'label'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': '<font color="green"> + <i>Base CIS</i></font>',
                    'type': 'enumerator',
                    'value': seq['custom_attributes']['cis_file'],
                    'data' : cis_items,
                    'name': 'cis_file'
                },{
                    'label': '<font color="green"> + <i>Base EDL</i></font>',
                    'type': 'enumerator',
                    'value': seq['custom_attributes']['edl_file'],
                    'data' : edl_items,
                    'name': 'edl_file'
                },{
                    'label': ' + <i>CIS Codec</i>',
                    'type': 'enumerator',
                    'value': self.proj['custom_attributes']['cis_codec'],
                    'data' : cis_codecs,
                    'name': 'cis_codec'
                },{
                    'label': ' + <i>CIS Format</i>',
                    'type': 'enumerator',
                    'value': self.proj['custom_attributes']['cis_format'],
                    'data' : cis_formats,
                    'name': 'cis_format'
                },{
                    'label': ' + <i>CIS Output</i>',
                    'type': 'text',
                    'value': self.proj['custom_attributes']['cis_output'],
                    'name': 'cis_output'
                },{
                    'label': ' + <i>CIS Slate</i>',
                    'type': 'enumerator',
                    'name': 'cis_template_file',
                    'data': template_items,
                    'value': self.proj['custom_attributes']['cis_template']
                },{
                    'label': '<font color="yellow"> + <i>Colorspace In</i><font>',
                    'type': 'enumerator',
                    'name': 'cis_colorspace_in',
                    'data': cis_colorspaces,
                    'value': self.proj['custom_attributes']['cis_colorspace_in']
                },{
                    'label': '<font color="yellow"> + <i>Colorspace Out</i><font>',
                    'type': 'enumerator',
                    'name': 'cis_colorspace_out',
                    'data': cis_colorspaces,
                    'value': self.proj['custom_attributes']['cis_colorspace_out']
                },{
                    'label': '<font color="orange"> + <i>Data Type</i><font>',
                    'type': 'enumerator',
                    'name': 'cis_data_type',
                    'data': data_type_settings,
                    'value': self.proj['custom_attributes']['cis_data_type']
                },{
                    'label': '<font color="pink"> + <i>Slate Frame</i></font>',
                    'type': 'boolean',
                    'value': self.proj['custom_attributes']['cis_slate_frame'],
                    'name': 'cis_slate_frame'
                },{
                    'label': '<font color="pink"> + <i>Overlays</i></font>',
                    'type': 'boolean',
                    'value': self.proj['custom_attributes']['cis_overlays'],
                    'name': 'cis_overlays'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },


                {
                    'label': '<b><font color="red">Save CIS settings</font></b>',
                    'type': 'boolean',
                    'value': False,
                    'name': 'make_cis_settings_default'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'value': '<i><b>OVERLAYS & LABELS</b></i>',
                    'type': 'label'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },

                {
                    'label': 'Date',
                    'type': 'date',
                    'name': 'date',
                    'value': datetime.date.today().isoformat()
                },{
                    'label': 'Description Text',
                    'type': 'text',
                    'value': cis_overlays_dict.get('cis_description_text'),
                    'name': 'description_text'
                },{
                    'label': 'Custom Text',
                    'type': 'text',
                    'value': cis_overlays_dict.get('cis_custom_text'),
                    'name': 'custom_text'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': '<font color="pink">Project Title</font>',
                    'type': 'enumerator',
                    'value': cis_overlays_dict.get('cis_frame_project_title'),
                    'data' : cis_txt_positions,
                    'name': 'cis_frame_project_title'
                },{
                    'label': '<font color="pink">Slate Info</font>',
                    'type': 'enumerator',
                    'value': cis_overlays_dict.get('cis_frame_description'),
                    'data' : cis_txt_positions,
                    'name': 'cis_frame_description'
                },{
                    'label': '<font color="pink">Shot Title</font>',
                    'type': 'enumerator',
                    'value': cis_overlays_dict.get('cis_frame_shot_title'),
                    'data' : cis_txt_positions,
                    'name': 'cis_frame_shot_title'
                },{
                    'label': '<font color="pink">Frame Range Info</font>',
                    'type': 'enumerator',
                    'value': cis_overlays_dict.get('cis_frame_range_info'),
                    'data' : cis_txt_positions,
                    'name': 'cis_frame_range_info'
                },{
                    'label': '<font color="pink">Timecode Info</font>',
                    'type': 'enumerator',
                    'value': cis_overlays_dict.get('cis_frame_timecode_info'),
                    'data' : cis_txt_positions,
                    'name': 'cis_frame_timecode_info'
                },{
                    'label': '<font color="pink">Version Info</font>',
                    'type': 'enumerator',
                    'value': cis_overlays_dict.get('cis_frame_version_info'),
                    'data' : cis_txt_positions,
                    'name': 'cis_frame_version_info'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': '<font color="pink">Top Left</font>',
                    'type': 'enumerator',
                    'value': cis_overlays_dict.get('cis_top_left'),
                    'data' : cis_txt_positions,
                    'name': 'cis_top_left'
                },{
                    'label': '<font color="pink">Top Right</font>',
                    'type': 'enumerator',
                    'value': cis_overlays_dict.get('cis_top_right'),
                    'data' : cis_txt_positions,
                    'name': 'cis_top_right'
                },{
                    'label': '<font color="pink">Bottom Left</font>',
                    'type': 'enumerator',
                    'value': cis_overlays_dict.get('cis_bottom_left'),
                    'data' : cis_txt_positions,
                    'name': 'cis_bottom_left'
                },{
                    'label': '<font color="pink">Bottom Right</font>',
                    'type': 'enumerator',
                    'value': cis_overlays_dict.get('cis_bottom_right'),
                    'data' : cis_txt_positions,
                    'name': 'cis_bottom_right'
                },{
                    'label': '<font color="pink">Top Center</font>',
                    'type': 'enumerator',
                    'value': cis_overlays_dict.get('cis_top_center'),
                    'data' : cis_txt_positions,
                    'name': 'cis_top_center'
                },{
                    'label': '<font color="pink">Bottom Center</font>',
                    'type': 'enumerator',
                    'value': cis_overlays_dict.get('cis_bottom_center'),
                    'data' : cis_txt_positions,
                    'name': 'cis_bottom_center'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': '<b><font color="red">Save Overlays & Labels</font></b>',
                    'type': 'boolean',
                    'value': False,
                    'name': 'make_labels_default'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'value': '<i><b>SUBMISSION RESULTS</b></i>',
                    'type': 'label'
                },{
                    'value': '<hr>',
                    'type': 'label'
                }]

                
        #Add the slate text options
        for item in cis_settings[::-1]:
            shot_items.insert(0, item)

        retUI = {'items': shot_items}


        if ('values' in eventdata) and (eventdata['values']['form_type']=='B'):#data:

            values = eventdata['values']
            commit = False


            #append some other values
            values['sequencename'] = seq_name

            self.logger.info(u'Got values: {0}'.format(values))

            cis_template = values['cis_template_file']

            make_cis_settings_default = values['make_cis_settings_default']

            #Unfortunate workaround to save the settings...
            pid = self.proj['id']
            sid = seq['id']
            session2 = ftrack_api.Session()
            self.proj = session2.query('select custom_attributes from Project where id is "{0}"'.format(pid)).first()
            seq = session2.query('select custom_attributes from Sequence where id is "{0}"'.format(sid)).first()

            if make_cis_settings_default:
                #cis settings
                #self.proj['custom_attributes']['slate_offline'] = values['slate_offline']
                self.proj['custom_attributes']['cis_codec'] = values['cis_codec']
                self.proj['custom_attributes']['cis_format'] = values['cis_format']
                self.proj['custom_attributes']['cis_output'] = values['cis_output']
                self.proj['custom_attributes']['cis_template'] = cis_template
                self.proj['custom_attributes']['cis_colorspace_in'] = values['cis_colorspace_in']
                self.proj['custom_attributes']['cis_colorspace_out'] = values['cis_colorspace_out']
                self.proj['custom_attributes']['cis_data_type'] = values['cis_data_type']
                self.proj['custom_attributes']['cis_overlays'] = values['cis_overlays']
                self.proj['custom_attributes']['cis_slate_frame'] = values['cis_slate_frame']
                seq['custom_attributes']['cis_file'] = values['cis_file']
                seq['custom_attributes']['edl_file'] = values['edl_file']

                commit = True


            make_labels_default = values['make_labels_default']

            if make_labels_default:

                overlays_dict = {}

                overlays_dict['cis_description_text'] = values['description_text']
                overlays_dict['cis_custom_text'] = values['custom_text']

                overlays_dict['cis_top_left'] = values['cis_top_left']
                overlays_dict['cis_top_right'] = values['cis_top_right']
                overlays_dict['cis_top_center'] = values['cis_top_center']
                overlays_dict['cis_bottom_left'] = values['cis_bottom_left']
                overlays_dict['cis_bottom_right'] = values['cis_bottom_right']
                overlays_dict['cis_bottom_center'] = values['cis_bottom_center']

                overlays_dict['cis_frame_project_title'] = values['cis_frame_project_title']
                overlays_dict['cis_frame_description'] = values['cis_frame_description']
                overlays_dict['cis_frame_shot_title'] = values['cis_frame_shot_title']
                overlays_dict['cis_frame_range_info'] = values['cis_frame_range_info']
                overlays_dict['cis_frame_timecode_info'] = values['cis_frame_timecode_info']
                overlays_dict['cis_frame_version_info'] = values['cis_frame_version_info']

                self.proj['custom_attributes']['cis_overlays_dict'] = overlays_dict


                commit = True

            
            if commit:
                session2.commit()

            totalSlatedItems = 0

            #create a new dict from teh asset infos from the UI
            #grab the index from the name of each parameter
            #and add it to the items with matching indexes

            shot_related_params = []
            for value in values:
                if ('_' in value) :
                    if (value.split('_')[-1]).isdigit():
                        shot_related_params.append(value)

            cis_nuke_dict = {}



            for item in self.master_dict:


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

                    totalSlatedItems += 1

                    item['image_file'] = item['image_file'].replace(item['asset_name'],item['version'])
                    item['metad_file'] = item['metad_file'].replace(item['asset_name'],item['version'])
                    item['asset_name'] = item['version']

                    firstframe = item['first_frame']
                    lastframe = item['last_frame']

                    temp_dir = "L:\\tmp\\deadline_submission_scripts\\cis"

                    if not os.path.isdir(temp_dir):
                        os.makedirs(temp_dir)
                    
                    asset_name = item['asset_name']

                    item['asset_name'] = asset_name

                    cis_nuke_dict[str(item['shot_name'])] = item

                    pass


            retSuccess = {
                'success': True,
                'message': 'Creating a CIS from {0}/{1} items!'.format(totalSlatedItems,len(self.master_dict))
            }

            if not totalSlatedItems:
                retSuccess['success'] = False

            else:

                item = self.master_dict[0]

                item['asset_name'] = seq_name
                item['base_cis']   = seq_base_cis
                item['base_edl']   = seq_base_edl

                item['base_path']  = seq_base_path
                item['fps']        = seq_fps

                item['edl_file']   = values['edl_file']
                item['cis_file']   = values['cis_file']


                default_base_output = '{base_cis}{asset_name}/'.format(base_cis=item['base_cis'], asset_name=item['asset_name'])

                template = cis_template
                slate_descriptor = template.split('.')[0]
                slate_descriptor = slate_descriptor.replace('Generic_Slate_','')
                slate_descriptor = slate_descriptor.replace('Manual_Slate_','')
                slate_descriptor = slate_descriptor.replace('CIS_Slate_','')
                template_path = os.path.join(template_files_dir, template).replace('\\', '/')

                item['codec'] = values['cis_codec']
                item['slate_type'] = 'offline'
                item['format'] = values['cis_format']
                item['slate_frame'] = values['cis_slate_frame']
                item['overlays'] = values['cis_overlays']
                item['colorspace_in'] = values['cis_colorspace_in']
                item['colorspace_out'] = values['cis_colorspace_out']
                item['data_type'] = values['cis_data_type']

                now = datetime.datetime.now()
                date_suffix = now.strftime("%Y-%m-%d-%H%M")
                
                cis_overlays ={
                    'cis_top_left' : translate(values['cis_top_left'], values, item),
                    'cis_top_right' : translate(values['cis_top_right'], values, item),
                    'cis_top_center' : translate(values['cis_top_center'], values, item),
                    'cis_bottom_left' : translate(values['cis_bottom_left'], values, item),
                    'cis_bottom_right' : translate(values['cis_bottom_right'], values, item),
                    'cis_bottom_center' : translate(values['cis_bottom_center'], values, item),
                    'cis_frame_project_title' : translate(values['cis_frame_project_title'], values, item),
                    'cis_frame_description' : translate(values['cis_frame_description'], values, item),
                    'cis_frame_shot_title' : translate(values['cis_frame_shot_title'], values, item),
                    'cis_frame_range_info' : translate(values['cis_frame_range_info'], values, item),
                    'cis_frame_timecode_info' : translate(values['cis_frame_timecode_info'], values, item),
                    'cis_frame_version_info' : translate(values['cis_frame_version_info'], values, item)
                                }
                item['cis_overlays'] = cis_overlays
                
                cisfile   = os.path.join(temp_dir,item['asset_name']+'_cis_'+date_suffix+'.nk').replace('\\', '/')
                job_info    = os.path.join(temp_dir,item['asset_name']+'_cis_nuke_job_info_'+date_suffix+'.job').replace('\\', '/')
                plugin_info = os.path.join(temp_dir,item['asset_name']+'_cis_nuke_plugin_info_'+date_suffix+'.job').replace('\\', '/')

                item['cis_output'] = values['cis_output']
                item['cis_output'] = translate(item['cis_output'], values, item)

                cis_nuke_dict['GLOBAL'] = item

                user = getpass.getuser()                

                mov = item['base_cis'] + item['cis_file']

                print mov
                print item['fps']

                try:
                    last_frame = get_duration_frames(mov, item['fps'] )
                except ValueError:
                    retFail = {
                        'success': False,
                        'message': 'Try Again, CIS succesfully failed for no reason! @ last frame'
                    }
                    return retFail

                last_frame = int(last_frame)

                first_frame = 1
                if values['cis_slate_frame']:
                    first_frame = 0

                sframes = '{}-{}'.format(str(first_frame),str(last_frame))

                for i in values:
                    print i, values[i]


                meta_script = item['cis_output'].split('/')
                meta_script.insert(-1, 'scripts')
                meta_script = '/'.join(meta_script).split('.')[0]+'__meta_chapters__.txt'

                post_job_file = '//qumulo/LiveApps/apps/Scripts/FTRACK/ftrack_hooks/cis_hook/hook/'
                post_job_file = post_job_file + sorted([f for f in os.listdir(post_job_file) if ('cis_post_job' in f) and (f.split('.')[-1] == 'py')], reverse=True)[0]
                post_job_script = '{py}'.format(py=post_job_file, mov=item['cis_output'], meta=meta_script)


                CreateNukeSlateFile( cisfile, template_path, cis_nuke_dict )
                CreateNukeJob( cisfile, sframes, item['asset_name']+' '+item['task_name'], item['cis_output'], user, job_info, plugin_info, post_job_script)
                SubmitJobToDeadline( job_info, plugin_info, cisfile )

            return retSuccess

        return retUI


    def launch(self, event):

        items=[]

        data = event['data']

        selection = data.get('selection', [])

        session = ftrack_api.Session()

        #gather shot items from selection
        for entity in selection:
            item = session.query('select id from TypedContext where id is {0}'.format(entity['entityId'])).first()
            items.append(item)

        if (len(items) == 1) and (items[0]['object_type']['name'] == 'Sequence') :

            get_task_types = session.query('select name from Task where ancestors any(id="{0}")'.format(entity['entityId'])).all()

            task_types = []

            for t in sorted(get_task_types):

                temp_t = {'label':t['name'], 'value':t['name']}

                if temp_t not in task_types:

                    task_types.append(temp_t)

            task_types = sorted(task_types, key = lambda i: i['label']) 
            ret_success = [{'success':True}]

            ret_cis_sequence_settings = [{
                'value': '<hr>',
                'type': 'label'
            },{
                'label': 'My String',
                'type': 'hidden',
                'value': 'A',
                'name': 'form_type'
            },{
                'value': '<i><b>What type of tasks should I create the CIS from?</b></i>',
                'type': 'label'
            },{
                'label': 'Task Type',
                'type': 'enumerator',
                'value': task_types[0]['label'],
                'name': 'cis_task_types',
                'data': task_types
            },{
                'value': '<hr>',
                'type': 'label'
            }]
            
            
            if 'values' in event['data']:
                values = event['data']['values']

                if values['form_type'] == 'A':

                    task_type = values['cis_task_types']
                    items = session.query('select id from Task where name is "{1}" and ancestors any(id="{0}")'.format( entity['entityId'], task_type )).all()

                    return self.main_proc(event['data'], items, session) 

                if values['form_type'] == 'B':

                    return self.main_proc(event['data'], items, session)


            return {'items': ret_cis_sequence_settings}

        #if more than just 1 item is selected or 
        #If the single selected item is not a sequence, get all the tasks under the sequence
        else:

            if 'values' in event['data']:
                values = event['data']['values']

                if values['form_type'] == 'B':

                    return self.main_proc(event['data'], items, session)

            return self.main_proc(event['data'], items, session)

def register(session, **kw):
    '''Register plugin.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    action = LuxCIS(session)
    action.register()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()