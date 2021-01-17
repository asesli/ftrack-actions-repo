'''
Update Shot Parametes Ftrack Hook
Alican Sesli - LUX VFX - 03.12.2019
Updates the shot parameters
    v7: House Cleaning (comments)
    v8: plate_combined --> plate_c
    v9: wont update frame range if lock_frame_range
'''

import logging
import ftrack_api
import os
import re
try:
    import ftrack
except:
    pass
import getpass
import time
import sys

sys.path.append("X:/apps/Scripts/FTRACK/python-lib/lib")
sys.path.append("X:/apps/Scripts/FTRACK/python-lib/lib/site-packages")
sys.path.append("X:/apps/Scripts/FTRACK/ftrack_hooks/update_shot_params_hook/hook")
sys.path.append("X:/apps/Scripts/FTRACK/ftrack_hooks/initialize_hook/hook")

from timecode_convert import TC_Op

from bs4 import BeautifulSoup

'''

import os
import sys

RESOURCE_DIRECTORY = os.path.abspath(
    #os.path.join(os.path.dirname(__file__), '..', 'resource', 'modules')

)

if RESOURCE_DIRECTORY not in sys.path:
    sys.path.append(RESOURCE_DIRECTORY)

import my_module

'''


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
#Shot should have the following attributes    : plate_path
#Project should have the following attributes : Project_Path  #<----naming will need to be conformed
### 

