'''
Alican Sesli - LUX VFX - 29.11.2019
Latest Shot Note to All Tasks
v7 : task note is now unicode
'''

import logging
import ftrack_api
import os
import getpass
try:
    import ftrack
except:
    pass
import urllib2

# setup ftrack environment
try:
    sys.path.insert(0,"L:/HAL/LIVEAPPS/apps/Scripts/FTRACK/ftrack_events/resources")
    import credentials

    os.environ["FTRACK_SERVER"]  = credentials.server_url
    os.environ["FTRACK_API_KEY"] = credentials.api_key

except ImportError:
    print("No \"config\" found.")

    
class TaskNote(object):

    label = 'Task Note'
    identifier = 'task.note.from.latest.shot.note'
    description = 'Takes the latest shot note and makes it a task note.'
    icon = 'https://static.thenounproject.com/png/177437-200.png'
    variant = 'From Latest Shot Note'
    def __init__(self, session):
        '''Initialise action.'''
        super(TaskNote, self).__init__()
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

        session = ftrack_api.Session()

        for entity in selection:

            item = session.query('select id, name, notes, object_type.name from TypedContext where id is {1} and object_type.name in {0}'.format(("Task","Shot"), entity['entityId'])).first()

            if item['object_type']['name'] == 'Task':
                tasks = [item]
                shot = [i for i in item['ancestors'] if i['object_type']['name'] == 'Shot'][0]

            if item['object_type']['name'] == 'Shot':
                shot = item
                tasks = [i for i in item['children'] if (i['object_type']['name'] == 'Task')]

            #print shot # single
            #print tasks # list

            notes_on_shot = shot['notes']

            '''
            #diagnose
            for n in notes_on_shot:
                print n
                print n['date'].timestamp
                print n['content']
                print n['author']
            '''

            note_list = []
            
            [note_list.append({'date':i['date'].timestamp, 'content':i['content'], 'author':i['author'], 'note_components':i['note_components']}) for i in notes_on_shot]
            note_list = sorted(note_list, key=lambda k: int(k['date']),reverse=True) 
            if not len(note_list):
                return {
                    'success': False,
                    'message': 'No notes exist at the Shot level.'
                }
            notes_on_shot = note_list[0]

            latest_note_on_shot = notes_on_shot['content']
            latest_note_on_shot = latest_note_on_shot.encode('utf-8')
            note_author = notes_on_shot['author']
            author = session.query('User where username is "{}"'.format(getpass.getuser())).first()

            server_location = session.query('Location where name is "ftrack.server"').one()
            components = []
            for note_component in notes_on_shot['note_components']:
                url = server_location.get_url(note_component['component'])
                #print 'Download URL: {0}'.format(url)
                file = urllib2.urlopen(url)
                with open('temp.jpg','wb') as output:
                  output.write(file.read())
                url = 'temp.jpg'
                component = session.create_component(url, data={'name': 'Myfile'}, location=server_location)
                components.append(component)

            note = u"Latest note on {shot} from {user}: \n\n {note} ".format(user=note_author['first_name'], note=latest_note_on_shot, shot=shot['name'])

            for task in tasks:
                task_note = session.create('Note', {'content': note,'author': author})
                for c in components:
                    session.create('NoteComponent',{'component_id': c['id'], 'note_id': task_note['id']})
                task['notes'].append(task_note)
                #task['notes'].append(task_note_component)


        session.commit()

        retSuccess = {
            'success': True,
            'message': 'Latest shot note has been added as a task note'
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

    action = TaskNote(session)
    action.register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()