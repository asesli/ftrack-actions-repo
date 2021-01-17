'''
Copy Nuke Path Ftrack Hook
Alican Sesli - LUX VFX - 03.12.2019
Copies the latest path of a work file to clipboard.
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
import subprocess

sys.path.append("X:/apps/Scripts/FTRACK/python-lib")
sys.path.append("X:/apps/Nuke11.2v4/lib")

FTRACK_URL = 'https://domain.ftrackapp.com'
FTRACK_KEY = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

os.environ['FTRACK_SERVER'] = FTRACK_URL
os.environ['FTRACK_API_KEY'] = FTRACK_KEY

class CopyPath(object):
    '''Action to copy the OS path of an item. (custom_attributes/path)'''

    label = 'Copy Path'
    identifier = 'copy.job.path'
    description = 'Copies paths'
    icon = 'https://static.thenounproject.com/png/1000344-200.png'
    variant = 'Latest Task File'

    def __init__(self, session):
        '''Initialise action.'''
        super(CopyPath, self).__init__()
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
                'icon': self.icon,
                'variant' : self.variant
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


        data = event['data']



        selection = data.get('selection', [])

        file = None

        for entity in selection:

            entityId = entity['entityId']
            selType = entity['entityType']

            #shots = self.session.query('select custom_attributes, object_type.name, project_id, type.name, parent.name, name from Shot where children.id is "{0}" or ancestors.id is "{0}" or project_id is "{0}" or id is "{0}"'.format(entityId)).all()
            
            task = self.session.query('select custom_attributes, object_type.name, type.name, parent.name, name from Task where id is "{0}"'.format(entityId)).first()
            
            task_path = task['custom_attributes']['path']
            task_name = task['name']
            shot_name = task['parent']['name']
            task_type = task['type']['name']


            if task_type in ['Precomp', 'Compositing', 'Paintout', 'Breakdown', 'Retime']:

                nuke_files = [str(i) for i in os.listdir(task_path) if i.split('.')[-1]=='nk' and shot_name.lower() in i.lower()]

                if task_name == 'Compositing':

                    nuke_files = [i for i in nuke_files if '_comp' in i.lower()]

                else:

                    nuke_files = [i for i in nuke_files if '_'+task_name.lower() in i.lower()]

                nuke_files = [i for i in nuke_files if len(i.lower().split('.')[0].split('_v')[-1]) == 3]
                nuke_files = sorted(nuke_files, key=lambda s: s.lower(), reverse=True)
                nuke_files = [task_path+i for i in nuke_files]

                latest_nuke_file = nuke_files[0]
                file = latest_nuke_file

                print file

        if file != None:

            def addToClipBoard(text):
                
                text = text.strip()
                command = 'echo ' + text + '|clip'
                os.system(command)

            addToClipBoard(file)

            return {
                'success': True,
                'message': 'Copied path to clipboard: <br><br> {0}'.format(file)
            }
        else:

            return {
                'success': False,
                'message': 'No applicable files exist for this task.'
            }
        
def register(session, **kw):
    '''Register plugin.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    action = CopyPath(session)
    action.register()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()
