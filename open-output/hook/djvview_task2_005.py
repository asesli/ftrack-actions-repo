import logging
import ftrack_api
import os
import glob
try:
    import ftrack
except ImportError:
    pass
import getpass
import sys
import subprocess



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

    label = 'Open Latest'
    identifier = 'open.output.latest.version.2'
    #description = 'Launch Shot/Task in DJV_View'
    #icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/937300-200.png'

    description = 'Launch Output'
    icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/937300-200.png'

    variant = 'Latest Version'

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

        #Check to see if the user trying to run this action belongs in the admin_roles
        admin_roles = ['API', 'Administrator', 'Project Manager']
        for_users = ['luxryan','alicans','matthiasl']
        user_id = event['source']['user']['id']
        user =  self.session.query('select username from User where id is "{0}"'.format(user_id)).one()
        
        if not bool([i for i in for_users if i == user['username']]):
            return False

        '''
        user_roles = [str(i['security_role']['name']) for i in user['user_security_roles']]
        if not bool(set(user_roles).intersection(admin_roles)):
            return False
        '''

        #user_roles = [str(i['security_role']['name']) for i in user['user_security_roles']]

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

    def get_latest_version_of_task(self, ftrack_task):

        sel = ftrack_task

        out_path= sel['custom_attributes']['out_path']#this taks output

        task_name = sel['name']#name of task #Compositing/CleanPlateSLGuy/Animation
        shot_code = sel['parent']['name']#better hope the task is parented under a shot
        obj_type_name = sel['object_type']['name']#Task
        typ_name = sel['type']['name']#Compositing/Animation/Tracking

        _image_asset = None #'Q:/TEST20/TES101/05_COMP/TES101_100_010/02_OUTPUT/01_precomp/Paintout_Head/Paintout_Head_V006/Paintout_Head_V006.0064.jpeg'

        image_types = ['jpeg', 'jpg', 'exr', 'dpx', 'tiff', 'tif', 'png', 'tga']


        if typ_name.lower() in ['compositing','precomp','cleanplate']:

            if typ_name != task_name:#this is a precomp task

                #print 'precomp'
                if os.path.isdir(out_path):
                    assets = [out_path+i+'/' for i in os.listdir(out_path) if task_name in i]
                    assets.sort()
                    assets.reverse()
                    for asset in assets:

                        files = [f for f in os.listdir(asset) if (f.split('.')[-1].lower() in image_types) and (task_name in f)]
                        if files:
                            files.sort()
                            files.reverse()
                            image = files[0] #<---by theaory, it should first return a jpeg, if that doesnt exist than a dpx, and then an exr... tadaaa 
                            _image_asset = asset + image
                            return _image_asset
                            break
                else:
                    return None

            else:#regular ol comp
                #print 'comp'
                if os.path.isdir(out_path):
                    assets = [out_path+i+'/' for i in os.listdir(out_path) if shot_code in i]
                    assets.sort()
                    assets.reverse()

                    for asset in assets:
                        #find an applicable jpeg to view, if it doesnt exist than find a dpx or an exr
                        
                        img_type_folders = [asset+i+'/' for i in os.listdir(asset) if i.lower() in image_types]
                        img_type_folders.sort()
                        img_type_folders.reverse()

                        #print img_type_folders
                        for img_folder in img_type_folders:
                            files = [ f for f in os.listdir(img_folder) if (f.split('.')[-1].lower() in image_types) and (shot_code in f) ]
                            if files:
                                files.sort()
                                files.reverse()
                                image = files[0] #<---by theaory, it should first return a jpeg, if that doesnt exist than a dpx, and then an exr... tadaaa 

                                _image_asset = img_folder + image
                                return _image_asset
                                break
                else:
                    return None

                        
        else:
            #print '3d task'

            if os.path.isdir(out_path):
                assets = [out_path+i+'/' for i in os.listdir(out_path)]
                assets.sort()
                assets.reverse()
                #print assets
                for asset in assets:
                    files = [ f for f in os.listdir(asset) if (f.split('.')[-1].lower() in image_types) and (shot_code in f) ]

                    
                    if files:
                        files.sort()
                        files.reverse()
                        image = files[0] #<---by theaory, it should first return a jpeg, if that doesnt exist than a dpx, and then an exr... tadaaa 
                        _image_asset = asset + image
                        return _image_asset
                        break
            else:
                return None

        #print image_asset
        #return _image_asset

    def launch(self, event):


        data = event['data']

        selection = data.get('selection', [])


        msg = 'Opening shot in DJ View'

        for entity in selection:

            entityId = entity['entityId']
            selType = entity['entityType']

            #shots = self.session.query('select custom_attributes, object_type.name, project_id, type.name, parent.name, name from Shot where children.id is "{0}" or ancestors.id is "{0}" or project_id is "{0}" or id is "{0}"'.format(entityId)).all()

            task = self.session.query('select custom_attributes, object_type.name, type.name, parent.name, name from Task where id is "{0}"'.format(entityId)).first()


            if not task:#detect shot
                #return early
                tasks = self.session.query('select custom_attributes, object_type.name, type.name, parent.name, name from Task where parent.id is "{0}"'.format(entityId)).all()
                if tasks:
                    #force this order if the Shot item is selected.. so taht it always choses comp first, then if nothing exists look at anim & so forth
                    #tasks = [comp, anim, mtcm, trac, lyot]
                    _tasks = [None, None, None, None, None]
                    for i in tasks:

                        if (i['name'].lower() == 'compositing') and (i['type']['name'] == i['name']):
                            _tasks[0] = i

                        elif (i['name'].lower() == 'animation'):
                            _tasks[1] = i

                        elif (i['name'].lower() == 'matchmove'):
                            _tasks[2] = i

                        elif (i['name'].lower() == 'tracking'):
                            _tasks[3] = i

                        elif (i['name'].lower() == 'layout'):
                            _tasks[4] = i

                        else:
                            _tasks.append(i)

                    image_asset = None

                    try:
                        num = 0
                        while image_asset == None:

                            image_asset = self.get_latest_version_of_task( _tasks[num] )

                            num+=1

                    except IndexError:
                        return {
                            'success': False,
                            'message': 'Couldnt find any outputs for this shot.<br>Try launching from a Task..'
                        }
                else:

                    return {
                        'success': False,
                        'message': 'Run this Action from Shot or Task level.'
                    }
                #print image_asset

                #return {'success':True}

                '''
                return {
                    'success': False,
                    'message': 'Run this action on a Task.<br> Make sure "out_path" parameter of the Task is populated.'
                }
                '''

            else:#Else it IS a task..
                out_path = task['custom_attributes']['out_path']
                if out_path in ['', None]:
                    #return early
                    return {
                        'success': False,
                        'message': 'Populate "out_path" parameter for this task.'
                    }

                elif not os.path.isdir(out_path):
                    #return early
                    return {
                        'success': False,
                        'message': 'Couldnt find the "out_path" directory. <br>out_path : {0}'.format(out_path)
                    }

                else:
                    image_asset = self.get_latest_version_of_task(task)




            
            if image_asset:

                #print image_asset
                #exe = 'C:/djv/bin/djv_view.exe'
                exe = '"C:/Program Files/djv-1.1.0-Windows-64/bin/djv_view.exe"'
                exe = "\\\\qumulo\\LiveApps\\apps\\djv_view.lnk"
                #exe = u"//qumulo/LiveApps/apps/djv_view.lnk"
                exe = '"\\\\qumulo\\LiveApps\\apps\\DJV\\DJV-1.3.0-win64\\bin\\djv_view.exe"'
                #exe = exe.replace('\\','/')

                '''
                files = []
                path = '\\\\qumulo\\LiveApps\\apps\\DJV\\'
                for p, d, f in os.walk(path):
                    [files.append(os.path.join(p,file).replace(os.sep, '/')) for file in f if file.split('.')[-1] == 'exe']
                print files
                '''
                if not os.path.isfile(exe.replace('"', '')):
                    #return early
                    return {
                        'success': False,
                        'message': 'Couldnt find DJ_View <br>exe : {0}'.format(exe)
                    }




                #print os.readlink(exe)

                '''
                import win32com.client
                #print(win32com.__file__)
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(exe)
                #print(shortcut.Targetpath)
                exe = shortcut.Targetpath
                '''


                file = image_asset.replace('/', '\\')
                args = exe + ' ' + file
                subprocess.Popen(args, shell=False)
                #subprocess.Popen(exe, shell=False)
                #os.system(args)
                #os.startfile (exe)



            else:
                
                self.browse(out_path)

                return {
                    'success': False,
                    'message': 'Couldnt locate your renders, opening the "out_path" directory instead!!!'
                }

        return {
            'success': True,
            'message': 'Opening {0} <br> with {1}'.format(image_asset,exe)
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