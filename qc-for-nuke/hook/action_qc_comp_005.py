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

#import datetime

#import io

#import traceback
#from shutil import copyfile
#from subprocess import *
#import sys


#sys.path.append("X:/apps/Scripts/FTRACK/ftrack_hooks/slate_assets_hook/hook")
sys.path.append("X:/apps/Scripts/FTRACK/python-lib")
sys.path.append("X:/apps/Scripts/FTRACK/ython-lib/site-packages")
#import pyperclip
#from lux_utils.get_latest_from import get_latest_from

#import fileinput


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


os.environ['FTRACK_API_USER'] = os.environ.get("USERNAME")

class TaskNoteFromShotNote(object):
    '''Custom action.'''

    label = 'QC for Nuke'
    identifier = 'copy.code.for.qc'
    description = 'Copies a specific code to be pasted into the QC Creator node in Nuke.'
    icon = 'https://static.thenounproject.com/png/1725373-200.png'

    def __init__(self, session):
        '''Initialise action.'''
        super(TaskNoteFromShotNote, self).__init__()
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

        selection = data.get('selection', [])

        entityTypes = ['Shot', 'Task']

        session = ftrack_api.Session()

        #if os.path.isdir(template_files_dir):
        #    template_files = [i for i in os.listdir(template_files_dir) if i[-3:] == '.nk']

        master_dict = []

        index = 0

        #gather shot items from selection
        qc_list = []

        for entity in selection:

            num = 0
            sel_type = entityTypes[num]
            item = session.query('select name from {0} where id is {1}'.format(sel_type, entity['entityId'])).first()


            while item == None:

                num += 1
                sel_type = entityTypes[num]
                item = session.query('select name from {0} where id is {1}'.format(sel_type, entity['entityId'])).first()



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





            #print entity
            #item = session.query('select name, custom_attributes from {0} where id is {1}'.format('Shot', entity['entityId'])).first()

            qc_list.append([str(shot['name']),str(shot['custom_attributes']['base_path'])])
            
        
        def addToClipBoard(text):
            command = 'echo ' + text.strip() + '| clip'
            os.system(command)


        nice_qc_list = str(qc_list)
        #nice_qc_list.replace('u/', '/')
        nice_qc_list = nice_qc_list.replace('[', '\[')
        nice_qc_list = nice_qc_list.replace(']', '\]')
        #pyperclip.copy(nice_qc_list)
        addToClipBoard(nice_qc_list)
        #print nice_qc_list



        retSuccess = {
            'success': True,
            'message': 'Copied the code to clipboard.'
        }


        return retSuccess

        
def register(session, **kw):
    '''Register plugin.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    action = TaskNoteFromShotNote(session)
    action.register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()