'''
Update Paths Ftrack Hook
Alican Sesli - LUX VFX - 03.12.2019
Updates the path parameters on ftrack based on task/shot/item hiearchy
    v14: House Cleaning (comments)
    v15: as job
'''

import logging
import ftrack_api
import os,sys
import re
import ftrack
import getpass
import time

# setup environment
try:
    sys.path.insert(0,"L:/HAL/LIVEAPPS/apps/Scripts/FTRACK/ftrack_events/resources")
    import credentials

    os.environ["FTRACK_SERVER"] = credentials.server_url
    os.environ["FTRACK_API_KEY"] = credentials.api_key

except ImportError:
    print("No \"config\" found.")

#this script will populate parameters of each task and shot nested under selected item with direct paths to file locations.
### prerequisites:
#Task should have the following attributes    : path, out_path, base_path
#Shot should have the following attributes    : plate_path
#Project should have the following attributes : Project_Path  #<----naming will need to be conformed
### 

class Initialize(object):
    '''Custom action.'''

    label = 'Initialize'
    identifier = 'init.task.paths'
    description = 'This updates the path parameter of all tasks nested under selected'
    #icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/1406969-200.png'
    icon = 'https://static.thenounproject.com/png/6067-200.png'
    variant = '1) Paths'

    def __init__(self, session):
        '''Initialise action.'''
        super(Initialize, self).__init__()
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
        admin_roles = ['API', 'Administrator', 'Project Manager']
        user_id = event['source']['user']['id']
        user =  self.session.query('User where id is "{0}"'.format(user_id)).one()
        user_roles = [str(i['security_role']['name']) for i in user['user_security_roles']]
        if not bool(set(user_roles).intersection(admin_roles)):
            return False

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

        start_time = time.time()

        data = event['data']

        userId = event['source']['user']['id']

        selection = data.get('selection', [])

        job = ftrack.createJob(
                description='Updating Paths',
                status='running',
                user=userId
            )

        try:
            
            total = 0
            sel_count = 0
            update = False

            for entity in selection:

                sel_count += 1

                entityId = entity['entityId']
                selType = entity['entityType']

                if selType in ['Slates']:
                    continue

                
                items = self.session.query('select custom_attributes, object_type.name, type.name, parent.name, link, name from TypedContext where ancestors.id is "{0}" or project_id is "{0}"'.format(entityId)).all()

                sel = self.session.query('select custom_attributes, object_type.name, type.name, parent.name, link, name from TypedContext where id is "{0}"'.format(entityId)).first()

                if sel == None:

                    sel = self.session.query('select custom_attributes, full_name from Project where id is "{0}"'.format(entityId)).first()
                    proj = sel

                else:
                    proj = self.session.query('select custom_attributes, full_name from Project where id is "{0}"'.format(sel['project_id'])).first()

                #episodes are found from Projet Looking downwards instead of finding it in the items iterator.

                episodes = self.session.query('select name from Episode where project_id is "{0}"'.format(proj['id'])).all()

                episode_names = [e['name'] for e in episodes]

                project_path = proj['custom_attributes']['Project_Path']
                project_name = proj['full_name']

                #print 'Project:',proj
                #print 'Selected:', sel
                #print 'Nested:', items
                #print 'Episodes:', episodes

                if sel == proj:

                    base_path = '{project_path}{project_name}/'.format(project_path=project_path, project_name=project_name)

                    if proj['custom_attributes']['base_path'] != base_path:
                        proj['custom_attributes']['base_path'] = base_path
                        update = True

                else:

                    items.append(sel)

                items_length = len(items)

                item_count = 0

                for i in items:

                    item_count += 1
                    total += 1

                    if len(selection) > 1:
                        job.setDescription('Updated {}/{} paths from selection {}/{}'.format(item_count, items_length, sel_count, len(selection)))

                    else:
                        job.setDescription('Updated {}/{} paths'.format(item_count, items_length)) 

                    episode = ''

                    if i['object_type']['name'] == 'Episode':

                        episode = i['name']

                    else:

                        episode = [ x['name'] for x in i['ancestors'] if x['name'] in episode_names ]

                        if len(episode)>0: 

                            episode = episode[0]

                        else:

                            episode = ''

                    base_path = '{project_path}{project_name}/{episode}/'.format(project_path=project_path, project_name=project_name, episode=episode).replace('//','/')

                    if i['custom_attributes']['base_path'] != base_path:
                        i['custom_attributes']['base_path'] = base_path
                        update = True


                    if i['object_type']['name'] == 'Sequence':
                        base_cis = '{base_path}09_QT/EDITORIAL/_base_cis/'.format(base_path=base_path)
                        if i['custom_attributes']['base_cis'] != base_cis:
                            i['custom_attributes']['base_cis'] = base_cis
                            update = True
                            

                        base_edl = '{base_path}09_QT/EDITORIAL/EDL/'.format(base_path=base_path)
                        if i['custom_attributes']['base_edl'] != base_edl:
                            i['custom_attributes']['base_edl'] = base_edl
                            update = True

                    if i['object_type']['name'] == 'Task':

                        shot_name = i['parent']['name'] #this may break when it comes to asset builds since they are not nested under a shot..
                        task_type = i['type']['name']
                        task_name = i['name']

                        path = ''#base_path
                        out_path = ''#base_path

                        if task_type.lower() in ['compositing', 'precomp', 'cleanplate', 'retime', 'rotoscoping', 'paintout']:

                            comp_out_dir = '02_OUTPUT/03_comp'

                            if task_type.lower() != task_name.lower():
                                comp_out_dir = '02_OUTPUT/01_precomp/{task_name}'.format(task_name=task_name)
                            
                            path     = '{base_path}{dept_name}/{shot_name}/'.format(base_path=base_path,shot_name=shot_name,dept_name='05_COMP')
                            out_path = '{base_path}{dept_name}/{shot_name}/{comp_out_dir}/'.format(base_path=base_path,shot_name=shot_name,dept_name='05_COMP',comp_out_dir=comp_out_dir)

                        if task_type.lower() in ['matchmove', 'tracking']:

                            path = '{base_path}{dept_name}/scenes/{shot_name}/tracking/'.format(base_path=base_path,shot_name=shot_name,dept_name='04_3D')
                            out_path = '{base_path}{dept_name}/{shot_name}/TRAC/'.format(base_path=base_path,shot_name=shot_name,dept_name='06_RENDERS')

                        if task_type.lower() in ['animation']:

                            path = '{base_path}{dept_name}/scenes/{shot_name}/anim/'.format(base_path=base_path,shot_name=shot_name,dept_name='04_3D')
                            out_path = '{base_path}{dept_name}/{shot_name}/ANIM/'.format(base_path=base_path,shot_name=shot_name,dept_name='06_RENDERS')

                        if task_type.lower() in ['layout']:

                            path = '{base_path}{dept_name}/scenes/{shot_name}/layout/'.format(base_path=base_path,shot_name=shot_name,dept_name='04_3D')
                            out_path = '{base_path}{dept_name}/{shot_name}/LYT/'.format(base_path=base_path,shot_name=shot_name,dept_name='06_RENDERS')

                        if task_type.lower() in ['lighting']:

                            path = '{base_path}{dept_name}/scenes/{shot_name}/lighting/'.format(base_path=base_path,shot_name=shot_name,dept_name='04_3D')
                            out_path = '{base_path}{dept_name}/{shot_name}/FINL/'.format(base_path=base_path,shot_name=shot_name,dept_name='06_RENDERS')

                        if task_type.lower() in ['fx']:

                            path = '{base_path}{dept_name}/scenes/{shot_name}/fx/'.format(base_path=base_path,shot_name=shot_name,dept_name='04_3D')
                            out_path = '{base_path}{dept_name}/{shot_name}/FX/'.format(base_path=base_path,shot_name=shot_name,dept_name='06_RENDERS')

                        path = path.replace('//', '/')
                        out_path = out_path.replace('//', '/')

                        if i['custom_attributes']['path']!= path: #only make changes if they dont already exist
                            i['custom_attributes']['path'] = path
                            update = True

                        if i['custom_attributes']['out_path'] != out_path: #only make changes if they dont already exist
                            i['custom_attributes']['out_path'] = out_path
                            update = True


                    #We could expand this so it browses the directorty for the most applicable plate... for now, run it at plate level, and let get_version choose _O vs _R
                    if i['object_type']['name'] == 'Shot':
                        shot_name = i['name']
                        #print shot_name
                        out_path = '{base_path}01_PLATES/{shot_name}/PLATE/'.format(base_path=base_path, shot_name=shot_name)
                        #plate_path = out_path

                        #plate_path = plate_path.replace('//', '/')
                        out_path = out_path.replace('//', '/')

                        #print out_path
                        #print
                        '''
                        if i['custom_attributes']['plate_path']!= plate_path: #only make changes if they dont already exist
                            i['custom_attributes']['plate_path'] = plate_path
                            update = True
                        '''
                        if i['custom_attributes']['out_path'] != out_path: #only make changes if they dont already exist
                            i['custom_attributes']['out_path'] = out_path
                            update = True


            if update:
                self.session.commit()


            job.setStatus('done')
            job.setDescription('Updated {} paths'.format(total)) 

        except Exception as e:
            job.setStatus('failed')
            
            job.setDescription('Error : {}'.format( e )) 


        #print("--- %s seconds ---" % (time.time() - start_time)) 

        return {
            'success': True,
            'message': 'Updating Ftrack links for {0} items nested under selected hierarchy!'.format(total)
        }
        
def register(session, **kw):
    '''Register plugin.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    action = Initialize(session)
    action.register()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()