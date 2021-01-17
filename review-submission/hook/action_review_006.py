'''Review submission action for Ftrack
Alican Sesli - Lux VFX - 23.01.2020 - 23.01.2020
    v1 - based on action_slate_028
    v2 - wip
    v4 - works
    v5 - nuke submission post-task-script to start the py script
    v6 - review submission now submits the py script as a post-job-script
'''

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


sys.path.append("X:/apps/Scripts/FTRACK/ftrack_hooks/slate_assets_hook/hook")
sys.path.append("X:/apps/Scripts/FTRACK/python-lib")

from lux_utils.get_latest_from import get_latest_from

import fileinput


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

#Translates the text fields to a format nuke can understand
def translate(_text, _values, _item):

    #shot/asset specific items
    #item = _item
    #master return dialog 
    #values = _values
    #'<None>','<Date>','<ShotCode>','<FrameRange>','<Description>','<Custom>', '<AssetName>'

    #_values = proj['custom_attributes']

    sequence_num = _item['shot_name'].split('_')[1]
    shot_num = _item['shot_name'].split('_')[-1]
    episode_num = removePattern(_item['episode_name'], r'\D*')
    episode_num = episode_num.replace('_','').replace(' ','')
    version_num = _item['version'].lower().split('_v')[-1]
    tag_replace = _text#.lower()
    tag_replace = tag_replace.replace('<', '{')
    tag_replace = tag_replace.replace('>', '}')

    format_name = _item['format']
    format_name = format_name.split(' ')[7::]
    format_name = ' '.join(format_name)

    tag_replace = tag_replace.format(
        none='',
        project=_item['project_code'],
        firstframe=str(_item['first_frame']),
        lastframe=str(_item['last_frame']),
        framecounter='[frame] ( ' + str(_item['first_frame'])+' - '+str(_item['last_frame']) + ' )',
        framerange=str(_item['first_frame'])+' - '+str(_item['last_frame']),
        projectname=_item['project_name'],
        duration=str(_item['duration']),
        episode=episode_num,
        episodename=_item['episode_name'],
        sequence=sequence_num,
        shot=shot_num,
        version=version_num,
        task=_item['task_name'],
        slatename=_item['slate_name'],
        format=format_name,
        defaultoutput=_item['default_base_output'],
        #description=_values['description_text'],
        #custom=_values['custom_text'],
        #date=_values['date'],
        description=_values['custom_attributes']['slate_description_text'],
        custom=_values['custom_attributes']['slate_custom_text'],
        date=datetime.date.today().isoformat(),

        shotname=_item['shot_name'],
        assetname=_item['asset_name'],
        codec=_item['codec'],
        colorspacein=_item['colorspace_in'],
        colorspaceout=_item['colorspace_out'],
        logo='logo',
        status=_item['status'],
        lens=_item['lens'],
        slatetype=_item['slate_type'],
        timecode="[python {nuke.toNode('SlatedTimeCode')['startcode'].value()}]")
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
def CreateNukeJob( _file, _frames, _asset, _outputImage, _user, _job_info, _plugin_info, _date, _extra_info):

    global scriptDialog

    version = 10.0
    
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
        jobName = _asset + " Slate Submission"
        comments = ['SLATE:', _frames, _user]
        comment = ' '.join(comments)
        if len(sceneFiles) > 1:
            jobName = jobName + " [" + Path.GetFileName( sceneFile ) + "]"
        
        jobInfoFilename =  _job_info

        title = _asset + ' '
        date = _date

        try:
            writer.close()
        except:
            pass



        post_task_script = 'L:/HAL/Alican/ftrack/_hooks/review_submission_hook/nuke_post_task_001.py'
        post_job_script = "L:/HAL/Alican/ftrack/_hooks/review_submission_hook/review_submitter_012.py"


        #[item['shot_name'] , item['task_name'] , item['slate_output'] , user, item['asset_name']+' Review', date]

        shot_code = _extra_info[0]
        task_type = _extra_info[1]
        mov_file = _extra_info[2]
        user = _extra_info[3]
        review = _extra_info[4]

        review = 'Review {}'.format(date)
        review = review.replace(' ', '-')

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
            writer.write( "PostTaskScript=%s\n" % post_task_script )
            writer.write( "Frames=%s\n" % frames )

            writer.write( "ExtraInfo0=%s\n" % shot_code )
            writer.write( "ExtraInfo1=%s\n" % task_type )
            writer.write( "ExtraInfo2=%s\n" % mov_file )
            writer.write( "ExtraInfo3=%s\n" % user )
            writer.write( "ExtraInfo4=%s\n" % review )

            writer.write( "PostJobScript=%s\n" % post_job_script )
            #postscript = {'pyscript':pyscript, 'shot_code':item['shot_name'], 'task_type':item['task_name'], 'mov_file':item['slate_output'], 'user':user }
            #writer.write( "PostJobScript=%s\n" % '{0} {1} {2} {3} {4}'.format( _postscript['pyscript'] , _postscript['shot_code'], _postscript['task_type'], _postscript['mov_file'], _postscript['user']) )

            #writer.write( "BatchName=%s %s\n" %  (title, date)  )

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
            writer.write( "NukeX=%s\n" % False )
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