class Initialize(object):
    '''Custom action.'''

    label = 'Initialize'
    identifier = 'init.shot.params'
    description = 'This updates shot Start/End frames, duration, and frame rate on FTrack'
    #icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/45456-200.png'
    icon = 'https://static.thenounproject.com/png/6067-200.png'
    variant = '2) Shot Parameters'

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


    def extract_data_from_EDLs(self, edl_folder):
        #edl_folder = "Q:/TEMP_PROJECT/09_QT/EDITORIAL/EDL/"
        
        files = [edl_folder+i for i in os.listdir(edl_folder) if '.xml' in i.lower()]
        files = sorted(files)
        shot_items = {}


        #print files

        for file in files:
            
            try:

                with open(file, 'r') as f:

                    read_data = f.read()
                    edl = BeautifulSoup(read_data, "xml")
                    clipitems =  edl.find_all('file')
                    shotids = [i.get('id') for i in clipitems]

                    for sid in shotids:
                        clips = edl.find(id=sid)
                        shotid = sid
                        duration = int(clips.duration.text)#Shot duration including the handles
                        framerate = clips.rate.timebase.text
                        start = int(clips.parent.start.text)#Start frame after head handle in the entire cut
                        end = int(clips.parent.end.text)#End frame before tail handle in the entire cut
                        handles = int((duration-(end-start))) #/ 2
                        timecode = int(clips.timecode.frame.text)###this returns the timecode frame and not the timecode string as string is a python obj type... so it gets confused.
                        #timecode = convertToTimecode(timecode)???
                        #print timecode

                        shot_items[shotid] ={'shotid':shotid, 'duration':duration, 'framerate':framerate, 'handles':handles, 'timecode':timecode}#, 'first_frame':start, 'flast_frame':end}

            except IOError:

                pass
                #print 'IOError: {0}'.format(file)


        return shot_items

    def getPlates(self, _path):

        #base_path = "Q:/EPISODIC/EPS101/"
        #plates_path = "01_PLATES/EPS101_001_020/"
        #path = base_path+plates_path
        #path = "Q:/William/01_PLATES/WIL_043_010/"
        #path = path
        plate_items = {}
        image_types = ['exr', 'jpeg', 'jpg', 'dpx', 'tga', 'targa', 'png']

        if _path[-1] not in ['/', '\\']:
            _path+='/'

        if os.path.isdir(_path):

            #####LOOK THROUGH PLATES
            plate_folders = [ i for i in os.listdir(_path) if (i[0] != '_') and (i[-1] != '_') ]
            #print plate_folders

            for p in plate_folders:
                plate = _path+p+'/'

                for i in os.listdir(plate):

                    label = p +'\n'+i
                    plate_subdir = plate+i+'/'
                    plate_type = sorted(os.listdir(plate_subdir))[0]
                    plate_type = plate_subdir+plate_type+'/'
                    #files = sorted( [f for f in os.listdir(plate_type) if (".nk" not in f) and ('.' in f) ] )
                    files = sorted( [f for f in os.listdir(plate_type) if f.split('.')[-1].lower() in image_types ] )

                    if len(files)>1:

                        #file = files[0].split('.')
                        #padding = '%0'+ str( len(file[1]) )+'d'
                        #ext = file[-1]
                        #file = file[0]
                        #file = plate_type+file+'.'+padding+'.'+ext
                        plate_type_name = plate_type.split('/')[-3]
                        first = int(files[0].split('.')[1])
                        last = int(files[-1].split('.')[1])

                        #plate_item = { plate_type_name : [first, last] }
                        #plate_item = { 'file':file, 'first':first, 'last':last, 'label':label }

                        plate_items[plate_type_name]=[first, last]



        return plate_items

    def launch(self, event):

        start_time = time.time()

        data = event['data']

        selection = data.get('selection', [])

        edl_entries = {}

        msg = ''

        for entity in selection:

            entityId = entity['entityId']
            selType = entity['entityType']

            shots = self.session.query('select custom_attributes, object_type.name, project_id, type.name, parent.name, name from Shot where children.id is "{0}" or ancestors.id is "{0}" or project_id is "{0}" or id is "{0}"'.format(entityId)).all()

            edl_paths = list(set([i['custom_attributes']['base_path']+'09_QT/EDITORIAL/EDL/' for i in shots]))
            


            '''
            #print edl_paths
            for path in edl_paths:

                #print path
                #print 'aaa'

                #if os.path.isfile(path):
                    
                entries_per_path = self.extract_data_from_EDLs(path)
                #print entries_per_path
                edl_entries.update(entries_per_path)

            '''


            ashot = shots[0]['project_id']

            proj = self.session.query('select custom_attributes from Project where id is "{0}"'.format(shots[0]['project_id'])).first()

            proj_fps =  proj['custom_attributes']['fps']

            for i in shots:

                if i['custom_attributes']['lock_frame_range']:
                    #go to the next item in the loop if the frame range is locked
                    continue

                name = i['name']

                #print name
                #print edl_entries


                if name in edl_entries:

                    #   try:
                    #{'duration': 24, 'shotid': u'TEM_050_030', 'framerate': u'24', 'handle': 10}
                    handles = edl_entries[name]['handles']
                    single_handle = int(handles/2)
                    duration = edl_entries[name]['duration']
                    #timecode = Timecode('29.97', '00:00:00:00')

                    timecode = TC_Op( float( float(edl_entries[name]['framerate']) )).frames_to_timecode( int( edl_entries[name]['timecode'] ))
                    i['custom_attributes']['Duration (frames)'] = duration
                    i['custom_attributes']['fps'] = proj_fps#edl_entries[name]['framerate']
                    #i['custom_attributes']['handles'] = handles
                    #i['custom_attributes']['Ein'] = single_handle+1
                    #i['custom_attributes']['Eend'] = duration-single_handle
                    i['custom_attributes']['Timecode'] = timecode
                    i['custom_attributes']['first_frame']  = 1 #single_handle+1
                    i['custom_attributes']['last_frame'] = duration #duration-single_handle


                    msg += '{0} has been updated from EDLs<br>'.format(name) 

                else:
                    #msg += 'No EDL entry found for {0} in {1}<br>'.format(name, edl_paths)

                    plate_path = i['custom_attributes']['base_path']+'01_PLATES/'+i['name']+'/'

                    available_plates = self.getPlates(plate_path)
                    #available_plates = self.getPlates(shot_plates_path)

                    #frames = [1,100]

                    if available_plates:

                        shot_first_frame = 0
                        shot_last_frame  = 0



                        if 'PLATE_O' in available_plates:
                            shot_first_frame = available_plates['PLATE_O'][0]
                            shot_last_frame  = available_plates['PLATE_O'][1]

                        if 'PLATE_R' in available_plates:
                            shot_first_frame = available_plates['PLATE_R'][0]
                            shot_last_frame  = available_plates['PLATE_R'][1]

                        if 'PLATE_COMBINED' in available_plates:
                            shot_first_frame = available_plates['PLATE_COMBINED'][0]
                            shot_last_frame  = available_plates['PLATE_COMBINED'][1]

                        if 'PLATE_C' in available_plates:
                            shot_first_frame = available_plates['PLATE_C'][0]
                            shot_last_frame  = available_plates['PLATE_C'][1]

                        else:
                            if available_plates:
                                if available_plates.keys():
                                    x = available_plates.keys()[0]
                                    if available_plates[x]:
                                        shot_first_frame = available_plates[x][0]
                                        shot_last_frame  = available_plates[x][1]


                        print shot_first_frame, shot_last_frame


                        if shot_first_frame != shot_last_frame:


                            #i['custom_attributes']['Ein']  = shot_first_frame #single_handle+1
                            #i['custom_attributes']['Eend'] = shot_last_frame #duration-single_handle
                            i['custom_attributes']['first_frame']  = shot_first_frame #single_handle+1
                            i['custom_attributes']['last_frame'] = shot_last_frame #duration-single_handle
                            i['custom_attributes']['Duration (frames)'] = int(shot_last_frame) - int(shot_first_frame) + 1
                            #i['custom_attributes']['handles'] = 0 #Set the handles to 0 when reading generating info from plates dir!

                            msg += '{0} has been updated from PLATES<br>'.format(name) 

                    else:

                        msg += 'Couldnt find an EDL nor PLATE for {0}<br>'.format(name)

                #except KeyError:
                #    msg += 'No EDL entry found for {0} in {1}<br>'.format(name, edl_paths)
                #    pass


        self.session.commit()

        howfast = ("--- %s seconds ---" % (time.time() - start_time)) 
        msg += '<br>'+howfast
        return {
            'success': True,
            'message': msg
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