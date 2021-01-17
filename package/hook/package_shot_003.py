'''Package Shots action for Ftrack
Alican Sesli - Lux VFX - 16.06.2020
    v2: getting it to work
    v3: first stable version
'''

import logging
import ftrack_api
import os, sys
import re
import subprocess
try:
    import ftrack
except:
    pass
import getpass
import datetime
from shutil import copyfile
import json
from subprocess import *

sys.path.append("X:/apps/Scripts/FTRACK/python-lib")
sys.path.append("X:/apps/Scripts/FTRACK/python-lib/lux_utils")

from ftrack_utils import *
import fileinput

os.environ["PYTHONHOME"] = r"C:\Python27"
os.environ["PYTHONPATH"] = r"C:\Python27\Lib"

# setup ftrack environment
try:
    sys.path.insert(0,"L:/HAL/LIVEAPPS/apps/Scripts/FTRACK/ftrack_events/resources")
    import credentials
    os.environ["FTRACK_SERVER"] = credentials.server_url
    os.environ["FTRACK_API_KEY"] = credentials.api_key

except ImportError:
    print("No \"config\" found.")




class Package(object):

    label = 'Package'
    identifier = 'package.shot'
    description = 'Packages all assets belonging to a Shot'
    icon = 'https://static.thenounproject.com/png/442808-200.png'
    variant = 'Shot Files'

    def __init__(self, session):
        '''Initialise action.'''
        super(Package, self).__init__()
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

        job = None
        if ('ftrack' in sys.modules) and (len(selection) > 1):
            userId = event['source']['user']['id']
            job = ftrack.createJob(
                    description='Gathering Shot Information',
                    status='running',
                    user=userId
                )

        #item = session.query('select name, object_type.name, descendants, ancestors, custom_attributes from TypedContext where id is {}'.format( selection[0]['entityId'] )).first()
        item = session.query('select name, object_type.name, descendants, ancestors, custom_attributes, status.name from TypedContext where id is {}'.format( selection[0]['entityId'] )).first()

        project_id = item['project_id']

        slates = get_slates(session, selection, project_id)

        try:
            master_dict = get_task_outputs(session, selection, oneitem=item, job=job)

        except TypeError:
            retFail = {
                'success': False,
                'message': 'Try Again, CIS succesfully failed for no reason! @ master dict'
            }
            return retFail

        template_files_dir = "L:/HAL/LUX_SLATE/nuke_templates"

        template_files = get_nk_files_from_folder( template_files_dir )

        template_files_selection = {
                    'label': 'Slate Template',
                    'type': 'enumerator',
                    'name': 'my_enumerator',
                    'data': [{'label':i, 'value':i} for i in template_files]
                }

        slate_settings = [

                {
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': ' + <i>Output</i>',
                    'type': 'text',
                    'value': '{defaultoutput}/CompPackage_{date}/{shotname}/',#overlays_dict.get('slate_output_offline'),#{defaultoutput}/{slatename}/{format}_{codec}/,
                    'name': 'package_output'
                },

                {
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'value': '<i><b>OVERLAYS & LABELS</b></i>',
                    'type': 'label'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': 'Date',
                    'type': 'date',
                    'name': 'date',
                    'value': datetime.date.today().isoformat()
                },{
                    'label': 'Description Text',
                    'type': 'text',
                    'value': '',#'Client Review',
                    'name': 'description_text'
                },{
                    'label': 'Custom Text',
                    'type': 'text',
                    'value': '',#'',
                    'name': 'custom_text'
                },
                
                {
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'value': '<i><b>SUBMISSION RESULTS</b></i>',
                    'type': 'label'
                },{
                    'value': '<hr>',
                    'type': 'label'
                }]


        shot_items = slate_settings


        for shot in master_dict:

            asset_name = shot['asset_name']
            index = shot['index']
            version_items = []
            frame_range = '{0}-{1}'.format( str(shot['first_frame']) , str(shot['last_frame']) )
            text = 'Could not locate rendered files.....\r'
            success_msg = 'FAILED'
            if shot['success']:
                success_msg = 'SUCCESSFUL'

                text = '''
    Offline sequence : {0}\r
    Online sequence  : {1}\r
    Slate Location   : {2}\r
'''.format(shot['image_file'],shot['metad_file'],shot['slate_output'])

                if shot['matte_file'] != '' :
                    #text = text + 'Mattes sequence : {0}\r'.format( shot['matte_file'] )
                    text = '''
    Offline sequence : {0}\r
    Online sequence  : {1}\r
    Matte  sequence  : {3}\r
    Slate Location   : {2}\r
'''.format(shot['image_file'],shot['metad_file'],shot['slate_output'],shot['matte_file'])

            text = text+'<hr>'

            vers_ext = ''
            if asset_name!='':
                vers_ext = '_'+asset_name.split('_')[-1]

            for i in shot['versions']:
                new_entry =  {}
                new_entry['label'] = i
                new_entry['value'] = i
                version_items.append(new_entry)

            title = {
                    'value': '<b>{0}{1}</b> : {3}<i>{2}</i>'.format(shot['item_title'], vers_ext, success_msg, '&nbsp;'*2),
                    'type': 'label'
                }

            title = {
                    'value': '<b>{}</b>'.format(shot['shot_name']),
                    'type': 'label'
                }
            message = {
                    'value': '<b>Existing Versions : </b>'+', '.join(shot['versions']),
                    'type': 'label'
                }

            framerange = {
                    'label': 'Frame Range',
                    'type': 'text',
                    'value': frame_range,
                    'name': 'framerange_{0}'.format(index)
                }

            br = {
                    'value': '<hr>',
                    'type': 'label'
                }


            if len(version_items) == 0:
                version_items.append( {'label':'None Found..', 'value':None} )

            versions = {
                    'label': 'Version',
                    'type': 'enumerator',
                    'value': version_items[0].get('label'),
                    'data' : version_items,
                    'name': 'version_{0}'.format(index)
                }


            comp_items = []
            for i in shot['comp_scripts']:
                new_entry =  {}
                new_entry['label'] = i
                new_entry['value'] = i
                comp_items.append(new_entry)
            if len(comp_items) == 0:
                comp_items.append( {'label':'None Found..', 'value':None} )

            versions_enum = {
                    'label': '<font color="green">Nuke Scripts</font>',
                    'type': 'enumerator',
                    'value': comp_items[-1].get('label'),#proj['custom_attributes']['resolution'],#slate_codecs[9].get('label'),#slate_txt_positions[6].get('label'),
                    'data' : comp_items,
                    'multi_select' : True,
                    'name': 'version_{0}'.format(index)
                }



            shot_items.append(title)
            #shot_items.append(versions)
            shot_items.append(versions_enum)
            shot_items.append(framerange)
            shot_items.append(message)
            shot_items.append(br)
            
        totalSlatedItems = 0
        totalPackagedItems = 0


        retUI = {'items': shot_items}

        if 'values' in data:

            # Do something with the values or return a new form.
            values = data['values']

            commit = False
            totalPackagedItems = 0
            
            self.logger.info(u'Got values: {0}'.format(values))


            shot_related_params = []
            for value in values:
                if ('_' in value) :
                    if (value.split('_')[-1]).isdigit():
                        shot_related_params.append(value)


            for item in master_dict:
                #print item
                for p in shot_related_params:
                    p_index = int(p.split('_')[-1])
                    if item['index'] == p_index:
                        if p.split('_')[0] == 'version':
                            item['version'] = values[p]
                        if p.split('_')[0] == 'framerange':
                            first_last = values[p].split('-')
                            item['first_frame'] = str(first_last[0])
                            item['last_frame'] = str(first_last[-1])
                            item['duration'] = str(int(first_last[-1]) - int(first_last[0]) + 1)


                if item['success']:

                    totalPackagedItems+=1
                    item['default_base_output'] = os.path.join(item['base_path'], "03_COORDINATION/PACKAGED_SHOTS")

                    #print item['version']

                    for nk in item['version']:

                        values['version'] = nk

                        item['package_output'] = values['package_output']
                        item['slate_name'] = item['shot_name']+'_Shot_Package'


                        item2 = item
                        item2['version']=nk
                        item['package_output'] = translate(item['package_output'], [values, item2])
                        #item['image_file'] = item['image_file'].replace(item['asset_name'],item['version'])
                        #item['metad_file'] = item['metad_file'].replace(item['asset_name'],item['version'])
                        #item['slate_output'] = item['slate_output'].replace(item['asset_name'],item['version'])
                        #item['asset_name'] = item['version']

                        nk_file = '{}05_COMP/{}/{}'.format(item['base_path'],item['shot_name'],nk)

                        firstframe = item['first_frame']
                        lastframe = item['last_frame']
                        inputImage   = item['image_file']
                        inputTCImage = item['slate_name']
                        outputImage  = item['slate_output']

                        user = getpass.getuser()

                        temp_dir = "L:\\tmp\\deadline_submission_scripts\\package_slates"

                        if not os.path.isdir(temp_dir):
                            os.makedirs(temp_dir)

                        asset_name = item['asset_name']





                        _nuke_script = item['image_file'].split('.')[0]+'.nk'

                        #_nuke_script = nk_file
                        _replaced_script = os.path.join(os.path.dirname(item['slate_output']), os.path.basename(_nuke_script))



                        _nuke_script = nk_file
                        _replaced_script = '{}/{}'.format(item['package_output'], nk)
                        _replaced_script =_replaced_script.replace('//','/')


                        #print _nuke_script
                        #print _replaced_script





                        sys.path.append('//qumulo/Libraries/HAL/LIVEAPPS/apps/Scripts/FTRACK/ftrack_hooks/package_hook/hook/')
                        import node_parser_006 as nodeparser
                        
                        title = nk + ' Package'
                        package_path = os.path.dirname(_replaced_script)
                        date = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")

                        package_files = nodeparser.replace_nuke(_nuke_script, _replaced_script) 

                        #print package_files

                        # print 'inputs'
                        for i in  package_files['inputs']:
                            #print i['original'], '---->', i['new']
                            _i = i['original'].replace('"','').replace("'",'')
                            _o = (package_path+'/'+i['new']).replace('//','/').replace('\\','/').replace('"','').replace("'",'')
                            io = [_i,_o]
                            #print io
                            weird = _o.split('SOURCED_ASSETS')[-1].split('.')[0]
                            #print weird
                            #copyNukeFiles(_i,_o)
                            submitPackagePyToDeadline( title,date,weird,io )

                        #print 'outputs'
                        for o in  package_files['outputs']:
                            #print o['original'], '---->', o['new']
                            _i = o['original'].replace('"','').replace("'",'')
                            _o = (package_path+'/'+o['new']).replace('//','/').replace('\\','/').replace('"','').replace("'",'')
                            io = [_i,_o]
                            weird = _o.split('SOURCED_ASSETS')[-1].split('.')[0]
                            #print io
                            #print weird
                            #copyNukeFiles(_i,_o)
                            submitPackagePyToDeadline( title,date,weird,io )



            retSuccess = {
                'success': True,
                'message': 'Packaging {0}/{1} items'.format(totalPackagedItems,len(master_dict))
            }

            if not totalPackagedItems:
                retSuccess['success'] = False

            return retSuccess

        if ('ftrack' in sys.modules) and (len(selection) > 1):
            job.setStatus('done')
            job.setDescription('Gathered {} items'.format( len(selection) )) 

        return retUI
        
def register(session, **kw):

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    action = Package(session)
    action.register()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()