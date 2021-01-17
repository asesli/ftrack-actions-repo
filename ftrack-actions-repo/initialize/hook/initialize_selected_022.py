'''
Initialize Selected Ftrack Hook
Alican Sesli - LUX VFX - 03.12.2019 - 02.11.2020
Creates files and folders baed on Ftrack Paths.
    v18: Rotoscoping tasks no longer creates work file/script. 
    v19: Retime scripts
    v20: Main project folders
    v22: Urls for comp
'''
import logging
import ftrack_api
import os,sys
import re
try:
    import ftrack
except:
    pass
import getpass
import time
import shutil


# setup ftrack environment
try:
    sys.path.insert(0,"L:/HAL/LIVEAPPS/apps/Scripts/FTRACK/ftrack_events/resources")
    import credentials

    os.environ["FTRACK_SERVER"]  = credentials.server_url
    os.environ["FTRACK_API_KEY"] = credentials.api_key

except ImportError:
    print("No \"config\" found.")




#this script will populate parameters of each task and shot nested under selected item with direct paths to file locations.
### prerequisites:
#Task should have the following attributes    : path, out_path, base_path
#Shot should have the following attributes    : plate_path #<---- no longer necesarry
#Project should have the following attributes : Project_Path  #<----naming will need to be conformed
### 

