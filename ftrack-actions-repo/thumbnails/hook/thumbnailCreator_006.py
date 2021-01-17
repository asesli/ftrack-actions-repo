
import os, sys
import subprocess

print('Python Version: ', sys.version)





sys.path.insert(0, "\\\\qumulo\\Libraries\\python-lib\\FTRACK")
import ftrack_api

sys.path.insert(0, "\\\\qumulo\\Libraries\\python-lib")


sys.path.append("X:/apps/Scripts/FTRACK/python-lib")
sys.path.append("X:/apps/Scripts/FTRACK/python-lib/lux_utils")
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


import imageio
import scipy.misc

from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True





def convertJpegFolderToGif(path, out_file, maxFrame, scale, speed, everyNthFrame):
    '''
    _path = "Q:/TEMP_PROJECT/05_COMP/TEM_001_120/02_OUTPUT/03_comp/TEM_001_120_V005/JPEG/"
    _out_file = "Q:/TEMP_PROJECT/03_COORDINATION/_thumbs/TEM_001_120_V005.gif"
    _maxFrame = '100'
    _scale = '0.1'
    _speed = '1'
    _everyNthFrame = '3'
    '''

    verbose = True

    path = path

    img_folder = os.path.dirname(path)

    imgs = [os.path.join(img_folder, i).replace('\\', '/') for i in sorted(os.listdir(img_folder)) if i.lower().split('.')[-1] in ['jpeg','jpg']]

    speed = float(speed)

    scale = float(scale)

    hold = int(everyNthFrame)   

    maximum = int(maxFrame)

    numpy_imgs = []

    cnt = 0
    cnt_to_use = 0

    imgs = imgs[:maximum]
    imgs = imgs[0::hold]
    print imgs
    for i, image in enumerate(imgs):

        the_img = imgs[i]

        im = imageio.imread(the_img)
        im = scipy.misc.imresize(im, scale)
        numpy_imgs.append(im)
        print 'Processing : {0}'.format(os.path.basename(the_img))

    kargs = { 'duration': ((0.1)*hold)/speed }
    imageio.mimsave(out_file, numpy_imgs, **kargs)
    
    return out_file


#print ftrack_api.__file__

selection = sys.argv[1]

selection = eval(selection)


#selection=[{u'entityId': u'8cc661de-0738-11ea-8928-92bd04417814', u'entityType': u'task'}]

#print selection

#os.environ['FTRACK_API_USER'] = os.environ.get("USERNAME")
os.environ['FTRACK_API_USER'] = "luxrj"


session = ftrack_api.session.Session(auto_connect_event_hub=True)



def create_and_upload_thumbnail(item, imgdir, gifpath):

    #imagefolder = "Q:/TEMP_PROJECT/05_COMP/TEM_001_120/02_OUTPUT/03_comp/TEM_001_120_V005/JPEG/"
    #thumbsfolder = "Q:/TEMP_PROJECT/03_COORDINATION/_thumbs/"
    #img_folder = LuxIOps(imagefolder)

    file = r'L:/HAL/LIVEAPPS/utils/jpeg2gif/dist/jpeg2gif.exe'

    #path = r"Q:/TEMP_PROJECT/05_COMP/TEM_005_100/02_OUTPUT/03_comp/TEM_005_100_V003/JPEG/"
    path = imgdir

    #out_file = r"Q:/TEMP_PROJECT/03_COORDINATION/_thumbs/TEM_005_100_V003.gif"
    out_file = gifpath
    
    maxFrame = r'100'
    scale = r'0.1'
    speed = r'2'
    everyNthFrame = r'3'

    if not os.path.isfile(out_file):

        try:
            #convertJpegFolderToGif()
            convertJpegFolderToGif( path, out_file, maxFrame, scale, speed, everyNthFrame )
            #subprocess.call( [file, path, out_file, maxFrame, scale, speed, everyNthFrame] )
        except WindowsError:
            print 'Something went wrong with the jpeg2gif.exe'
    #filename = convertJpegFolderToGif(imagefolder, out_path=thumbsfolder, hold=2, max=100)
    
    if os.path.isfile(out_file):
        print out_file
        thumbnail_component = item.create_thumbnail(out_file)
    else:
        print out_file, 'does not exist'

entityTypes = ['Project', 'Episode', 'Sequence', 'Shot', 'Task']

dept_folders = ['01_PLATES','02_INPUT','03_COORDINATION','04_3D','05_COMP','06_RENDERS','07_DAILIES','08_PFTrack','09_QT']


associated_shots =[]
associated_seqs = []
associated_epis = []
#all_objs = []


