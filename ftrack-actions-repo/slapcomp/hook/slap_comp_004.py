'''
Slap Comps Lighting task Ftrack Hook
Alican Sesli - LUX VFX - 02.21.2020- 02.21.2020
Creates files and folders baed on Ftrack Paths.
    v01: Ported from SlapComp_selected_020
    v02: creates nuke script from Ftrack UI
    v03: deadline implementation
    v04: passing file parameter for regular Wrtie nodes because LUX WRITES are problematic when used in a non standard kinda way.
'''
import logging
import ftrack_api
import os, sys
import re
import subprocess
try:
    import ftrack
except:
    pass
import getpass
import time
import shutil

#from shutil import copyfile
from subprocess import *

sys.path.append("X:/apps/Scripts/FTRACK/python-lib")
sys.path.append("X:/apps/Scripts/FTRACK/python-lib/lux_utils")

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

#Creates a job_info and pugin_info files
def CreateNukeJob( _file, _frames, _asset, _outputImage, _user, _job_info, _plugin_info):
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

    # Submit each scene file separately.
    for sceneFile in sceneFiles:
        jobName = _asset + " Slate"
        comments = ['SLATE:', _frames, _user]
        comment = ' '.join(comments)
        if len(sceneFiles) > 1:
            jobName = jobName + " [" + Path.GetFileName( sceneFile ) + "]"
        
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
            writer.write( "ChunkSize=%s\n" % 1 )
        
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
            writer.write( "WriteNode=%s\n" % '' )
            writer.write( "StackSize=%s\n" % 0 )
            writer.write( "UseGpu=%s\n" % False )
            writer.write( "PerformanceProfiler=%s\n" % False )
            writer.write( "PerformanceProfilerDir=%s\n" % '' )

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