#submits a .py script to deadline so the copying and renaming of files can be done as a job

#postscript = {'pyscript':pyscript, 'shot_code':item['shot_name'], 'task_type':item['task_name'], 'mov_file':item['slate_output'], 'user':user }

#def submitRenamerToDeadline(source_path, export_path, new_name, original_name):

def submitFtrackReviewToDeadline(pyscript, shot_code, task_type, mov_file, user, _asset, _date):

    def EncodeAsUTF16String( unicodeString ):
        return unicodeString.decode( "utf-8" ).encode( "utf-16-le" )

    def create_job_plugin_info(shot_code, task_type, mov_file, user):
        #Creates job_info and plugin_info files for submitting to deadline

        # Create job info file.
        deadline_submission_scripts = "L:\\tmp\\deadline_submission_scripts\\review\\ftrack"

        if not os.path.isdir(deadline_submission_scripts):
            os.makedirs(deadline_submission_scripts)

        job_info = '{0}\\job_info_{1}.job'.format(deadline_submission_scripts,shot_code)
        job_info = unicode(job_info, "utf-8")


        title = _asset + ' '
        date = _date

        review = 'Review {}'.format(date)
        review = review.replace(' ', '-')

        with open(job_info, 'w') as fileHandle: 
            fileHandle.write( "Plugin=%s\n" % 'Python' )
            fileHandle.write( "Name=%s for Client\n" % shot_code )
            #fileHandle.write( "UserName=%s\n" % '' )
            fileHandle.write( "Comment =%s\n" % 'Ftrack Review Submission' )
            fileHandle.write( "Frames=%s\n" % '1' )
            fileHandle.write( "Pool=%s\n" % 'dds' )
            fileHandle.write( "Priority=%s\n" % '99' )
            #fileHandle.write( "OutputFilename0=%s\\\n" % arg_dest_path )
            fileHandle.write( "BatchName=%s %s\n" %  (title, date)  )
            fileHandle.write( "InitialStatus=%s\n" % 'Suspended' )

        # Create the plugin info file
        plugin_info = '{0}\\plugin_info_{1}.job'.format(deadline_submission_scripts,shot_code)

        with open(plugin_info, 'w') as fileHandle: 
            fileHandle.write( "Arguments=%s %s %s %s %s\n" % (shot_code, task_type, mov_file, user, review) )
            fileHandle.write( "Version=%s\n" % '2.7' )
            fileHandle.write( "SingleFramesOnly=%s\n" % 'False' )

        return job_info, plugin_info

    dl_command  = r'L:\DeadlineRepository10\bin\Windows\64bit\deadlinecommand.exe'

    job_info, plugin_info = create_job_plugin_info(shot_code, task_type, mov_file, user)

    plugin_file = pyscript

    args = [ dl_command , job_info , plugin_info , plugin_file ]
    command = ' '.join(args)

    p = Popen(command,stdout=PIPE,stderr=PIPE,shell=True)


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