for entity in selection:

    num = 0
    et = entityTypes[num]

    item = session.query('select name from {0} where id is {1}'.format(et, entity['entityId'])).first()

    while item == None:
        num += 1
        et = entityTypes[num]
        item = session.query('select name from {0} where id is {1}'.format(et, entity['entityId'])).first()


    #print et
    #print 'context_type:', item['context_type']
    #print 'name:', item['name']
    #object_type = item['object_type']['name'] #Shot, Task, Sequence, project
    
    object_name = item['name']
    if et == 'Project':
        title = item['full_name']
    else:    
        title = item['project']['full_name']
    
    #print 'name:',object_name

    #print 'selection: {0} - {1}'.format(object_type, object_name)

    descendants = item['descendants'][:]

    if et == 'Project':
        #print item['name'] #name of the object
        #dont append the item if its a project; project thumbs should be manual.
        pass
    if et == 'Episode':
        descendants.append(item)
        pass
    if et == 'Sequence':
        descendants.append(item)
        pass
    if et == 'Shot':
        descendants.append(item)
        pass
    if et == 'Task':
        descendants.append(item['parent'])
        pass

    #print descendants

    if len(descendants):
        for d in descendants:
            obj = d['id']
            if d['object_type']['name'] == 'Shot':
                #print d['name']
                associated_shots.append(obj)

            if d['object_type']['name'] == 'Sequence':
                #print d['name']
                associated_seqs.append(obj)

            if d['object_type']['name'] == 'Episode':
                #print d['name']
                associated_epis.append(obj)


    #print associated_shots, associated_seqs, associated_epis

#obj_list = [associated_shots, associated_seqs, associated_epis]

shot_ids = associated_shots#input_list[0]
shot_ids = [str(i) for i in shot_ids]
if len(shot_ids) > 1:
    shot_ids = tuple(shot_ids)
    shot_objs = session.query('select name, type, link, project.custom_attributes, project.full_name from TypedContext where id in {0}'.format( shot_ids )).all()
else:
    if len(shot_ids) != 0:
        shot_ids = shot_ids[0]
        shot_objs = session.query('select name, type, link, project.custom_attributes, project.full_name from TypedContext where id is {0}'.format( shot_ids )).all()
    else:
        shot_objs = []
#print shot_ids


sequ_ids = associated_seqs#input_list[1]
sequ_ids = [str(i) for i in sequ_ids]
if len(sequ_ids) > 1:
    sequ_ids = tuple(sequ_ids)
    sequ_objs = session.query('select name, type, link, project.custom_attributes, project.full_name from TypedContext where id in {0}'.format( sequ_ids )).all() 
else:
    if len(sequ_ids) != 0:
        sequ_ids = sequ_ids[0]
        sequ_objs = session.query('select name, type, link, project.custom_attributes, project.full_name from TypedContext where id is {0}'.format( sequ_ids )).all() 
    else:
        sequ_objs = []
#print sequ_ids


epis_ids = associated_epis#input_list[2]
epis_ids = [str(i) for i in epis_ids]
if len(epis_ids) > 1:
    epis_ids = tuple(epis_ids)
    epis_objs = session.query('select name, type, link, project.custom_attributes, project.full_name from TypedContext where id in {0}'.format( epis_ids )).all()
else:
    if len(epis_ids) != 0:
        epis_ids = epis_ids[0]
        epis_objs = session.query('select name, type, link, project.custom_attributes, project.full_name from TypedContext where id is {0}'.format( epis_ids )).all()
    else:
        epis_objs = []

print shot_objs
print sequ_objs
print epis_objs

associated_shots = shot_objs
associated_seqs = sequ_objs
associated_epis = epis_objs

#all_objs = shot_objs + sequ_objs +epis_objs
#objs_len = len(all_objs)
progress_len = float(len(shot_objs + sequ_objs +epis_objs))
progress_inc = float(100.0/(progress_len))
progress = 0.00
#progress += progress_inc
print("Total Objects: {}".format(progress_len))
print("Progress: {}%".format(int(progress)))