class SlapComp(object):
    '''Custom action.'''

    label = 'SlapComp'
    identifier = 'slap.comp.lighting.task'
    description = 'Slap comps the lighting task'
    icon = 'http://static.thenounproject.com/png/2751322-200.png'
    
    def __init__(self, session):
        '''Initialise action.'''
        super(SlapComp, self).__init__()
        self.session = session
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def register(self):
        '''Register action.'''
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

        return {
            'items': [{
                'label': self.label,
                'description': self.description,
                'actionIdentifier': self.identifier,
                'icon': self.icon
            }]
        }

    def launch(self, event):

        start_time = time.time()

        data = event['data']

        #self.logger.info(u'Got values: {0}'.format(values))

        selection = data.get('selection', [])

        def addToClipBoard(text):
            command = 'echo ' + text.strip() + '| clip'
            os.system(command)

        for entity in selection:

            entityId = entity['entityId']

            selType = entity['entityType']

            sel = self.session.query('select custom_attributes, object_type.name, type.name, parent.name, parent.custom_attributes, link, name, project.custom_attributes from TypedContext where id is "{0}"'.format(entityId)).first()

            base_path = sel['custom_attributes']['base_path']
            out_path = sel['custom_attributes']['out_path']
            shot_name =  sel['parent']['name']

            plates_dir = '{}01_PLATES/{}/PLATE/'.format(base_path, shot_name)
            plate_folders = os.listdir(plates_dir)

            render_folders = [x[0].replace('\\','/')+'/' for x in os.walk(out_path)]

            comp_dir = '{}05_COMP/{}/'.format(base_path, shot_name)

            mattes_dir = '{}02_OUTPUT/02_mattes/'.format(comp_dir)
            mattes_folders = os.listdir(mattes_dir)

            slap_comps = list(set([i.split('.')[0] for i in os.listdir(comp_dir) if '{}_slapcomp'.format(shot_name.lower()) in i.lower()]))

            if not slap_comps:
                slap_comp_nk = '{}{}_SlapComp_v001.nk'.format(comp_dir,shot_name)

            else:
                slap_comps = sorted(slap_comps)
                last_slap_comp = slap_comps[-1]
                last_slap_comp_version = int(last_slap_comp.lower().split('_v')[-1])
                new_slap_comp_version = str(last_slap_comp_version+1).zfill(3)
                slap_comp_nk = '{}{}_SlapComp_v{}.nk'.format(comp_dir,shot_name,new_slap_comp_version)

            #print slap_comp_nk

        slap_comp_version = int(slap_comp_nk.split('.')[0].lower().split('_v')[-1])
        slap_comp_out_dir = '{}02_OUTPUT/01_precomp/SlapComp/SlapComp_V{}/'.format(comp_dir,str(slap_comp_version).zfill(3))

        file_out = '{}SlapComp_V{}.%04d.ext'.format( slap_comp_out_dir, str(slap_comp_version).zfill(3) )

        plates = []
        for i in plate_folders:
            plates_dct = {'label':i, 'value':'{}{}/01_EXRS/{}.%04d.exr'.format(plates_dir, i, shot_name)}
            plates.append(plates_dct)

        renders = []
        for i in render_folders:
            renders_dct = {'label':i.split('/FINL/')[-1], 'value':i}
            renders.append(renders_dct)

        shadows = []
        for i in render_folders:
            shadows_dct = {'label':i.split('/FINL/')[-1], 'value':i}
            shadows.append(shadows_dct)

        mattes = []
        for i in mattes_folders:
            mattes_dct = {'label':i, 'value':'{}{}/'.format(mattes_dir, i)}
            mattes.append(mattes_dct)


        user = getpass.getuser()

        slapCompSettings = {
            'items': [
                {
                    'label': '<font color="green">Plate</font>',
                    'type': 'enumerator',
                    'value': '',
                    'data' : plates,
                    'name': 'plate'
                }, {
                    'label': '<font color="green">3D renders</font>',
                    'type': 'enumerator',
                    'value': '',
                    'data' : renders,
                    'multi_select' : True,
                    'name': 'renders'
                }, {
                    'label': '<font color="green">Shadows</font>',
                    'type': 'enumerator',
                    'value': '',
                    'data' : shadows,
                    'multi_select' : True,
                    'name': 'shadows'
                }, {
                    'label': '<font color="green">Mattes</font>',
                    'type': 'enumerator',
                    'value': '',
                    'data' : mattes,
                    'multi_select' : True,
                    'name': 'mattes'
                },{
                    'label': '<font color="green">Apply Colour to 3D Renders</font>',
                    'type': 'boolean',
                    'value': False, 
                    'name': 'colour'
                },{
                    'label': '<font color="green">Calculation Frame</font>',
                    'type': 'text',
                    'value': '1001',#proj['custom_attributes']['slate_rename_with_tags'],
                    'name': 'colour_frame'
                },{
                    'label': '<font color="green">Apply LUT</font>',
                    'type': 'boolean',
                    'value': False, 
                    'name': 'lut'
                },{
                    'label': '<font color="green">Apply Grain</font>',
                    'type': 'boolean',
                    'value': False, 
                    'name': 'grain'
                },{
                    'label': '<font color="green">Apply Lens Distortion to CG</font>',
                    'type': 'boolean',
                    'value': False, 
                    'name': 'distortion'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': '<font color="green">Submit to Deadline</font>',
                    'type': 'boolean',
                    'value': False, 
                    'name': 'submit_to_deadline'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'value': slap_comp_nk,
                    'type': 'label'
                }
            ]
        }
        

        if 'values' in data:

            values = data['values']

            self.logger.info(u'Got values: {0}'.format(values))

            ftrack_dict = {
                'plate'         : values['plate'],
                'renders'       : values['renders'],
                'shadows'       : values['shadows'],
                'mattes'        : values['mattes'],
                'grain'         : values['grain'],
                'colour'        : values['colour'],
                'colour_frame'  : values['colour_frame'],
                'lut'           : values['lut'],
                'distortion'    : values['distortion'],
                'version'       : slap_comp_version,
                'user'          : user,
                'file_out'      : file_out
            }


            if not os.path.exists(slap_comp_out_dir):
                os.makedirs(slap_comp_out_dir)
            
            print ftrack_dict

            proj_format = sel['project']['custom_attributes']['resolution'][0]

            shot_fps            = sel['parent']['custom_attributes']['fps']
            if shot_fps != None:    shot_fps=float(shot_fps)
            else:   shot_fps=float(24)

            shot_timecode       = sel['parent']['custom_attributes']['Timecode']
            if shot_timecode != None:    shot_timecode=str(shot_timecode)
            else:   shot_timecode=str('00:00:00:00')

            shot_first_frame    = sel['parent']['custom_attributes']['first_frame']
            if shot_first_frame != None:    shot_first_frame=int(shot_first_frame)
            else:   shot_first_frame=1


            shot_last_frame     = sel['parent']['custom_attributes']['last_frame']
            if shot_last_frame != None:    shot_last_frame=int(shot_last_frame)
            else:   shot_last_frame=100


            comp_template = "X:/apps/Scripts/FTRACK/nuke_templates/basic_comp_template.nk"

            file = { 'template':comp_template, 'newfile':slap_comp_nk, 'first_frame':shot_first_frame, 'last_frame':shot_last_frame, 'fps':shot_fps, 'format':'"'+proj_format+'"', 'timecode': shot_timecode }
            
            shutil.copy(file['template'], file['newfile'])

            with open(file['newfile'], 'r+') as content_file:
                content = content_file.read()

                content = content.replace('<timecode>', str(file['timecode']))
                content = content.replace('<first_frame>', str(file['first_frame']))
                content = content.replace('<last_frame>', str(file['last_frame']))
                content = content.replace('<fps>', str(file['fps']))
                content = content.replace('<format>', str(file['format']))

                content = content.replace('<onScriptLoad>', '"'+"import importAssets;reload(importAssets);importAssets.ImportAssets().sanityCheck();importAssets.ImportAssets().slapComp3D({})".format(ftrack_dict)+'"')
                content = content.replace('<onScriptSave>', "nuke.Root()['onScriptLoad'].setValue('');nuke.Root()['onScriptSave'].setValue('')")

                content_file.seek(0)
                content_file.write(content)
                content_file.truncate()


            addToClipBoard(slap_comp_nk)

            if values['submit_to_deadline']:

                print 'deadline submission'



                temp_dir = "L:\\tmp\\deadline_submission_scripts\\slapcomps"
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)

                name = slap_comp_nk.split('.')[0].split('/')[-1]

                job_info    = os.path.join(temp_dir,'{}_nuke_job_info.job'.format( name )).replace('\\', '/')
                plugin_info = os.path.join(temp_dir,'{}_nuke_plugin_info.job'.format( name )).replace('\\', '/')

                sframes = '{}-{}'.format(shot_first_frame, shot_last_frame)

                CreateNukeJob( slap_comp_nk, sframes, "blablablabla", "more bla bla", user, job_info, plugin_info)

                SubmitJobToDeadline( job_info, plugin_info, slap_comp_nk )


            return {
                'success': True,
                'message': 'Slap Comp Created!'
            }

        return slapCompSettings    
          

def register(session, **kw):
    '''Register plugin.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    action = SlapComp(session)
    action.register()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()