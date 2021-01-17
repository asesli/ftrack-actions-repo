'''
Generate Actuals Ftrack Hook
Alican Sesli - LUX VFX - 03.12.2019
Submits an event selection from ftrack to a py script to be processed on Deadline
    v14: Overhaul
    v15: Deadline intergration/submission
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
from datetime import datetime
import io
import traceback
from shutil import copyfile
from subprocess import *
import sys


sys.path.insert(0, "L:\\HAL\\LIVEAPPS\\apps\\Scripts\\FTRACK\\python-lib\\Lib")


import xlsxwriter
from datetime import datetime


sys.path.append("X:/apps/Scripts/FTRACK/python-lib")

os.environ["PYTHONHOME"] = r"C:\Python27"
os.environ["PYTHONPATH"] = r"C:\Python27\Lib"

FTRACK_URL = 'https://domain.ftrackapp.com'
FTRACK_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

os.environ['FTRACK_SERVER'] = FTRACK_URL
os.environ['FTRACK_API_KEY'] = FTRACK_KEY

def submitPyToDeadline(title, obj):

    def EncodeAsUTF16String( unicodeString ):
        return unicodeString.decode( "utf-8" ).encode( "utf-16-le" )

    now = datetime.now()
    #label = now.strftime("%d-%m-%Y %H:%M:%S")
    name = now.strftime("%Y-%m-%d_%H-%M-%S")

    def create_job_plugin_info():
        #Creates job_info and plugin_info files for submitting to deadline
        # >>>> returns the following
        # > job_info     = path to the job info file
        # > plugin_info  = path to the plugin info file

        # Create job info file.
        deadline_submission_scripts = "L:\\tmp\\deadline_submission_scripts\\generate_actuals"

        if not os.path.isdir(deadline_submission_scripts):
            os.makedirs(deadline_submission_scripts)

        job_info = '{0}\\job_info_{1}.job'.format(deadline_submission_scripts,name)
        job_info = unicode(job_info, "utf-8")

        with open(job_info, 'w') as fileHandle: 
            fileHandle.write( "Plugin=%s\n" % 'Python' )
            fileHandle.write( "Name=%s Ftrack Actuals\n" % title )
            #fileHandle.write( "UserName=%s\n" % '' )
            fileHandle.write( "Comment =%s Ftrack Actuals\n" % title )
            fileHandle.write( "Frames=%s\n" % '1' )
            fileHandle.write( "Pool=%s\n" % 'maya2018' )
            fileHandle.write( "Priority=%s\n" % '99' )
            #fileHandle.write( "OutputFilename0=%s\\\n" % arg_dest_path )

        # Create the plugin info file
        plugin_info = '{0}\\plugin_info_{1}.job'.format(deadline_submission_scripts,name)

        with open(plugin_info, 'w') as fileHandle: 
            fileHandle.write( 'Arguments="%s"\n' % (str(obj)))#, arg_original_name) )
            fileHandle.write( "Version=%s\n" % '2.7' )
            fileHandle.write( "SingleFramesOnly=%s\n" % 'False' )

        return job_info, plugin_info

    dl_command  = r'L:\DeadlineRepository10\bin\Windows\64bit\deadlinecommand.exe'

    job_info, plugin_info = create_job_plugin_info()

    #plugin_file = '//qumulo/Libraries/HAL/LIVEAPPS/apps/Scripts/FTRACK/ftrack_hooks/thumbnails_hook/hook/thumbnailCreator_002.py'

    plugins_path = '//qumulo/Libraries/HAL/LIVEAPPS/apps/Scripts/FTRACK/ftrack_hooks/generate_actuals_hook/hook/'

    plugins = sorted([i for i in os.listdir(plugins_path) if ('actualsCreator' in i) and (i.split('.')[-1] == 'py')], reverse =True)

    plugin_file = plugins_path+plugins[0]
    print plugin_file

    args = [ dl_command , job_info , plugin_info , plugin_file ]
    command = ' '.join(args)

    #print command
    p = Popen(command,stdout=PIPE,stderr=PIPE,shell=True)
    
    '''
    stdout,stderr=p.communicate()
    if stderr:
        print "STDERR : ", stderr
    else:
        print "STDOUT : ", stdout
    '''
    



class GenerateActuals(object):
    '''Custom action.'''

    label = 'Generate Actuals'
    identifier = 'generate.actuals'
    description = 'Generate Actuals'
    icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/53525-200.png'

    def __init__(self, session):
        '''Initialise action.'''
        super(GenerateActuals, self).__init__()
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

        #Check to see if the user trying to run this action belongs in the admin_roles
        '''
        admin_roles = ['API', 'Administrator', 'Project Manager']
        user_id = event['source']['user']['id']
        user =  self.session.query('User where id is "{0}"'.format(user_id)).one()
        user_roles = [str(i['security_role']['name']) for i in user['user_security_roles']]
        if not bool(set(user_roles).intersection(admin_roles)):
            return False
        '''
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

        session = ftrack_api.Session()

        user = getpass.getuser()

        selection = event['data'].get('selection', [])

        one_item =  session.query('select name, project.full_name from TypedContext where id is {0}'.format(selection[0]['entityId'])).first()

        if one_item is not None:

            title = one_item['project']['full_name']

        else:

            one_item = session.query('select id, full_name from Project where id is {0}'.format(selection[0]['entityId'])).first()

            title = one_item['full_name']
        
        entityId = selection[0]['entityId']

        one_task = session.query('select parent.parent from Task where ancestors.id is "{0}" or project_id is "{0}" or id is "{0}"'.format(entityId)).first()

        path = one_task['custom_attributes']['base_path']

        path = path + '03_COORDINATION/'


        ids = [str(i.get('entityId')) for i in selection]
        #print ids
        if len(ids)>1:
            ids = tuple(ids)
        else:
            ids = "({})".format(ids[0])

        #names = session.query('select name from TypedContext where id in "{}"'.format(ids)).all()
        names = session.query("select name from TypedContext where id in {}".format(ids)).all()
        name='Actuals-'
        #print names
        names = list(set(names))
        for n in names:
            name+= n['name']+'-'
            title += ' - '+ n['name'] 
        name = name[:-1]

        sheetname = "sheet-{}".format(user)

        datestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        file = "{0}{1}-{2}.xlsx".format( path, name, datestamp )

        print file
        
        submission_d = {'selection':selection, 'user':user, 'out_file':file}

        submitPyToDeadline( title, submission_d )

        self.browse(os.path.dirname(file))

        return {
            'success': True,
            'message': 'Actuals Submitted to Deadline<br>{}'.format(file)
        }


def register(session, **kw):
    '''Register plugin.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    action = GenerateActuals(session)
    action.register()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()