msg = '<br>'
if len(associated_shots):
    for shot in associated_shots:
        #go into comp folder and find latest populated jpeg folder. 
        #turn it into a gif if the version doesnt already exist
        #print shot.keys()
        
        drive_dir = shot['project']['custom_attributes']['Project_Path']
        project_dir = shot['project']['full_name']
        epispode_dir = ''
        shot_dir = shot['name']
        #print shot['link']
        
        dept_folder_root = drive_dir+project_dir+'/'

        for i in shot['link']:
            if i['type'] == 'TypedContext':
                if len(i['name'])<=6:
                    epispode_dir = i['name']
                    dept_folder_root+=i['name']+'/'
                    break

        comp_output_path = dept_folder_root + '05_COMP/'+shot_dir+'/02_OUTPUT/03_comp/'

        plate_output_path = dept_folder_root + '01_PLATES/'+shot_dir+'/PLATE/PLATE_O/02_FULL_RES_JPEGS/'

        gif_name = 'temp.gif'

        if not os.path.isdir(dept_folder_root + '03_COORDINATION/_thumbs/'):
            os.makedirs(dept_folder_root + '03_COORDINATION/_thumbs/')

        #check to see if this fodler exist otherwise use plates or something...
        if os.path.isdir(comp_output_path):
            #this will still fail.. 
            possible_versions =sorted([i for i in os.listdir(comp_output_path) if i.lower().split('_v')[0]==shot_dir.lower()])
            possible_versions = reversed(possible_versions)
            #print possible_versions
            version = ''
            
            for i in possible_versions:
                gif_name = i+'.gif'
                _p = comp_output_path+i+'/JPEG/'
                if os.path.isdir(_p):
                    if len( [ f for f in  os.listdir(_p) if '.jp' in f ] )>1:
                        version = i
                        break

            comp_output_path+=version+'/JPEG/'
            gif_path = dept_folder_root + '03_COORDINATION/_thumbs/' + gif_name
            #print comp_output_path
            #create_and_upload_thumbnail(shot, comp_output_path)

            create_and_upload_thumbnail(shot, comp_output_path, gif_path)


            #print '/'.join([i['name'] for i in shot['link']])
            #print '/'.join(shot['link']['name'])
            #create_and_upload_thumbnail(shot)
            msg+='<br>Creating/Updating thumbs from COMP '+shot['name']
            #pass


        elif os.path.isdir(plate_output_path):
            gif_path = dept_folder_root + '03_COORDINATION/_thumbs/' + shot_dir+'.gif'

            create_and_upload_thumbnail(shot, plate_output_path, gif_path)


            msg+='<br>Creating/Updating thumbs from PLATES '+shot['name']

        progress += progress_inc
        print("Progress: {}%".format(int(progress)))

if len(associated_seqs):
    for seq in associated_seqs:

        drive_dir = seq['project']['custom_attributes']['Project_Path']
        project_dir = seq['project']['full_name']
        epispode_dir = ''
        dept_folder_root = drive_dir+project_dir+'/'

        for i in shot['link']:
            if i['type'] == 'TypedContext':
                if len(i['name'])<=6:
                    epispode_dir = i['name']
                    dept_folder_root+=i['name']+'/'
                    break

        seq_name = seq['name']
        seq_name_head = seq_name.split('_SEQ')[0]
        
        thumbs_folder = dept_folder_root + '/03_COORDINATION/_thumbs/'
        seq_gif = ''
        if os.path.isdir(thumbs_folder):

            seq_thumbs = [ sgif for sgif in os.listdir(thumbs_folder) if seq_name_head in sgif ]
            seq_thumbs = sorted(seq_thumbs)
            
            if len(seq_thumbs) > 0:
                first_shot = seq_thumbs[0].split('_V')[0]
                first_shot_thumbs = [ fsgif for fsgif in os.listdir(thumbs_folder) if first_shot in fsgif ]#all versions of first shot in seq.
                first_shot_thumbs = sorted(first_shot_thumbs)
                seq_gif = first_shot_thumbs[-1]#latest v of first shot
                seq_gif_path = thumbs_folder + '/' + seq_gif


                thumbnail_component = seq.create_thumbnail(seq_gif_path)



        msg+='<br>Using {0} for {1}'.format( seq_gif, seq_name ) 

        progress += progress_inc
        print("Progress: {}%".format(int(progress)))

if len(associated_epis):
    for epi in associated_epis:

        drive_dir = epi['project']['custom_attributes']['Project_Path']
        project_dir = epi['project']['full_name']
        epispode_dir = ''

        dept_folder_root = drive_dir+project_dir+'/'

        for i in shot['link']:
            if i['type'] == 'TypedContext':
                if len(i['name'])<=6:
                    epispode_dir = i['name']
                    dept_folder_root+=i['name']+'/'
                    break

        epi_name = epi['name']
        epi_gif = ''
        thumbs_folder = dept_folder_root + '/03_COORDINATION/_thumbs/'

        if os.path.isdir(thumbs_folder):

            epi_thumbs = [ egif for egif in os.listdir(thumbs_folder) if epi_name in egif ]
            epi_thumbs = sorted(epi_thumbs)
            
            if len(epi_thumbs) > 0:
                first_shot = epi_thumbs[0].split('_V')[0]
                first_shot_thumbs = [ fsgif for fsgif in os.listdir(thumbs_folder) if first_shot in fsgif ]#all versions of first shot in seq.
                first_shot_thumbs = sorted(first_shot_thumbs)
                epi_gif = first_shot_thumbs[-1]#latest v of first shot
                epi_gif_path = thumbs_folder + '/' + epi_gif


                thumbnail_component = epi.create_thumbnail(epi_gif_path)


        msg+='<br>Using {0} for {1}'.format( epi_gif, epi_name ) 
        progress += progress_inc
        print("Progress: {}%".format(int(progress)))


msg = msg.replace('<br>', '\n\r')

print msg