class LuxReview(object):
    '''Custom action.'''

    label = 'Submit for Review'
    identifier = 'submit.for.review'
    description = 'This will slate outputs of selected task(s) and submit it for Review on Ftrack'
    icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/881271-200.png'

    def __init__(self, session):
        '''Initialise action.'''
        super(LuxReview, self).__init__()
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
                'icon': self.icon
            }]
        }

    def launch(self, event):
        '''Callback method for custom action.'''

        data = event['data']
        #print event
        selection = data.get('selection', [])

        #shot_items = []

        entityTypes = ['Project', 'Episode', 'Sequence', 'Shot', 'Task']

        dept_folders = ['01_PLATES','02_INPUT','03_COORDINATION','04_3D','05_COMP','06_RENDERS','07_DAILIES','08_PFTrack','09_QT']


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

        session = ftrack_api.Session()

        template_files = []

        template_files_dir = "L:/HAL/LUX_SLATE/nuke_templates"

        if os.path.isdir(template_files_dir):
            template_files = [i for i in os.listdir(template_files_dir) if i[-3:] == '.nk']

        #shots = []
        #tasks = []

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

            project_id = item['project_id']

            proj = session.query('select custom_attributes from Project where id is "{0}"'.format(project_id)).first()

            object_name = item['name']
            
            item_type = item['object_type']['name']

            #print item['name']
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

            project_name = proj['name']#[i for i in item['ancestors'] if i['object_type']['name'] == 'Project'][0]['name']
            try:
                episode_name = [i for i in item['ancestors'] if i['object_type']['name'] == 'Episode'][0]['name']
            except:
                episode_name = ''
                pass
            #print [i for i in item['ancestors']]#get the project code

            project_code = proj['name']
            project_name = proj['full_name']

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
                'matte_file': '',
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

                    if os.path.isdir(matte_path):
                        imgs = [i for i in os.listdir(matte_path) if grabPattern(i, shot_name+r"(_[a-zA-Z]*)*_[vV](\d{3})-matte\.\d") != '']
                        if len(imgs) >= 1:#frame_duration:#duration:
                            found_image_folders.append(matte_path)
                            imgs.sort()
                            file_types['matte'] = os.path.join(matte_path,imgs[0])

                    if 'JPEG' in file_types:
                        image_file = file_types['JPEG']

                    if 'EXR' in file_types:
                        metad_file = file_types['EXR']

                    if 'DPX' in file_types:
                        metad_file = file_types['DPX']

                    if 'matte' in file_types:
                        matte_file = file_types['matte']

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

                        if matte_file != '':
                            matte_file = matte_file.replace('\\','/').replace('//','/')
                            matte_file = matte_file.replace(pad_pattern, new_pad)
                            item_info['matte_file'] = matte_file

                        item_info['metad_file'] = metad_file
                        item_info['image_file'] = image_file
                        item_info['asset_name'] = folder
                        #slate_output = os.path.join(project_path, project_name, episode_name, "07_DAILIES/SLATED_OUTPUTS/<TEMPLATE_DESCRIPTOR>", folder+'.mov')
                        #slate_output = 'c:\\program files\\bob.mov'
                        default_base_output = os.path.join(base_path, "07_DAILIES/SLATED_OUTPUTS/review")
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

        for i in template_files:
            new_entry =  {}#{dict(template_file_entry)}
            new_entry['label'] = i
            new_entry['value'] = i
            template_items.append(new_entry)


        template_files_selection = {
                    'label': 'Slate Template',
                    'type': 'enumerator',
                    'name': 'my_enumerator',
                    'data': template_items
                }


        for shot in master_dict:

            #project_name = shot['project_name']
            #shot_name = shot['shot_name']
            #image_file = shot['image_file']
            #metad_file = shot['metad_file']
            #output = shot['slate_output']
            #duration = shot['duration']
            #success = shot['success']
            asset_name = shot['asset_name']
            index = shot['index']
            version_items = []
            frame_range = '{0}-{1}'.format( str(shot['first_frame']) , str(shot['last_frame']) )
            text = 'Could not locate rendered files.....\r'
            success_msg = 'FAILED'
            if shot['success']:
                success_msg = 'SUCCESSFUL'

                text = '''
    Offline sequence : {0}\r
    Online sequence  : {1}\r
    Slate Location   : {2}\r
'''.format(shot['image_file'],shot['metad_file'],shot['slate_output'])

                if shot['matte_file'] != '' :
                    #text = text + 'Mattes sequence : {0}\r'.format( shot['matte_file'] )
                    text = '''
    Offline sequence : {0}\r
    Online sequence  : {1}\r
    Matte  sequence  : {3}\r
    Slate Location   : {2}\r
'''.format(shot['image_file'],shot['metad_file'],shot['slate_output'],shot['matte_file'])

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
            shot_items.append(framerange)
            shot_items.append(message)
            

        totalSelectedItems = 0
        totalSlatedItems = 0
        retSuccess = {
            'success': True,
            'message': 'Slating {0}/{1} items!'.format(totalSlatedItems,totalSelectedItems)
        }
        '''
        template_input = [{
                    'label': 'Slate Template:',
                    'type': 'text',
                    'value': "L:/HAL/LUX_SLATE/nuke_templates/Generic_Slate_HD1080_QT_timecode.nk",
                    'name': 'template_file'
                },{
                    'label': 'Make slate default for the project',
                    'type': 'boolean',
                    'value': True,
                    'name': 'make_default'

                },{
                    'value': '<hr>',
                    'type': 'label'
                }]
        '''
        template_files_selection = [{
                    'label': 'Offline Slate',
                    'type': 'enumerator',
                    'name': 'offline_template_file',
                    'data': template_items,
                    'value': proj['custom_attributes']['offline_slate_template']#template_items[0]['label']
                },{
                    'label': 'Online Slate',
                    'type': 'enumerator',
                    'name': 'online_template_file',
                    'data': template_items,
                    'value': proj['custom_attributes']['online_slate_template']#template_items[0]['label']
                },{
                    'label': 'Make default',
                    'type': 'boolean',
                    'value': False,
                    'name': 'make_default'
                },{
                    'value': '<hr>',
                    'type': 'label'
                }]

        slate_txt_items = sorted(['{none}','{date}', '{framecounter}', '{project}', '{projectname}', '{episode}', '{episodename}', '{sequence}', '{shot}', '{shotname}', '{version}', '{task}', '{assetname}', '{description}','{slatename}', '{custom}', '{lens}', '{status}', '{codec}', '{format}', '{firstframe}', '{lastframe}', '{duration}','{logo}','{colorspacein}','{colorspaceout}', 'Lux Visual Effects'])
        slate_txt_positions = []
        for item in slate_txt_items:
            #slate_txt_dct = {'label':item, 'value':item.split('<')[-1].split('>')[0]}
            slate_txt_dct = {'label':item, 'value':item}
            slate_txt_positions.append(slate_txt_dct)

        slate_codecs_raw = ['', 'rle \tAnimation', 'apcn\tApple ProRes 422', 'apch\tApple ProRes 422 HQ', 'apcs\tApple ProRes 422 LT', 'apco\tApple ProRes 422 Proxy', 'ap4h\tApple ProRes 4444', 'ap4x\tApple ProRes 4444 XQ', 'AV1x\tAvid 1:1x', 'AVdn\tAvid DNxHD Codec', 'AVdh\tAvid DNxHR Codec', 'AVdv\tAvid DV Codec', 'AVd1\tAvid DV100 Codec', 'AVj2\tAvid JPEG 2000 Codec', 'AVDJ\tAvid Meridien Compressed', 'AVUI\tAvid Meridien Uncompressed', 'AVup\tAvid Packed Codec', 'AVrp\tAvid RGBPacked Codec', 'WRLE\tBMP', 'cvid\tCinepak', 'yuv2\tComponent Video', 'dvcp\tDV - PAL', 'dvc \tDV/DVCPRO - NTSC', 'dvpp\tDVCPRO - PAL', 'smc \tGraphics', 'h261\tH.261', 'h263\tH.263', 'avc1\tH.264', 'mjp2\tJPEG 2000', 'mp1v\tMPEG-1 Video', 'mp4v\tMPEG-4 Video', 'mjpa\tMotion JPEG A', 'mjpb\tMotion JPEG B', 'raw \tNone', 'png \tPNG', 'jpeg\tPhoto - JPEG', '8BPS\tPlanar RGB', 'SVQ1\tSorenson Video', 'SVQ3\tSorenson Video 3', 'tga \tTGA', 'tiff\tTIFF', 'v210\tUncompressed 10-bit 4:2:2', 'rpza\tVideo']
        slate_codecs = []
        for item in slate_codecs_raw:
            if '\t' not in item:
                item = '\t'+item
            slate_codec_dct = {'label':item.split('\t')[1], 'value':item.split('\t')[0]}
            slate_codecs.append(slate_codec_dct)


        slate_colorspaces_raw = ['', 'default\tdefault', 'linear\tlinear', 'sRGB\tsRGB', 'rec709\trec709', 'Cineon\tCineon', 'Gamma1.8\tGamma1.8', 'Gamma2.2\tGamma2.2', 'Gamma2.4\tGamma2.4', 'Gamma2.6\tGamma2.6', 'Panalog\tPanalog', 'REDLog\tREDLog', 'ViperLog\tViperLog', 'AlexaV3LogC\tAlexaV3LogC', 'PLogLin\tPLogLin', 'SLog\tSLog', 'SLog1\tSLog1', 'SLog2\tSLog2', 'SLog3\tSLog3', 'CLog\tCLog', 'Log3G10\tLog3G10', 'Log3G12\tLog3G12', 'HybridLogGamma\tHybridLogGamma', 'Protune\tProtune', 'BT1886\tBT1886', 'st2084\tst2084']
        slate_colorspaces = []
        for item in slate_colorspaces_raw:
            if '\t' not in item:
                item = '\t'+item
            slate_colorspace_dct = {'label':item.split('\t')[1], 'value':item.split('\t')[0]}
            slate_colorspaces.append(slate_colorspace_dct)

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

        slate_formats = []
        for item in list_of_resolutions:
            slate_res_dct = {'label':item[0], 'value':item[1]}
            slate_formats.append(slate_res_dct)



        slate_settings = [{
            'label': 'Slate Type',
            'type': 'enumerator',
            'name': 'slate_type',
            'value': 'offline2',
            'data': [
                {
                    'label': 'offline',
                    'value': 'offline'
                }, {
                    'label': 'offline2',
                    'value': 'offline2'
                }, {
                    'label': 'online',
                    'value': 'online'
                }
            ]
        },{
            'value': '<hr>',
            'type': 'label'
        }]
        
        
        #Add the slate text options
        for item in slate_settings[::-1]:
            shot_items.insert(0, item)
        

        #Add the slate file options
        '''
        for item in template_files_selection[::-1]:
            shot_items.insert(0, item)
        '''
        retUI = {'items': shot_items}


        date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")



        if 'values' in data:

            # Do something with the values or return a new form.
            values = data['values']
            
            self.logger.info(u'Got values: {0}'.format(values))

            totalSlatedItems = 0

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
      
      
                #print item

                if item['success']:

                    totalSlatedItems += 1

                    item['image_file'] = item['image_file'].replace(item['asset_name'],item['version'])
                    item['metad_file'] = item['metad_file'].replace(item['asset_name'],item['version'])
                    item['slate_output'] = item['slate_output'].replace(item['asset_name'],item['version'])

                    item['asset_name'] = item['version']

                    firstframe = item['first_frame']
                    lastframe = item['last_frame']

                    inputImage   = item['image_file']
                    inputTCImage = item['metad_file']
                    outputImage  = item['slate_output']


                    user = getpass.getuser()

                    temp_dir = "L:\\tmp\\deadline_submission_scripts\\review"

                    if not os.path.isdir(temp_dir):
                        os.makedirs(temp_dir)
                    

                    #print item

                    asset_name = item['asset_name']

                    #Process Offline Slate Submission
                    if values['slate_type']:

                        item['slate_type']      = values['slate_type']

                        if values['slate_type'] == 'offline':
                            print 'offline slate template'
                            item['codec']           = proj['custom_attributes']['slate_codec_offline']
                            item['format']          = proj['custom_attributes']['slate_format_offline']
                            item['slate_frame']     = proj['custom_attributes']['offline_slate_frame']
                            item['overlays']        = proj['custom_attributes']['offline_overlays']
                            item['colorspace_in']   = proj['custom_attributes']['slate_colorspace_in_offline']
                            item['colorspace_out']  = proj['custom_attributes']['slate_colorspace_out_offline']
                            item['data_type']       = proj['custom_attributes']['slate_data_type_offline']
                            item['slate_output']    = proj['custom_attributes']['slate_output_offline']
                            template                = proj['custom_attributes']['offline_slate_template']

                        if values['slate_type'] == 'offline2':
                            print 'offline2 slate template'
                            item['codec']           = proj['custom_attributes']['slate_codec_offline2']
                            item['format']          = proj['custom_attributes']['slate_format_offline2']
                            item['slate_frame']     = proj['custom_attributes']['offline_slate_frame2']
                            item['overlays']        = proj['custom_attributes']['offline_overlays2']
                            item['colorspace_in']   = proj['custom_attributes']['slate_colorspace_in_offline2']
                            item['colorspace_out']  = proj['custom_attributes']['slate_colorspace_out_offline2']
                            item['data_type']       = proj['custom_attributes']['slate_data_type_offline2']
                            item['slate_output']    = proj['custom_attributes']['slate_output_offline2']
                            template                = proj['custom_attributes']['offline_slate_template2']

                        if values['slate_type'] == 'online':
                            print 'online slate template'
                            item['codec']           = proj['custom_attributes']['slate_codec_online']
                            item['format']          = proj['custom_attributes']['slate_format_online']
                            item['slate_frame']     = proj['custom_attributes']['online_slate_frame']
                            item['overlays']        = proj['custom_attributes']['online_overlays']
                            item['colorspace_in']   = proj['custom_attributes']['slate_colorspace_in_online']
                            item['colorspace_out']  = proj['custom_attributes']['slate_colorspace_out_online']
                            item['data_type']       = proj['custom_attributes']['slate_data_type_online']
                            item['slate_output']    = proj['custom_attributes']['slate_output_online']
                            template                = proj['custom_attributes']['online_slate_template']

                        item['format'] = item['format'][0]

                        ##proj['custom_attributes']['slate_offline'] = values['slate_offline']
                        #proj['custom_attributes']['slate_codec_offline'] = values['slate_codec_offline']
                        #proj['custom_attributes']['slate_format_offline'] = values['slate_format_offline']
                        #proj['custom_attributes']['slate_output_offline'] = values['slate_output_offline']
                        #proj['custom_attributes']['offline_slate_template'] = offline_template
                        #proj['custom_attributes']['slate_colorspace_in_offline'] = values['slate_colorspace_in_offline']
                        #proj['custom_attributes']['slate_colorspace_out_offline'] = values['slate_colorspace_out_offline']
                        #proj['custom_attributes']['slate_data_type_offline'] = values['slate_data_type_offline']
                        #proj['custom_attributes']['offline_overlays'] = values['offline_overlays']
                        #proj['custom_attributes']['offline_slate_frame'] = values['offline_slate_frame']

                        '''
                        item['asset_name'] = asset_name
                        item['codec'] = values['slate_codec_offline']
                        item['slate_type'] = 'offline'
                        item['format'] = values['slate_format_offline']
                        item['slate_frame'] = values['offline_slate_frame']
                        item['overlays'] = values['offline_overlays']
                        item['colorspace_in'] = values['slate_colorspace_in_offline']
                        item['colorspace_out'] = values['slate_colorspace_out_offline']
                        item['data_type'] = values['slate_data_type_offline']
                        '''

                        #template = offline_template
                        slate_descriptor = template.split('.')[0]
                        slate_descriptor = slate_descriptor.replace('Generic_Slate_','')
                        slate_descriptor = slate_descriptor.replace('Manual_Slate_','')
                        template_path = os.path.join(template_files_dir, template).replace('\\', '/')

                        item['slate_name'] = slate_descriptor

                        if proj['custom_attributes']['slate_rename_for_client']:

                            #item['asset_name'] = translate(proj['custom_attributes']['slate_rename_with_tags'], proj, item)
                            pass

                        slate_overlays ={
                            'slate_top_left' : translate(proj['custom_attributes']['slate_top_left'], proj, item),
                            'slate_top_right' : translate(proj['custom_attributes']['slate_top_right'], proj, item),
                            'slate_top_center' : translate(proj['custom_attributes']['slate_top_center'], proj, item),
                            'slate_bottom_left' : translate(proj['custom_attributes']['slate_bottom_left'], proj, item),
                            'slate_bottom_right' : translate(proj['custom_attributes']['slate_bottom_right'], proj, item),
                            'slate_bottom_center' : translate(proj['custom_attributes']['slate_bottom_center'], proj, item),
                            'slate_frame_project_title' : translate(proj['custom_attributes']['slate_frame_project_title'], proj, item),
                            'slate_frame_description' : translate(proj['custom_attributes']['slate_frame_description'], proj, item),
                            'slate_frame_shot_title' : translate(proj['custom_attributes']['slate_frame_shot_title'], proj, item),
                            'slate_frame_range_info' : translate(proj['custom_attributes']['slate_frame_range_info'], proj, item),
                            'slate_frame_timecode_info' : translate(proj['custom_attributes']['slate_frame_timecode_info'], proj, item),
                            'slate_frame_version_info' : translate(proj['custom_attributes']['slate_frame_version_info'], proj, item)
                                        }

                        item['slate_overlays'] = slate_overlays

                        slatefile   = os.path.join(temp_dir,item['asset_name']+'_review_slate.nk').replace('\\', '/')
                        job_info    = os.path.join(temp_dir,item['asset_name']+'_review_nuke_job_info.job').replace('\\', '/')
                        plugin_info = os.path.join(temp_dir,item['asset_name']+'_review_nuke_plugin_info.job').replace('\\', '/')

                        #item['slate_output'] = values['slate_output_offline']
                        item['slate_output'] = translate(item['slate_output'], proj, item)

                        #print item['slate_output'] 
                        slate_frame_subtract = 1
                        if item['slate_frame'] == False:
                            slate_frame_subtract = 0
                        
                        frames = "{0}-{1}".format(firstframe, lastframe)
                        sframes = "{0}-{1}".format(str(int(firstframe)-slate_frame_subtract), lastframe)

                        

                        pyscript = "L:/HAL/Alican/ftrack/_hooks/review_submission_hook/review_submitter_011.py"

                        postscript = {'pyscript':pyscript, 'shot_code':item['shot_name'], 'task_type':item['task_name'], 'mov_file':item['slate_output'], 'user':user }

                        extra_info = [item['shot_name'] , item['task_name'] , item['slate_output'] , user, item['asset_name']+' Review', date]

                        CreateNukeSlateFile( slatefile, template_path, item )

                        CreateNukeJob( slatefile, sframes, item['asset_name']+' Review', item['slate_output'], user, job_info, plugin_info, date, extra_info)

                        SubmitJobToDeadline( job_info, plugin_info, slatefile )

                        #submitFtrackReviewToDeadline(pyscript , item['shot_name'] , item['task_name'] , item['slate_output'] , user, item['asset_name']+' Review', date)

                        pass


            retSuccess = {
                'success': True,
                'message': 'Slating {0}/{1} items!'.format(totalSlatedItems,len(master_dict))
            }

            if not totalSlatedItems:
                retSuccess['success'] = False

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

    action = LuxReview(session)
    action.register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()