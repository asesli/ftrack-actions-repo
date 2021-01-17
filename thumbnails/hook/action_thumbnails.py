'''
Generate Thumbnails Ftrack Hook
Alican Sesli - LUX VFX - 03.12.2019
Submits an event selection from ftrack to a py script to be processed on Deadline
    v15: Submission + various fixes
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

sys.path.append("X:/apps/Scripts/FTRACK/python-lib")

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

def submitPyToDeadline(title, obj):

    def EncodeAsUTF16String( unicodeString ):
        return unicodeString.decode( "utf-8" ).encode( "utf-16-le" )

    now = datetime.now()
    #label = now.strftime("%d-%m-%Y %H:%M:%S")
    name = now.strftime("%d-%m-%Y_%H-%M-%S")

    def create_job_plugin_info():
        #Creates job_info and plugin_info files for submitting to deadline
        # >>>> returns the following
        # > job_info     = path to the job info file
        # > plugin_info  = path to the plugin info file

        # Create job info file.
        deadline_submission_scripts = "L:\\tmp\\deadline_submission_scripts\\generate_thumbnails"

        if not os.path.isdir(deadline_submission_scripts):
            os.makedirs(deadline_submission_scripts)

        job_info = '{0}\\job_info_{1}.job'.format(deadline_submission_scripts,name)
        job_info = unicode(job_info, "utf-8")

        with open(job_info, 'w') as fileHandle: 
            fileHandle.write( "Plugin=%s\n" % 'Python' )
            fileHandle.write( "Name=%s Ftrack Thumbnails\n" % title )
            #fileHandle.write( "UserName=%s\n" % '' )
            fileHandle.write( "Comment =%s Ftrack Thumbnails\n" % title )
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
    plugins_path = '//qumulo/Libraries/HAL/LIVEAPPS/apps/Scripts/FTRACK/ftrack_hooks/thumbnails_hook/hook/'
    plugins = sorted([i for i in os.listdir(plugins_path) if ('thumbnailCreator' in i) and (i.split('.')[-1] == 'py')], reverse =True)
    plugin_file = plugins_path+plugins[0]
    #print plugin_file

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
    


class UpdateThumbnails(object):
    '''Custom action.'''

    label = 'Update Thumbnails'
    identifier = 'update.thumbnails'
    description = 'Update UpdateThumbnails'
    icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/1119801-200.png'

    def __init__(self, session):
        '''Initialise action.'''
        super(UpdateThumbnails, self).__init__()
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


            #no user
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
        #
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

        session = ftrack_api.Session()

        selection = event['data'].get('selection', [])

        one_item =  session.query('select name, project.full_name from TypedContext where id is {0}'.format(selection[0]['entityId'])).first()

        if one_item is not None:

            title = one_item['project']['full_name']

        else:

            one_item = session.query('select id, full_name from Project where id is {0}'.format(selection[0]['entityId'])).first()
            title = one_item['full_name']

        #print title
        #print selection

        submitPyToDeadline( title, selection )

        return {
            'success': True,
            'message': 'Thumbnail Generation Submitted to Deadline'.format()
        }


def register(session, **kw):
    '''Register plugin.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    action = UpdateThumbnails(session)
    action.register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()