'''
Contactsheet Ftrack Hook
Alican Sesli - LUX VFX - 03.12.2019
Creates a Contact Sheet based on selected tasks
    v5: House Cleaning (comments)
    v7: hex_to_rgb lstrip issue
    v8: hex issue still there, trying to retrieve status.color from ftrack instead. something about ftrack symbol cannot be replaced with .replace.. whatever. maybe now
'''
import logging
import ftrack_api
import os
try:
    import ftrack
except:
    pass
import getpass
import sys
from shutil import copyfile
from subprocess import *
import datetime
import io
import traceback

sys.path.append("X:/apps/Scripts/FTRACK/ftrack_hooks/slate_hook/hook")
sys.path.append("X:/apps/Scripts/FTRACK/python-lib")

from lux_utils.get_latest_from import get_latest_from

import fileinput

os.environ["PYTHONHOME"] = r"C:\Python27"
os.environ["PYTHONPATH"] = r"C:\Python27\Lib"


FTRACK_URL = 'https://domain.ftrackapp.com'
FTRACK_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

os.environ['FTRACK_SERVER'] = FTRACK_URL
os.environ['FTRACK_API_KEY'] = FTRACK_KEY

class ContactSheet(object):
    '''Contact Sheet action'''

    label = 'Contact sheet selected tasks'
    identifier = 'make.contact.sheet'
    description = 'Generates a contact sheet using the latest ouputs of the selected tasks'
    icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/1366577-200.png'

    def __init__(self, session):
        '''Initialise action.'''
        super(ContactSheet, self).__init__()
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

    def browse(self, path): 

        browse_dir = path
        platform = sys.platform

        if platform == 'darwin':
            os.system('open %s' % browse_dir)

        if platform == 'linux2':
            os.system('nautilus %s' % browse_dir)

        if platform == 'win32':
            browse_dir = browse_dir.replace('/', '\\')
            os.system('explorer %s' % browse_dir)

    def launch(self, event):

        #Creates a job_info and pugin_info files
        def SubmitNukeJob( _file, _frames, _asset, _outputImage, _user, _job_info, _plugin_info):
            global scriptDialog

            version = 10.0
            
            # Check the Nuke files.
            sceneFiles = [_file]
            if( len( sceneFiles ) == 0 ):
                scriptDialog.ShowMessageBox( "No Nuke file specified", "Error" )
                return

            # Check if a valid frame range has been specified.
            frames = _frames
            '''
            if( not FrameUtils.FrameRangeValid( frames ) ):
                scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
                return
            '''
            successes = 0
            failures = 0
            #print _asset
            # Submit each scene file separately.
            for sceneFile in sceneFiles:
                jobName = "ContactSheet Submission: " + _asset
                comments = ['ContactSheet:', _frames, _user]
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
                    writer.write( "ChunkSize=%s\n" % 20 )
                


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
                    writer.write( "WriteNode=%s\n" % 'Write_JPEG' )
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
            stdout,stderr=p.communicate()

            if stderr:
                print "STDERR : ", stderr
            else:
                print "STDOUT : ", stdout

        def _replaceAll(nkFile,searchExp,replaceExp):
            try:
                slate_file.close()
            except:
                pass

            slate_file = fileinput.input(nkFile, inplace=1)

            for line in slate_file:
                if searchExp in line:
                    line = line.replace(searchExp,replaceExp)
                sys.stdout.write(line)
            slate_file.close()

        def hex_to_rgb(value):
            #value = value.lstrip('#')
            value = value.replace('#','')
            lv = len(value)
            return tuple(float(int(value[i:i + lv // 3], 16))/255 for i in range(0, lv, lv // 3))

        data = event['data']
        selection = data.get('selection', [])

        #options
        contact_sheet_name = 'cs001'#name
        search_file_type = 'jpeg'#input image type
        render_file_type = 'jpeg'

        final_scale_factor = 0.5 # Multiplier Reformat that down scales the contact sheet. 

        global_font_scale = 0.5 # Size of the font
        scale = 1 # Multiplier for the size of each individual panel
        disable_label = False # Disables the titles on panels
        disable_status_colour = False # Disables the status colours on each panel
        show_assignee = True # Show the current assignee of is task

        controller_options = { 'disable_label':disable_label,'disable_status_colour':disable_status_colour,'global_font_scale':global_font_scale,'scale':scale }

        base_path = ''
        images = []
        msg = 'Creating a contact sheet from outputs of {0} selected tasks..<br><br>'
        on_script_load = '''"for node in nuke.allNodes():
    if node.Class() == 'Read':
        try:
            dict = eval(node['label'].value())
            for key in dict.keys():
                if key == 'first':  node[key].setValue(dict[key]),node['origfirst'].setValue(dict[key])
                if key == 'last':   node[key].setValue(dict[key]),node['origlast'].setValue(dict[key])
                if key == 'file':   node[key].setValue(dict[key])
        except:
            pass
for node in nuke.allNodes():
    if 'cs_label' in node.name():
        try:
            if node.input(0)['file'].value() == '':
                node['message'].setValue('')
            dict = eval(node.input(0)['label'].value())
            rgba = [dict['r'],dict['g'],dict['b'],1.0]
            user = dict['user']
            node['color'].setValue(rgba)
            if node.input(0)['file'].value() == '':
                node['message'].setValue('')
            node.setSelected(True)
            rn = nuke.createNode('Retime')
            rn['input.first_lock'].setValue(True)
            rn['input.last_lock'].setValue(True)
            rn['input.first'].setValue(node.input(0)['first'].value())
            rn['input.last'].setValue(node.input(0)['last'].value())
            rn['before'].setValue('loop')
            rn['after'].setValue('loop')
            rn.setSelected(False)
            node.setSelected(False)
        except:
            pass
    if node.Class() == 'NoOp':
        try:
            dict = eval(node['label'].value())
            for key in dict.keys():
                if key == 'disable_label':  node[key].setValue(dict[key])
                if key == 'disable_status_colour':  node[key].setValue(dict[key])
                if key == 'global_font_scale':  node[key].setValue(dict[key])
                if key == 'scale':  node[key].setValue(dict[key])
        except:
            pass"
'''

        # Retrieve task specific parameters

        retUI = {
            'items': [
                {
                    'label': 'My String',
                    'type': 'text',
                    'value': 'no string',
                    'name': 'my_string'
                }, {
                    'label': 'My String2',
                    'type': 'text',
                    'value': 'no string2',
                    'name': 'my_string2'
                }, {
                    'label': 'My Date',
                    'type': 'date',
                    'name': 'my_date',
                    'value': datetime.date.today().isoformat()
                }, {
                    'label': 'My Number',
                    'type': 'number',
                    'name': 'my_number',
                    'empty_text': 'Type a number here...'
                }, {
                    'value': '## This is a label. ##',
                    'type': 'label'
                }, {
                    'label': 'Enter your text',
                    'name': 'my_textarea',
                    'value': 'some text',
                    'type': 'textarea'
                }, {
                    'label': 'My Boolean',
                    'name': 'my_boolean',
                    'value': True,
                    'type': 'boolean'
                }, {
                    'value': 'This field is hidden',
                    'name': 'my_hidden',
                    'type': 'hidden'
                }, {
                    'label': 'My Enum',
                    'type': 'enumerator',
                    'name': 'my_enumerator',
                    'data': [
                        {
                            'label': 'Option 1',
                            'value': 'opt1'
                        }, {
                            'label': 'Option 2',
                            'value': 'opt2'
                        }
                    ]
                }
            ]
        }
        #return retUI
        request_file_type = {
            'items': [
                {
                    'label': 'Contact sheet name',
                    'type': 'text',
                    'value': '',
                    'name': 'contact_sheet_name',
                    'empty_text':'Name your contact sheet!'
                },{
                    'value': '## What FILE TYPE do you want to SOURCE to contact sheets from? ##',
                    'type': 'label'
                },{
                    'label': 'Source file type',
                    'type': 'enumerator',
                    'name': 'search_file_type',
                    'value': search_file_type,
                    'data': [
                        {
                            'label': 'jpeg',
                            'value': 'jpeg'
                        }, {
                            'label': 'exr',
                            'value': 'exr'
                        }, {
                            'label': 'dpx',
                            'value': 'dpx'
                        }
                    ]
                },{
                    'value': '## What FILE TYPE do you want to RENDER contact sheets as? ##',
                    'type': 'label'
                },{
                    'label': 'Output file type',
                    'type': 'enumerator',
                    'name': 'render_file_type',
                    'value': render_file_type,
                    'data': [
                        {
                            'label': 'jpeg',
                            'value': 'jpeg'
                        }, {
                            'label': 'exr',
                            'value': 'exr'
                        }, {
                            'label': 'dpx',
                            'value': 'dpx'
                        }
                    ]
                },{
                    'value': '## Extra settings ##',
                    'type': 'label'
                }, {
                    'label': 'Contact sheet scale',
                    'type': 'number',
                    'name': 'final_scale_factor',
                    'value': final_scale_factor
                }, {
                    'label': 'Show Label',
                    'name': 'disable_label',
                    'value': True,
                    'type': 'boolean'
                }, {
                    'label': 'Show Status colour',
                    'name': 'disable_status_colour',
                    'value': True,
                    'type': 'boolean'
                }, {
                    'label': 'Show assignee',
                    'name': 'show_assignee',
                    'value': True,
                    'type': 'boolean'
                }, 
            ]
        }

        if 'values' in data:

            values = data['values']
            self.logger.info(u'Got values: {0}'.format(values))

            contact_sheet_name = values['contact_sheet_name']
            search_file_type = values['search_file_type']
            render_file_type = values['render_file_type']

            #scale = float(values['scale'])#1.0 # Multiplier for the size of each individual panel
            #global_font_scale = float(values['global_font_scale'])#0.5 # Size of the font
            final_scale_factor = float(values['final_scale_factor'])#0.5 # Multiplier Reformat that down scales the contact sheet. 

            disable_label = not bool(values['disable_label'])#False # Disables the titles on panels
            disable_status_colour = not bool(values['disable_status_colour'])#False # Disables the status colours on each panel
            show_assignee = bool(values['show_assignee'])#True # Show the current assignee of is task

            if not contact_sheet_name:
                return {
                    'success': False,
                    'message': 'Name your contact sheet!'
                }

            contact_sheet_name = contact_sheet_name.replace(' ', '_')

            for entity in selection:

                entityId = entity['entityId']
                selType = entity['entityType']

                task = self.session.query('select status, status.color, custom_attributes from Task where id is "{0}"'.format(entityId)).first()

                shot = self.session.query('select custom_attributes from Shot where id is "{0}"'.format(entityId)).first()
                #shot = self.session.query('select status, custom_attributes from Task where id is "{0}"'.format(entityId)).first()

                if (not task) and (not shot):
                    return {
                        'success': False,
                        'message': 'No tasks/shots selected..'
                    }

                assignee = ''

                if show_assignee and task:

                    users = self.session.query(
                        'select first_name, last_name from User '
                        'where assignments any (context_id = "{0}")'.format(task['id']))

                    for user in users:
                        user = str(user['first_name'])+' '+str(user['last_name'][0])
                        assignee+=' '+user

                if task:
                    base_path = task['custom_attributes']['base_path']
                    out_path = task['custom_attributes']['out_path']
                    work_path = task['custom_attributes']['path']
                    status_colour = task['status']['color']
                    #print status_colour
                    r,g,b = hex_to_rgb(status_colour)
                    r,g,b = round(r,4),round(g,4),round(b,4)
                    status_colour = '{0} {1} {2} {3} {4}'.format('{',r,g,b,'}')


                if shot:
                    base_path = shot['custom_attributes']['base_path']
                    out_path = shot['custom_attributes']['out_path']
                    #work_path = task['custom_attributes']['path']
                    #status_colour = task['status']['color']

                    #r,g,b = hex_to_rgb(status_colour)
                    #r,g,b = round(r,4),round(g,4),round(b,4)
                    #status_colour = '{0} {1} {2} {3} {4}'.format('{','0','0','0','}')
                    r,g,b = '0','0','0'


                version_info = get_latest_from(out_path, search_file_type)

                if version_info != None:

                    image_sequence = version_info[0]
                    first_frame = version_info[1][0]
                    last_frame = version_info[1][1]

                    image = { 'file':image_sequence,'first':first_frame,'last':last_frame,'r':r,'g':g,'b':b, 'user':assignee }
                    images.append(image)
            
            images = sorted(images, key=lambda k: k['file']) 

            if images:

                contact_sheet_path = base_path+'05_COMP/_contactsheets/'
                contact_sheet_scripts = contact_sheet_path +'scripts/'
                contact_sheet_renders  = contact_sheet_path +'renders/'+ contact_sheet_name + '/'
                contact_sheet_file = contact_sheet_scripts+ contact_sheet_name + '.nk'
                contact_sheet_output = contact_sheet_renders + contact_sheet_name+'.####.'+render_file_type
                contact_sheet_output_DPX = contact_sheet_renders + contact_sheet_name +'.####.'+'dpx'
                contact_sheet_output_EXR = contact_sheet_renders + contact_sheet_name +'.####.'+'exr'
                contact_sheet_output_raw = contact_sheet_renders + contact_sheet_name +'.####.'+'exr'
                contact_sheet_temp_file_dir = contact_sheet_path +'_temp/'+ contact_sheet_name + '/'

                if not os.path.isdir(contact_sheet_scripts):
                    try:
                        os.makedirs(contact_sheet_scripts)
                    except WindowsError:
                        pass

                if not os.path.isdir(contact_sheet_renders):
                    os.makedirs(contact_sheet_renders)

                if not os.path.isdir(contact_sheet_temp_file_dir):
                    os.makedirs(contact_sheet_temp_file_dir)  

                firstframe = str(sorted(images, key=lambda k: k['first'])[0]['first'])
                lastframe  = str(sorted(images, key=lambda k: k['last'])[-1]['last'])

                # Duplicate the nuke template
                copyfile("X:/apps/Scripts/FTRACK/nuke_templates/contact_sheet_template.nk", contact_sheet_file)
                # Settings
                _replaceAll(contact_sheet_file, '1062710627', str(len(images)) )
                _replaceAll(contact_sheet_file, '-999999999', firstframe )
                _replaceAll(contact_sheet_file, '999999999', lastframe )
                _replaceAll(contact_sheet_file, '<output_path_jpeg>', contact_sheet_output )
                _replaceAll(contact_sheet_file, '<output_path_exr>', contact_sheet_output_EXR )
                _replaceAll(contact_sheet_file, '<output_path_dpx>', contact_sheet_output_DPX )
                _replaceAll(contact_sheet_file, '<on_script_load>', on_script_load )
                _replaceAll(contact_sheet_file, '0.91919191', str(final_scale_factor) )
                _replaceAll(contact_sheet_file, '<controller_options>', '{'+str(controller_options)+'}')

                msg = msg.format(len(images))
                msg+= 'Submitting contact sheet to Deadline!<br><h2><b>Nuke Script: {0}<br>Renders: {1}</br><br></h2>'.format(contact_sheet_file, contact_sheet_output)

                for index, image_info in enumerate(images):
                    ### this replaces < # > in the label of the nuke node to a dictionary! 
                    ### onScriptLoad processes this dict. and populates each nodes params!
                    num = index+1
                    print num, image_info
                    #{ 'file':image_sequence,'first':first_frame,'last':last_frame,'r':r,'g':g,'b':b, 'user':assignee }
                    #new_msg = '{0}<br><br>'.format(image_info['file'],image_info['user'])
                    new_msg = '{2}) {0}   {1}<br><br>'.format(image_info['file'].split('/')[-1],image_info['user'],num)
                    msg+=new_msg

                    _replaceAll(contact_sheet_file, '<'+str(num)+'>', '{'+str(image_info)+'}')


                # # # SUBMIT THE NUKE FILE TO THE FARM NOW! # # #    

                #contact_sheet_file = contact_sheet_file
                job_info = contact_sheet_temp_file_dir + contact_sheet_name +'_nuke_job_info.job'
                plugin_info = contact_sheet_temp_file_dir + contact_sheet_name +'_nuke_plugin_info.job'
                user = getpass.getuser()
                asset = contact_sheet_name
                sframes = "{0}-{1}".format(str(int(firstframe)), lastframe)
                #outputImage = contact_sheet_output

                SubmitNukeJob( contact_sheet_file, sframes, asset, contact_sheet_output, user, job_info, plugin_info)

                SubmitJobToDeadline( job_info, plugin_info, contact_sheet_file )

                


                return {
                    'success': True,
                    'message': '{0}'.format(msg)
                }

        return request_file_type
        
def register(session, **kw):
    '''Register plugin.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    action = ContactSheet(session)
    action.register()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()