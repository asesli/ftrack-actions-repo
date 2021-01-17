'''Slate assets action for Ftrack
Alican Sesli - Lux VFX - 19.01.2018 - 24.04.2020
    v31 - NEW SLATING - ues the slate items from ftrack
    v32 - script organization/minor restructuring
    v33 - slate_assets unrolled.
    v34 - housekeeping
    v35 - modularized
    v37 - gather as job, external modules
    v38 - get_slates() connecton now needs proj_id, instead of optional oneitem to retrieve projid from.
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


class SlateAsset(object):

    label = 'Slate'
    identifier = 'slate.selected.tasks'
    description = 'This will slate outputs of selected task(s)'
    icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/1465042-200.png'
    variant = 'Assets'

    def __init__(self, session):
        '''Initialise action.'''
        super(SlateAsset, self).__init__()
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
                    'value': '<i><b>CHOOSE YOUR SLATES</b></i>',
                    'type': 'label'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': '<font color="green">Slates</font>',
                    'type': 'enumerator',
                    'value': '',#proj['custom_attributes']['resolution'],#slate_codecs[9].get('label'),#slate_txt_positions[6].get('label'),
                    'data' : slates,
                    'multi_select' : True,
                    'name': 'slates'
                },{
                    'value': '<hr>',
                    'type': 'label'
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
                },{
                    'value': '<hr>',
                    'type': 'label'
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

            message = {
                    'value': text,
                    'type': 'label'
                }

            framerange = {
                    'label': 'Frame Range',
                    'type': 'text',
                    'value': frame_range,
                    'name': 'framerange_{0}'.format(index)
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

            shot_items.append(title)
            shot_items.append(versions)
            shot_items.append(framerange)
            shot_items.append(message)
            
        totalSlatedItems = 0

        retUI = {'items': shot_items}

        if 'values' in data:

            # Do something with the values or return a new form.
            values = data['values']

            commit = False
            
            self.logger.info(u'Got values: {0}'.format(values))
            
            slates = [str(i) for i in values['slates']]

            if slates == 'Empty':
                slates = []
                ret_fail = {
                    'success': False,
                    'message': 'No slates chosen.'
                }
                return ret_fail

            if len(slates) > 1:

                ftrack_slates = session.query('select name, custom_attributes, project.id from Slate where name in {} and project.id is {}'.format( tuple(slates), project_id )).all()

            if len(slates) == 1:

                ftrack_slates = session.query('select name, custom_attributes, project.id from Slate where name is "{}" and project.id is {}'.format( slates[0], project_id )).all()

            for fslate in ftrack_slates:
                #iterate through the ftrack slate items that are chosen

                slate_custom_attributes = fslate['custom_attributes']

                if not values['description_text']:
                    values['description_text'] = slate_custom_attributes['slate_overlays_description_text']

                if not values['custom_text']:
                    values['custom_text'] = slate_custom_attributes['slate_overlays_custom_text']

                totalSlatedItems = 0

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

                        totalSlatedItems += 1

                        asset_name = item['asset_name']

                        item['slate_type']      = slate_custom_attributes['slate_type']
                        item['slate_name']      = fslate['name']
                        item['asset_name']      = asset_name
                        item['codec']           = slate_custom_attributes['slate_codec']
                        item['format']          = slate_custom_attributes['slate_format']
                        item['slate_frame']     = slate_custom_attributes['slate_slateframe']
                        item['overlays']        = slate_custom_attributes['slate_overlays']
                        item['colorspace_in']   = slate_custom_attributes['slate_colorspace_in']
                        item['colorspace_out']  = slate_custom_attributes['slate_colorspace_out']
                        item['data_type']       = slate_custom_attributes['slate_data_type']

                        item['image_file']      = item['image_file'].replace(item['asset_name'],item['version'])
                        item['metad_file']      = item['metad_file'].replace(item['asset_name'],item['version'])
                        item['slate_output']    = item['slate_output'].replace(item['asset_name'],item['version'])

                        if item['slate_type']  == 'mattes':
                            item['image_file']  = item['matte_file'].replace(item['asset_name'],item['version'])

                        item['asset_name'] = item['version']

                        firstframe   = item['first_frame']
                        lastframe    = item['last_frame']
                        inputImage   = item['image_file']
                        inputTCImage = item['metad_file']
                        outputImage  = item['slate_output']

                        user = getpass.getuser()

                        temp_dir = "L:\\tmp\\deadline_submission_scripts\\slates"

                        if not os.path.isdir(temp_dir):
                            os.makedirs(temp_dir)

                        template = slate_custom_attributes['slate_template']
                        slate_descriptor = template.split('.')[0]
                        slate_descriptor = slate_descriptor.replace('Generic_Slate_','')
                        slate_descriptor = slate_descriptor.replace('Manual_Slate_','')
                        template_path = os.path.join(template_files_dir, template).replace('\\', '/')

                        item['slate_template_name'] = slate_descriptor

                        if slate_custom_attributes['slate_rename']:

                            item['asset_name'] = translate(slate_custom_attributes['slate_assetname_rename'], [values, item])

                        slate_overlays = {
                            'slate_top_left'            : translate(slate_custom_attributes['slate_overlays_top_left'], [values, item]),
                            'slate_top_right'           : translate(slate_custom_attributes['slate_overlays_top_right'], [values, item]),
                            'slate_top_center'          : translate(slate_custom_attributes['slate_overlays_top_center'], [values, item]),
                            'slate_bottom_left'         : translate(slate_custom_attributes['slate_overlays_bottom_left'], [values, item]),
                            'slate_bottom_right'        : translate(slate_custom_attributes['slate_overlays_bottom_right'], [values, item]),
                            'slate_bottom_center'       : translate(slate_custom_attributes['slate_overlays_bottom_center'], [values, item]),
                            
                            'slate_frame_project_title' : translate(slate_custom_attributes['slate_slateframe_project_title'], [values, item]),
                            'slate_frame_description'   : translate(slate_custom_attributes['slate_slateframe_description'], [values, item]),
                            'slate_frame_shot_title'    : translate(slate_custom_attributes['slate_slateframe_shot_title'], [values, item]),
                            'slate_frame_range_info'    : translate(slate_custom_attributes['slate_slateframe_range_info'], [values, item]),
                            'slate_frame_timecode_info' : translate(slate_custom_attributes['slate_slateframe_timecode_info'], [values, item]),
                            'slate_frame_version_info'  : translate(slate_custom_attributes['slate_slateframe_version_info'], [values, item])}

                        item['slate_overlays'] = slate_overlays

                        str_slate_type = item['slate_name'].replace(' ','')
                        slatefile   = os.path.join(temp_dir,'{}_{}_slate.nk'.format( item['asset_name'] , str_slate_type )).replace('\\', '/')
                        job_info    = os.path.join(temp_dir,'{}_{}_nuke_job_info.job'.format( item['asset_name'] , str_slate_type )).replace('\\', '/')
                        plugin_info = os.path.join(temp_dir,'{}_{}_nuke_plugin_info.job'.format( item['asset_name'] , str_slate_type )).replace('\\', '/')

                        item['slate_output'] = slate_custom_attributes['slate_output']
                        item['slate_output'] = translate(item['slate_output'], [values, item])

                        slate_frame_subtract = 1
                        if item['slate_frame'] == False:
                            slate_frame_subtract = 0
                        
                        frames = "{0}-{1}".format(firstframe, lastframe)
                        sframes = "{0}-{1}".format(str(int(firstframe)-slate_frame_subtract), lastframe)

                        CreateNukeSlateFile( slatefile, template_path, item )

                        CreateNukeJob( slatefile, sframes, item['asset_name']+' '+item['slate_name'], item['slate_output'], user, job_info, plugin_info)

                        SubmitJobToDeadline( job_info, plugin_info, slatefile )

            retSuccess = {
                'success': True,
                'message': 'Slating {0}/{1} items!'.format(totalSlatedItems,len(master_dict))
            }

            if not totalSlatedItems:
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

    action = SlateAsset(session)
    action.register()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()