class Initialize(object):
    '''Custom action.'''

    label = 'Initialize'
    identifier = 'init.files.and.folders'
    description = 'Creates default folder structures and version 1 of work files for the selected hiearchy if they dont already exist.'
    icon = 'https://static.thenounproject.com/png/6067-200.png'
    variant = '3) Files and Folders'

    def __init__(self, session):
        '''Initialise action.'''
        super(Initialize, self).__init__()
        self.session = session
        #self.root_folder_template = 'L:/HAL/Alican/folders/MAIN_FOLDERS/'
        #self.root_folder_template = 'L:/HAL/Alican/folders/MAIN_FOLDERS_FTRACK/'
        self.root_folder_template = 'Q:/UnsortedProjects/projectfoldertemplates/MAIN_FOLDERS/'
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
    #make dir if it doesnt exist
    def makedir(self, directory):
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except:
                pass
        #print directory
    #Makes a list of all folders nested under source tree, and recreateas them  inside destination tree
    #used for creating default dept folders
    def createDirsFromExisting(self, source, destination):

        folders = [x[0] for x in os.walk(source) if '{' not in x[0]]
        '''
        _folders =  []

        for f in folders:
            _folders.append(f)

        folders = [i.replace("\\",'/') for i in _folders]
        '''
        folders = [i.replace("\\",'/') for i in folders]
        folders.sort(lambda x,y: cmp(x.count('/'), y.count('/') ) )
        folders.sort()
        for f in folders:
            src = f
            dst = f.replace(source, destination)
            #print src.ljust(70),'-->\t\t',dst
            try:
                #shutil.copytree(src, dst) #slower
                os.makedirs(dst)
            except:
                pass
    #Duplicates all files found in the source tree into destination tree while preserving hierarchies
    #used for copying default dept files
    def copyExistingFiles(self, source, destination):

        files = [(x[0], x[2]) for x in os.walk(source) if (len(x[2]) > 0) and ('{' not in x[0])]

        _files   =  []

        for f in files:
            for x in f[1]:
                file_path = os.path.join(f[0], x)
                _files.append(file_path)

        files = [i.replace("\\",'/') for i in _files]

        #files.sort(lambda x,y: cmp(x.count('/'), y.count('/') ) )
        files.sort()

        for f in files:
            src = f
            dst = f.replace(source, destination)
            #print src.ljust(70),'-->\t\t',dst
            try:
                if not os.path.isfile(dst) or self.overwrite:
                    shutil.copy(src, dst)
            except:
                pass


    def duplicate_nuke_file(self, source, destination):
        return 

    def launch(self, event):

        start_time = time.time()

        data = event['data']

        askOverwrite = {
            'items': [
                {
                    'value': '## Overwrite v001 files? ##',
                    'type': 'label'
                },{
                    'label': 'Overwrite files',
                    'name': 'overwrite',
                    'value': False,
                    'type': 'boolean'
                }
            ]
        }
        

        if 'values' in data:

            values = data['values']
            self.logger.info(u'Got values: {0}'.format(values))

            self.overwrite = values['overwrite']

            selection = data.get('selection', [])

            dept_folders = ['01_PLATES','02_INPUT','03_COORDINATION','04_3D','05_COMP','06_RENDERS','07_DAILIES','08_PFTrack','09_QT']

            folders = []
            files = []
            
            skipped_items = ''
            skipped_cnt = 0

            for entity in selection:

                entityId = entity['entityId']

                selType = entity['entityType']

                items = self.session.query('select custom_attributes, id, object_type.name, type.name, parent.name, parent.id, parent.custom_attributes, name from TypedContext where ancestors.id is "{0}" or project_id is "{0}" or descendants.id is "{0}"'.format(entityId)).all()

                sel = self.session.query('select custom_attributes, id, object_type.name, type.name, parent.name, parent.id, parent.custom_attributes, link, name from TypedContext where id is "{0}"'.format(entityId)).first()
                

                if sel == None:

                    sel = self.session.query('select custom_attributes, full_name from Project where id is "{0}"'.format(entityId)).first()

                    proj = sel

                else:

                    proj = self.session.query('select custom_attributes, full_name from Project where id is "{0}"'.format(sel['project_id'])).first()

                #episodes are found from Projet Looking downwards instead of finding it in the items iterator.
                #episodes = session.query('select name, id from Episode where ancestors.id is "{0}" or id is "{0}" or project_id is "{0}"'.format(proj['id'])).all()
                #episode_names = [e['name'] for e in episodes]
                #project_path = proj['custom_attributes']['Project_Path']
                #project_name = proj['full_name']

                #print 'Project:',proj
                #print 'Selected:', sel
                #print 'Nested:', items
                #print 'Episodes', episodes
                #print sel['custom_attributes']['base_path']

                if sel != proj:
                    #if we ad proj to the iterable, it will error out as proj has different parameters.
                    items.append(sel)

                items_length = len(items)

                #find an Episode object in selcted up or down stream of the tree
                episodes = [i['name'] for i in items if i['object_type']['name']=='Episode']

                proj_base_path = proj['custom_attributes']['base_path']
                proj_format = proj['custom_attributes']['resolution'][0]

                if episodes:
                    #create all dept folders in the episode base folder
                    for e in episodes:
                        episode_path = '{base_path}{episode_name}/'.format(base_path=proj_base_path,episode_name=e)
                        root_path = episode_path
                        #COPY PASTE 01-09_DEPT FOLDERS HERE
                        self.createDirsFromExisting(self.root_folder_template,root_path)

                        self.copyExistingFiles(self.root_folder_template,root_path)

                else : 
                    root_path = proj_base_path
                    #COPY PASTE 01-09_DEPT FOLDERS HERE
                    self.createDirsFromExisting(self.root_folder_template,root_path)

                    self.copyExistingFiles(self.root_folder_template,root_path)

                #All the Base folders have been duplicated from the template folder sturcture at this point.

                for i in items:


                    object_type = i['object_type']['name']

                    #We may need to change this... ftrack doesnt see default values from hiearchy attributes when its value is sourced from its parent..
                    #fix would be to create 'base_path' attributes for all object types. 
                    #Update paths function already looks at each item 1 by 1 anyways
                    base_path = i['custom_attributes']['base_path']
                    if '/' not in base_path:
                        skipped_cnt+=1
                        msg = '{0}:{1}:{2} <- check base_path<br>'.format( object_type,i['name'],i['parent']['name'],i['custom_attributes']['base_path'] )
                        skipped_items+=msg

                        #print object_type, i['name'], i['custom_attributes']['base_path'],i['parent']['name'], '<-- base_path error; update paths'
                        continue


                    #if object_type == 'Project':


                    if object_type == 'Shot':
                        #Shot speicific folders
                        #plates
                        shot_name = i['name']
                        plate_path = '{base_path}01_PLATES/{shot_name}/'.format(base_path=base_path,shot_name=shot_name)

                        folders.append(plate_path)

                        pass

                    if object_type == 'Task':

                        shot_name  = i['parent']['name'] #this may break when it comes to asset builds since they are not nested under a shot..
                        task_type  = i['type']['name']
                        task_name  = i['name']
                        ftrack_id  = i['id']
                        ftrack_parent_id = i['parent']['id']
                        ftrack_url = 'https://lux-visual-effects.ftrackapp.com/#slideEntityId={ftrack_id}&slideEntityType=task&itemId=home'.format(ftrack_id=ftrack_id)
                        ftrack_proj_view_url = 'https://lux-visual-effects.ftrackapp.com/#entityId={ftrack_id}&entityType=task&itemId=projects&view=tasks'.format(ftrack_id=ftrack_parent_id)


                        #shot_fps            = float(i['parent']['custom_attributes']['fps'])
                        shot_fps            = i['parent']['custom_attributes']['fps']
                        if shot_fps != None:    shot_fps=float(shot_fps)
                        else:   shot_fps=float(24)

                        shot_timecode       = i['parent']['custom_attributes']['Timecode']
                        if shot_timecode != None:    shot_timecode=str(shot_timecode)
                        else:   shot_timecode=str('00:00:00:00')
                        #shot_duration       = int(i['parent']['custom_attributes']['duration'])
                        '''
                        handles             = i['parent']['custom_attributes']['handles']
                        if handles != None:    handles=int(handles)
                        else:   handles=0
                        '''
                        shot_first_frame    = i['parent']['custom_attributes']['first_frame']
                        if shot_first_frame != None:    shot_first_frame=int(shot_first_frame)
                        else:   shot_first_frame=1


                        shot_last_frame     = i['parent']['custom_attributes']['last_frame']
                        if shot_last_frame != None:    shot_last_frame=int(shot_last_frame)
                        else:   shot_last_frame=100

                        shot_plates_path    = '{base_path}01_PLATES/{shot_name}/'.format(base_path=base_path,shot_name=shot_name)


                        if task_type in ['Compositing', 'Precomp', 'Cleanplate', 'Retime', 'Paintout']:

                            #2D/COMP Dept Paths
                            comp_dirs = [
                                '{base_path}05_COMP/{shot_name}/',
                                '{base_path}05_COMP/{shot_name}/01_DATA/',
                                '{base_path}05_COMP/{shot_name}/01_DATA/camera/',
                                '{base_path}05_COMP/{shot_name}/01_DATA/obj/',
                                '{base_path}05_COMP/{shot_name}/02_OUTPUT/',
                                '{base_path}05_COMP/{shot_name}/02_OUTPUT/01_precomp/',
                                '{base_path}05_COMP/{shot_name}/02_OUTPUT/02_mattes/',
                                '{base_path}05_COMP/{shot_name}/02_OUTPUT/03_comp/'
                                ]

                            comp_dirs = [d.format(base_path=base_path, shot_name=shot_name) for d in comp_dirs]
                            #print comp_dirs
                            comp_base = comp_dirs[0] 



                            comp_out_dir = '02_OUTPUT/03_comp/{shot_name}_V001/'.format(shot_name=shot_name) 
                            work_file = '{comp_base}{shot_name}_Comp_v001.nk'.format(comp_base=comp_base,shot_name=shot_name)
                            comp_template = "X:/apps/Scripts/FTRACK/nuke_templates/basic_comp_template.nk"

                            if (task_type.lower() == 'retime'):

                                work_file = '{comp_base}{shot_name}_{task_name}_v001.nk'.format(comp_base=comp_base,shot_name=shot_name,task_name=task_name)
                                comp_template = "X:/apps/Scripts/FTRACK/nuke_templates/basic_retime_template.nk"

                            if ((task_type.lower() != task_name.lower()) and task_type.lower() == 'compositing') or (task_type.lower() != 'compositing') and (task_type.lower() != 'retime'):

                                comp_out_dir = '02_OUTPUT/01_precomp/{task_name}/{task_name}_V001/'.format(task_name=task_name)

                                #init precomp nk file 
                                work_file = '{comp_base}{shot_name}_{task_name}_v001.nk'.format(comp_base=comp_base,shot_name=shot_name,task_name=task_name)
                                comp_template = "X:/apps/Scripts/FTRACK/nuke_templates/basic_precomp_template.nk"


                            #files.append([comp_template,work_file])
                            #nuke_dict = { 'template':comp_template, 'newfile':work_file, 'first_frame':1, 'last_frame':100, 'fps':25.0, 'duration':100, 'timecode': '00:00:00:00' }

                            nuke_dict = {'ftrack_proj_view_url':ftrack_proj_view_url, 'ftrack_parent_id':ftrack_parent_id, 'ftrack_id':ftrack_id, 'ftrack_url':ftrack_url, 'template':comp_template, 'newfile':work_file, 'first_frame':shot_first_frame, 'last_frame':shot_last_frame, 'fps':shot_fps, 'format':'"'+proj_format+'"', 'timecode': shot_timecode, 'plate_path':shot_plates_path, 'shot_name':shot_name, 'task_name':task_name }
                            
                            files.append( nuke_dict )

                            comp_dir = '{comp_base}{comp_out_dir}'.format(comp_base=comp_base,comp_out_dir=comp_out_dir)

                            comp_dirs.append(comp_dir)

                            folders += comp_dirs





                        if task_type in ['Tracking', 'Lighting', 'Animation', 'Layout', 'FX', 'Matchmove']:
                            #3D/General Dept Paths
                            cg_dirs = [
                                '{base_path}04_3D/images/{shot_name}/',
                                '{base_path}04_3D/objects/{shot_name}/',
                                '{base_path}04_3D/scenes/{shot_name}/',
                                '{base_path}04_3D/scenes/{shot_name}/anim/',
                                '{base_path}04_3D/scenes/{shot_name}/lighting/',
                                '{base_path}04_3D/scenes/{shot_name}/tracking/',
                                '{base_path}06_RENDERS/{shot_name}/',
                                '{base_path}06_RENDERS/{shot_name}/ANIM/',
                                '{base_path}06_RENDERS/{shot_name}/FINL/',
                                '{base_path}06_RENDERS/{shot_name}/TRAC/'
                                ]
                            
                            cg_dirs = [d.format(base_path=base_path, shot_name=shot_name) for d in cg_dirs]

                            folders += cg_dirs


                            if task_type == 'FX':

                                task_dirs = [
                                    '{base_path}04_3D/scenes/{shot_name}/fx/',
                                    '{base_path}06_RENDERS/{shot_name}/FX/'
                                    ]

                                task_dirs = [d.format(base_path=base_path, shot_name=shot_name) for d in task_dirs]

                                folders += task_dirs


            #create the folders

            folders = list(set(folders))
            #folders.sort(lambda x,y: cmp(x.count('/'), y.count('/') ) )
            folders.sort()

            for folder in folders:

                #print folder
                self.makedir(folder)

            '''
            for file in files:

                #print file
                try:
                    if not os.path.isfile(file[1]):
                        shutil.copy(file[0], file[1])
                except:
                    pass
            '''
            file_cnt = 0
            for file in files:
                #print file

                #try:
                if not os.path.isfile(file['newfile']) or self.overwrite:
                    file_cnt+=1


                    shutil.copy(file['template'], file['newfile'])

                    with open(file['newfile'], 'r+') as content_file:
                        content = content_file.read()
                        #print content
                        #{ 'template':comp_template, 'newfile':work_file, 'first_frame':shot_first_frame, 'last_frame':shot_last_frame, 'fps':shot_fps, 'timecode': shot_timecode, 'plate_path':shot_plates_path }
                        content = content.replace('<timecode>', str(file['timecode']))
                        content = content.replace('<first_frame>', str(file['first_frame']))
                        content = content.replace('<last_frame>', str(file['last_frame']))
                        content = content.replace('<fps>', str(file['fps']))
                        content = content.replace('<format>', str(file['format']))
                        content = content.replace('<ftrack_url>', str(file['ftrack_url']))
                        content = content.replace('<ftrack_id>', str(file['ftrack_id']))
                        content = content.replace('<ftrack_parent_id>', str(file['ftrack_parent_id']))
                        content = content.replace('<ftrack_proj_view_url>', str(file['ftrack_proj_view_url']))
                        
                        #content = content.replace('<onScriptLoad>', '"'+"import importPlates;importPlates.importPlates('"+file['plate_path']+"')"+'"')
                        if file['task_name'] == 'Retime':
                            content = content.replace('<onScriptLoad>', '"'+"import importAssets;importAssets.ImportAssets().initRetimeScript()"+'"')
                        else:
                            content = content.replace('<onScriptLoad>', '"'+"import importAssets;importAssets.ImportAssets().initScript()"+'"')

                        content = content.replace('<onScriptSave>', "nuke.Root()['onScriptLoad'].setValue('');nuke.Root()['onScriptSave'].setValue('')")

                        content_file.seek(0)
                        content_file.write(content)
                        content_file.truncate()
                        #print content
                    #except:
                    #    pass
                    #duplicate template file into the new file
                    #change the entries to the ones in the dict
                    #

            folder_cnt = len(folders)
            #file_cnt = len(files)

            #print("--- %s items ---" % (folder_cnt)) 
            #print("--- %s seconds ---" % (time.time() - start_time)) 

            return {
                'success': True,
                'message': 'Creating {0} directories <br> Creating {1} initial files <br> Also skipped {2} items below<br> {3}'.format(folder_cnt, file_cnt, skipped_cnt, skipped_items)
            }

        return askOverwrite    
            
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