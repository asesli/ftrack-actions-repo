'''
Open folder Ftrack Hook
Alican Sesli - LUX VFX - 08.11.2019 - 01.29.2020
Opens the working folder of a selected item in Windows Explorer
    v3: first version
    v4: message now displays the folder that is being opened
    v5: variant changed from Shot Folder to Task Folder
'''

import logging
import ftrack_api
import os
try:
    import ftrack
except ImportError:
    pass
import getpass
import sys
#import subprocess

# setup ftrack environment
try:
    sys.path.insert(0,"L:/HAL/LIVEAPPS/apps/Scripts/FTRACK/ftrack_events/resources")
    import credentials

    os.environ["FTRACK_SERVER"]  = credentials.server_url
    os.environ["FTRACK_API_KEY"] = credentials.api_key

except ImportError:
    print("No \"config\" found.")
    
class OpenOutput(object):
    '''Custom action.'''

    label = 'Open Output'
    identifier = 'open.output.folder'
    #description = 'Open Shot Folder'
    #icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/73289-200.png'
    description = 'Launch Output'
    icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/937300-200.png'
    variant = 'Task Folder'

    def __init__(self, session):
        '''Initialise action.'''
        super(OpenOutput, self).__init__()
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
                'variant': self.variant
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

        msg = 'Opening shot folder'

        for entity in selection:

            entityId = entity['entityId']
            selType = entity['entityType']

            task = self.session.query('select custom_attributes from TypedContext where id is "{0}"'.format(entityId)).first()

            base_path = task['custom_attributes']['base_path']
            try:
                out_path = task['custom_attributes']['out_path']
            except KeyError:
                out_path = base_path
            '''
            try:
                work_path = task['custom_attributes']['path']
            except KeyError:
                work_path = out_path
            '''

            self.browse(out_path)
            
            out_path = r'{}'.format(out_path)

        return {
            'success': True,
            'message': 'Opening {0}'.format(out_path)
        }
        
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