'''
Alican Sesli - LUX VFX - 29.11.2019
Latest Task Note to All Tasks
v6 : task note is now unicode
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
    identifier = 'task.note.to.all.other.tasks'
    description = 'Takes the latest task note and puts it on all sister tasks'
    icon = 'https://static.thenounproject.com/png/177437-200.png'
    variant = 'To All Other Tasks'

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

        data = event['data']

        selection = data.get('selection', [])

        session = ftrack_api.Session()

        for entity in selection:

            task = session.query('select name from {0} where id is {1}'.format('Task', entity['entityId'])).first()
            #print 'task', task
            if not task:
                retFail = {
                    'success': False,
                    'message': 'Run this action on a Task type item'
                }
                return retFail
            shot = [i for i in task['ancestors'] if i['object_type']['name'] == 'Shot'][0]
            #print 'shot', shot
            sister_tasks = [i for i in shot['children'] if (i['object_type']['name'] == 'Task') and (i['id']!=entity['entityId'])]
            #print 'sister_tasks', [i['name'] for i in sister_tasks]

            notes_on_task = task['notes']

            note_list = []
            [note_list.append({'date':i['date'].timestamp, 'content':i['content'], 'author':i['author'], 'note_components':i['note_components']}) for i in notes_on_task]
            if not len(note_list):
                return {
                    'success': False,
                    'message': 'No notes exist for this Task.'
                }

            note_list = sorted(note_list, key=lambda k: int(k['date']),reverse=True) 
            notes_on_task = note_list[0]

            latest_note_on_task = notes_on_task['content']
            latest_note_on_task = latest_note_on_task.encode('utf-8')
            note_author = notes_on_task['author']
            author = session.query('User where username is "{}"'.format(getpass.getuser())).first()

            server_location = session.query('Location where name is "ftrack.server"').one()
            components = []
            for note_component in notes_on_task['note_components']:
                url = server_location.get_url(note_component['component'])
                #print 'Download URL: {0}'.format(url)
                file = urllib2.urlopen(url)
                with open('temp.jpg','wb') as output:
                  output.write(file.read())
                url = 'temp.jpg'
                component = session.create_component(url, data={'name': 'Myfile'}, location=server_location)
                components.append(component)

                
            note = u"{user}'s note from {task}: \n\n {note}".format(user=note_author['first_name'], task=task['name'], note=latest_note_on_task)
            
            for task in sister_tasks:
                task_note = session.create('Note', {
                    'content': note,
                    'author': author
                })
                for c in components:
                    session.create('NoteComponent',{'component_id': c['id'], 'note_id': task_note['id']})
                task['notes'].append(task_note)

        session.commit()
        
        retSuccess = {
            'success': True,
            'message': 'Latest task note has been added to all other tasks!'
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