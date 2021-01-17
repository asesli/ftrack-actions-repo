'''Create Slate action for Ftrack
Alican Sesli - Lux VFX - 03.02.2020 - 04.02.2020
    v01 - proting in from slate assets v28
    v02 - wip
    v05 - works
    v06 - slates need to go to a folder named slates on ftrack
'''

import logging
import ftrack_api
import os
import sys

try:
    import ftrack
except:
    pass
import getpass
import datetime



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


class CreateSlate(object):
    '''Custom action.'''

    label = 'Slate'
    identifier = 'create.a.slate'
    description = 'This will create a slate for slating and converting shots.'
    icon = 'https://d30y9cdsu7xlg0.cloudfront.net/png/1465042-200.png'
    variant = 'Create'

    def __init__(self, session):
        '''Initialise action.'''
        super(CreateSlate, self).__init__()
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
        #print event
        selection = data.get('selection', [])

        entityTypes = ['Project', 'Episode', 'Sequence', 'Shot', 'Task']

        dept_folders = ['01_PLATES','02_INPUT','03_COORDINATION','04_3D','05_COMP','06_RENDERS','07_DAILIES','08_PFTrack','09_QT']

        list_of_resolutions = [
            ['PC_Video  640 x 480','640 480 0 0 640 480 1 PC_Video'],
            ['NTSC  720 x 486 0.91','720 486 0 0 720 486 0.91 NTSC'],
            ['PAL  720 x 576 1.09','720 576 0 0 720 576 1.09 PAL'],
            ['NTSC_16:9  720 x 486 1.21','720 486 0 0 720 486 1.21 NTSC_16:9'],
            ['PAL_16:9  720 x 576 1.46','720 576 0 0 720 576 1.46 PAL_16:9'],
            ['HD_720  1280 x 720','1280 720 0 0 1280 720 1 HD_720'],
            ['HD_1080  1920 x 1080','1920 1080 0 0 1920 1080 1 HD_1080'],
            ['UHD_4K  3840 x 2160','3840 2160 0 0 3840 2160 1 UHD_4K'],
            ['1K_Super_35(full-ap)  1024 x 778','1024 778 0 0 1024 778 1 1K_Super_35(full-ap)'],
            ['1K_Cinemascope  914 x 778 2.0','914 778 0 0 914 778 2 1K_Cinemascope'],
            ['2K_Super_35(full-ap)  2048 x 1556','2048 1556 0 0 2048 1556 1 2K_Super_35(full-ap)'],
            ['2K_Cinemascope  1828 x 1556 2.0','1828 1556 0 0 1828 1556 2 2K_Cinemascope'],
            ['2K_DCP  2048 x 1080','2048 1080 0 0 2048 1080 1 2K_DCP'],
            ['4K_Super_35(full-ap)  4096 x 3112','4096 3112 0 0 4096 3112 1 4K_Super_35(full-ap)'],
            ['4K_Cinemascope  3656 x 3112 2.0','3656 3112 0 0 3656 3112 2 4K_Cinemascope'],
            ['4K_DCP  4096 x 2160','4096 2160 0 0 4096 2160 1 4K_DCP'],
            ['square_256  256 x 256','256 256 0 0 256 256 1 square_256'],
            ['square_512  512 x 512','512 512 0 0 512 512 1 square_512'],
            ['square_1K  1024 x 1024','1024 1024 0 0 1024 1024 1 square_1K'],
            ['square_2K  2048 x 2048','2048 2048 0 0 2048 2048 1 square_2K'],
            ['square_128  128 x 128','128 128 0 0 128 128 1 square_128'],
            ['square_4K  4096 x 4096','4096 4096 0 0 4096 4096 1 square_4K'],
            ['square_8K  8192 x 8192','8192 8192 0 0 8192 8192 1 square_8K'],
            ['HALF_HD  960 x 540','960 540 0 0 960 540 1 HALF_HD'],
            ['FCP  720 x 480 0.89','720 480 0 0 720 480 0.9 FCP'],
            ['BBC  2048 x 1165','2048 1165 0 0 2048 1165 1 BBC'],
            ['BBC_HALF  1024 x 582','1024 582 0 0 1024 582 1 BBC_HALF'],
            ['DCI_2K  2048 x 1080','2048 1080 0 0 2048 1080 1 DCI_2K'],
            ['DCI_2K_16:9  2048 x 1152','2048 1152 0 0 2048 1152 1 DCI_2K 16:9'],
            ['ANA_2K 2.66:1 2288 x 858','2288 858 0 0 2288 858 1 ANA_2K'],
            ['QHD+ 16:9 3200 x 1800','3200 1800 0 0 3200 1800 1 QHD+ 16:9'],
            ['4K_ANA 4096 x 3416', '4096 3416 0 0 4096 3416 2 4K_ANA'],
            ['4K_ANA_S 4096 x 3416', '4096 3416 0 0 4096 3416 1 4K_ANA_S'],
            ['3K 2880 x 1620', '2880 1620 0 0 2880 1620 1 3K']

        ]

        session = ftrack_api.Session()

        template_files = []

        template_files_dir = "L:/HAL/LUX_SLATE/nuke_templates"

        if os.path.isdir(template_files_dir):
            template_files = [i for i in os.listdir(template_files_dir) if i[-3:] == '.nk']

        master_dict = []

        index = 0

        entity = selection[0]


        #print entity.keys()
        #print entity['entityType']

        if entity['entityType'] == 'show':

            project_id = entity['entityId']

            proj = session.query('select full_name, custom_attributes from Project where id is "{0}"'.format(project_id)).first()

        else:

            item = session.query('select name, project.id, id from TypedContext where id is {0}'.format(entity['entityId'])).first()
            
            project_id = item['project']['id']

            proj = session.query('select full_name, custom_attributes from Project where id is "{0}"'.format(project_id)).first()

        #print proj

        shot_items = []
        template_items = []

        for i in template_files:
            new_entry =  {}#{dict(template_file_entry)}
            new_entry['label'] = i
            new_entry['value'] = i
            template_items.append(new_entry)

        slate_txt_items = sorted(['{none}','{date}', '{framecounter}', '{project}', '{projectname}', '{episode}', '{episodename}', '{sequence}', '{shot}', '{shotname}', '{version}', '{task}', '{assetname}', '{description}','{slatename}', '{custom}', '{lens}', '{status}', '{codec}', '{format}', '{firstframe}', '{lastframe}', '{duration}','{logo}','{colorspacein}','{colorspaceout}', 'Lux Visual Effects'])
        slate_txt_positions = []
        for item in slate_txt_items:
            #slate_txt_dct = {'label':item, 'value':item.split('<')[-1].split('>')[0]}
            slate_txt_dct = {'label':item, 'value':item}
            slate_txt_positions.append(slate_txt_dct)

        slate_codecs_raw = ['', 'rle \tAnimation', 'apcn\tApple ProRes 422', 'apch\tApple ProRes 422 HQ', 'apcs\tApple ProRes 422 LT', 'apco\tApple ProRes 422 Proxy', 'ap4h\tApple ProRes 4444', 'ap4x\tApple ProRes 4444 XQ', 'AV1x\tAvid 1:1x', 'AVdn\tAvid DNxHD Codec', 'AVdh\tAvid DNxHR Codec', 'AVdv\tAvid DV Codec', 'AVd1\tAvid DV100 Codec', 'AVj2\tAvid JPEG 2000 Codec', 'AVDJ\tAvid Meridien Compressed', 'AVUI\tAvid Meridien Uncompressed', 'AVup\tAvid Packed Codec', 'AVrp\tAvid RGBPacked Codec', 'WRLE\tBMP', 'cvid\tCinepak', 'yuv2\tComponent Video', 'dvcp\tDV - PAL', 'dvc \tDV/DVCPRO - NTSC', 'dvpp\tDVCPRO - PAL', 'smc \tGraphics', 'h261\tH.261', 'h263\tH.263', 'avc1\tH.264', 'mjp2\tJPEG 2000', 'mp1v\tMPEG-1 Video', 'mp4v\tMPEG-4 Video', 'mjpa\tMotion JPEG A', 'mjpb\tMotion JPEG B', 'raw \tNone', 'png \tPNG', 'jpeg\tPhoto - JPEG', '8BPS\tPlanar RGB', 'SVQ1\tSorenson Video', 'SVQ3\tSorenson Video 3', 'tga \tTGA', 'tiff\tTIFF', 'v210\tUncompressed 10-bit 4:2:2', 'rpza\tVideo']
        slate_codecs = []
        for item in slate_codecs_raw:
            if '\t' not in item:
                item = '\t'+item
            slate_codec_dct = {'label':item.split('\t')[1], 'value':item.split('\t')[0]}
            slate_codecs.append(slate_codec_dct)

        slate_colorspaces_raw = ['', 'default\tdefault', 'linear\tlinear', 'sRGB\tsRGB', 'rec709\trec709', 'Cineon\tCineon', 'Gamma1.8\tGamma1.8', 'Gamma2.2\tGamma2.2', 'Gamma2.4\tGamma2.4', 'Gamma2.6\tGamma2.6', 'Panalog\tPanalog', 'REDLog\tREDLog', 'ViperLog\tViperLog', 'AlexaV3LogC\tAlexaV3LogC', 'PLogLin\tPLogLin', 'SLog\tSLog', 'SLog1\tSLog1', 'SLog2\tSLog2', 'SLog3\tSLog3', 'CLog\tCLog', 'Log3G10\tLog3G10', 'Log3G12\tLog3G12', 'HybridLogGamma\tHybridLogGamma', 'Protune\tProtune', 'BT1886\tBT1886', 'st2084\tst2084']
        slate_colorspaces = []
        for item in slate_colorspaces_raw:
            if '\t' not in item:
                item = '\t'+item
            slate_colorspace_dct = {'label':item.split('\t')[1], 'value':item.split('\t')[0]}
            slate_colorspaces.append(slate_colorspace_dct)

        default_data_type = ['default\tdefault']
        mov_settings = ['----------\t----------', "{'file_type': 'mov', 'mov64_dnxhd_codec_profile': 'DNxHD 444 10-bit 440Mbit'}\tmov - DNxHD 444 10-bit 440Mbit", "{'file_type': 'mov', 'mov64_dnxhd_codec_profile': 'DNxHD 422 10-bit 220Mbit'}\tmov - DNxHD 422 10-bit 220Mbit", "{'file_type': 'mov', 'mov64_dnxhd_codec_profile': 'DNxHD 422 8-bit 220Mbit'}\tmov - DNxHD 422 8-bit 220Mbit", "{'file_type': 'mov', 'mov64_dnxhd_codec_profile': 'DNxHD 422 8-bit 145Mbit'}\tmov - DNxHD 422 8-bit 145Mbit", "{'file_type': 'mov', 'mov64_dnxhd_codec_profile': 'DNxHD 422 8-bit 36Mbit'}\tmov - DNxHD 422 8-bit 36Mbit"]
        exr_settings = ['----------\t----------', "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'none'}\texr - 16 bit half - none", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'Zip (1 scanline)'}\texr - 16 bit half - Zip (1 scanline)", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'Zip (16 scanlines)'}\texr - 16 bit half - Zip (16 scanlines)", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'PIZ Wavelet (32 scanlines)'}\texr - 16 bit half - PIZ Wavelet (32 scanlines)", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'RLE'}\texr - 16 bit half - RLE", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'B44'}\texr - 16 bit half - B44", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'B44A'}\texr - 16 bit half - B44A", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'DWAA'}\texr - 16 bit half - DWAA", "{'file_type': 'exr', 'datatype': '16 bit half', 'compression': 'DWAB'}\texr - 16 bit half - DWAB", '----------\t----------', "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'none'}\texr - 32 bit float - none", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'Zip (1 scanline)'}\texr - 32 bit float - Zip (1 scanline)", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'Zip (16 scanlines)'}\texr - 32 bit float - Zip (16 scanlines)", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'PIZ Wavelet (32 scanlines)'}\texr - 32 bit float - PIZ Wavelet (32 scanlines)", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'RLE'}\texr - 32 bit float - RLE", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'B44'}\texr - 32 bit float - B44", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'B44A'}\texr - 32 bit float - B44A", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'DWAA'}\texr - 32 bit float - DWAA", "{'file_type': 'exr', 'datatype': '32 bit float', 'compression': 'DWAB'}\texr - 32 bit float - DWAB"]
        dpx_settings = ['----------\t----------', "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'user-defined'}\tdpx - 8 bit - user-defined", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'printing density'}\tdpx - 8 bit - printing density", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'linear'}\tdpx - 8 bit - linear", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'log'}\tdpx - 8 bit - log", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'unspecified video'}\tdpx - 8 bit - unspecified video", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'SMPTE 240M'}\tdpx - 8 bit - SMPTE 240M", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'CCIR 709-1'}\tdpx - 8 bit - CCIR 709-1", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'CCIR 601-2 system B/G'}\tdpx - 8 bit - CCIR 601-2 system B/G", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'CCIR 601-2 system M'}\tdpx - 8 bit - CCIR 601-2 system M", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'NTSC'}\tdpx - 8 bit - NTSC", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'PAL'}\tdpx - 8 bit - PAL", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'Z linear'}\tdpx - 8 bit - Z linear", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': 'Z homogeneous'}\tdpx - 8 bit - Z homogeneous", "{'file_type': 'dpx', 'datatype': '8 bit', 'transfer': '(auto detect)'}\tdpx - 8 bit - (auto detect)", '----------\t----------', "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'user-defined'}\tdpx - 10 bit - user-defined", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'printing density'}\tdpx - 10 bit - printing density", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'linear'}\tdpx - 10 bit - linear", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'log'}\tdpx - 10 bit - log", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'unspecified video'}\tdpx - 10 bit - unspecified video", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'SMPTE 240M'}\tdpx - 10 bit - SMPTE 240M", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'CCIR 709-1'}\tdpx - 10 bit - CCIR 709-1", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'CCIR 601-2 system B/G'}\tdpx - 10 bit - CCIR 601-2 system B/G", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'CCIR 601-2 system M'}\tdpx - 10 bit - CCIR 601-2 system M", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'NTSC'}\tdpx - 10 bit - NTSC", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'PAL'}\tdpx - 10 bit - PAL", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'Z linear'}\tdpx - 10 bit - Z linear", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': 'Z homogeneous'}\tdpx - 10 bit - Z homogeneous", "{'file_type': 'dpx', 'datatype': '10 bit', 'transfer': '(auto detect)'}\tdpx - 10 bit - (auto detect)", '----------\t----------', "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'user-defined'}\tdpx - 12 bit - user-defined", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'printing density'}\tdpx - 12 bit - printing density", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'linear'}\tdpx - 12 bit - linear", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'log'}\tdpx - 12 bit - log", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'unspecified video'}\tdpx - 12 bit - unspecified video", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'SMPTE 240M'}\tdpx - 12 bit - SMPTE 240M", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'CCIR 709-1'}\tdpx - 12 bit - CCIR 709-1", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'CCIR 601-2 system B/G'}\tdpx - 12 bit - CCIR 601-2 system B/G", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'CCIR 601-2 system M'}\tdpx - 12 bit - CCIR 601-2 system M", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'NTSC'}\tdpx - 12 bit - NTSC", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'PAL'}\tdpx - 12 bit - PAL", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'Z linear'}\tdpx - 12 bit - Z linear", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': 'Z homogeneous'}\tdpx - 12 bit - Z homogeneous", "{'file_type': 'dpx', 'datatype': '12 bit', 'transfer': '(auto detect)'}\tdpx - 12 bit - (auto detect)", '----------\t----------', "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'user-defined'}\tdpx - 16 bit - user-defined", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'printing density'}\tdpx - 16 bit - printing density", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'linear'}\tdpx - 16 bit - linear", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'log'}\tdpx - 16 bit - log", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'unspecified video'}\tdpx - 16 bit - unspecified video", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'SMPTE 240M'}\tdpx - 16 bit - SMPTE 240M", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'CCIR 709-1'}\tdpx - 16 bit - CCIR 709-1", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'CCIR 601-2 system B/G'}\tdpx - 16 bit - CCIR 601-2 system B/G", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'CCIR 601-2 system M'}\tdpx - 16 bit - CCIR 601-2 system M", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'NTSC'}\tdpx - 16 bit - NTSC", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'PAL'}\tdpx - 16 bit - PAL", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'Z linear'}\tdpx - 16 bit - Z linear", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': 'Z homogeneous'}\tdpx - 16 bit - Z homogeneous", "{'file_type': 'dpx', 'datatype': '16 bit', 'transfer': '(auto detect)'}\tdpx - 16 bit - (auto detect)"]
        jpg_settings = ['----------\t----------', "{'file_type': 'jpeg', '_jpeg_sub_sampling': '4:1:1'}\tjpeg - 4:1:1", "{'file_type': 'jpeg', '_jpeg_sub_sampling': '4:2:2'}\tjpeg - 4:2:2", "{'file_type': 'jpeg', '_jpeg_sub_sampling': '4:4:4'}\tjpeg - 4:4:4"]
        png_settings = ['----------\t----------', "{'file_type': 'png', 'datatype': '8 bit'}\tpng - 8 bit", "{'file_type': 'png', 'datatype': '16 bit'}\tpng - 16 bit"]
        tga_settings = ['----------\t----------', "{'file_type': 'targa', 'compression': 'none'}\ttarga - none", "{'file_type': 'targa', 'compression': 'RLE'}\ttarga - RLE"]
        tif_settings = ['----------\t----------', "{'file_type': 'tiff', 'datatype': '8 bit', 'compression': 'none'}\ttiff - 8 bit - none", "{'file_type': 'tiff', 'datatype': '8 bit', 'compression': 'PackBits'}\ttiff - 8 bit - PackBits", "{'file_type': 'tiff', 'datatype': '8 bit', 'compression': 'LZW'}\ttiff - 8 bit - LZW", "{'file_type': 'tiff', 'datatype': '8 bit', 'compression': 'Deflate'}\ttiff - 8 bit - Deflate", '----------\t----------', "{'file_type': 'tiff', 'datatype': '16 bit', 'compression': 'none'}\ttiff - 16 bit - none", "{'file_type': 'tiff', 'datatype': '16 bit', 'compression': 'PackBits'}\ttiff - 16 bit - PackBits", "{'file_type': 'tiff', 'datatype': '16 bit', 'compression': 'LZW'}\ttiff - 16 bit - LZW", "{'file_type': 'tiff', 'datatype': '16 bit', 'compression': 'Deflate'}\ttiff - 16 bit - Deflate", '----------\t----------', "{'file_type': 'tiff', 'datatype': '32 bit float', 'compression': 'none'}\ttiff - 32 bit float - none", "{'file_type': 'tiff', 'datatype': '32 bit float', 'compression': 'PackBits'}\ttiff - 32 bit float - PackBits", "{'file_type': 'tiff', 'datatype': '32 bit float', 'compression': 'LZW'}\ttiff - 32 bit float - LZW", "{'file_type': 'tiff', 'datatype': '32 bit float', 'compression': 'Deflate'}\ttiff - 32 bit float - Deflate"]
        all_data_types = default_data_type + mov_settings + exr_settings + dpx_settings + jpg_settings + png_settings + tga_settings + tif_settings
        data_type_settings = []
        for item in all_data_types:
            data_type_dct = {'label':item.split('\t')[1], 'value':item.split('\t')[0]}
            data_type_settings.append(data_type_dct)

        slate_formats = []
        for item in list_of_resolutions:
            slate_res_dct = {'label':item[0], 'value':item[1]}
            slate_formats.append(slate_res_dct)

        slate_types = []
        list_of_slate_types = ['offline\toffline', 'online\tonline', 'mattes\tmattes', 'review\treview']
        for item in list_of_slate_types:
            if '\t' not in item:
                item = '\t'+item
            slate_types_dct = {'label':item.split('\t')[1], 'value':item.split('\t')[0]}
            slate_types.append(slate_types_dct)

        slate_names = []
        list_of_slate_names = ['something\tsomething']
        for item in list_of_slate_names:
            if '\t' not in item:
                item = '\t'+item
            slate_names_dct = {'label':item.split('\t')[1], 'value':item.split('\t')[0]}
            slate_names.append(slate_names_dct)


        slate_settings = [{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'value': '<i><b>SLATE SETTINGS</b></i>',
                    'type': 'label'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': '<b><font color="green">Slate Name</font></b>',
                    'type': 'text',
                    'value': 'Type a new name or choose from existing...',
                    'data' : '',
                    'name': 'slate_name'
                },{
                    'label': '<b><font color="green">Slate Type</font></b>',
                    'type': 'enumerator',
                    'value': 'offline',#slate_types[0]['label'],
                    'data' : slate_types,
                    'name': 'slate_type'
                },{
                    'label': ' + <i>Slate Codec</i>',
                    'type': 'enumerator',
                    'value': slate_codecs[9]['value'],#'Avid DNxHD Codec',#proj['custom_attributes']['slate_codec_offline'],
                    'data' : slate_codecs,
                    'name': 'slate_codec'
                },{
                    'label': ' + <i>Slate Format</i>',
                    'type': 'enumerator',
                    'value': slate_formats[6]['value'],#'HD_1080  1920 x 1080',#proj['custom_attributes']['slate_format_offline'],
                    'data' : slate_formats,
                    'name': 'slate_format'
                },{
                    'label': ' + <i>Slate Output</i>',
                    'type': 'text',
                    'value': '{defaultoutput}/{slatename}/{codec}/{assetname}.mov',#proj['custom_attributes']['slate_output_offline'],
                    'name': 'slate_output'
                },{
                    'label': ' + <i>Slate Template</i>',
                    'type': 'enumerator',
                    'name': 'slate_template',
                    'data': template_items,
                    'value': 'Generic_Slate_MOV.nk',#proj['custom_attributes']['offline_slate_template']
                },{
                    'label': '<font color="yellow"> + <i>Colorspace In</i><font>',
                    'type': 'enumerator',
                    'name': 'slate_colorspace_in',
                    'data': slate_colorspaces,
                    'value': 'sRGB',#proj['custom_attributes']['slate_colorspace_in_offline']
                },{
                    'label': '<font color="yellow"> + <i>Colorspace Out</i><font>',
                    'type': 'enumerator',
                    'name': 'slate_colorspace_out',
                    'data': slate_colorspaces,
                    'value': 'sRGB',#proj['custom_attributes']['slate_colorspace_out_offline']
                },{
                    'label': '<font color="orange"> + <i>Data Type</i><font>',
                    'type': 'enumerator',
                    'name': 'slate_data_type',
                    'data': data_type_settings,
                    'value': data_type_settings[0]['value']#'default',#proj['custom_attributes']['slate_data_type_offline']
                },{
                    'label': '<font color="pink"> + <i>Slate Frame</i></font>',
                    'type': 'boolean',
                    'value': True, #proj['custom_attributes']['offline_slate_frame'],
                    'name': 'slate_slateframe'
                },{
                    'label': '<font color="pink"> + <i>Overlays</i></font>',
                    'type': 'boolean',
                    'value': True, #proj['custom_attributes']['offline_overlays'],
                    'name': 'slate_overlays'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': '<font color="green"><b>Copy Files for Client</b></font>',
                    'type': 'boolean',
                    'value': False,#proj['custom_attributes']['copy_files_for_client'],
                    'name': 'copy_files_for_client'
                },{
                    'label': ' + <i>Files Output</i>',
                    'type': 'text',
                    'value': '{defaultoutput}/{slatename}/{assetname}',#proj['custom_attributes']['slate_output_files'],
                    'name': 'slate_output_files'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': '<b>Rename assetname</b>',
                    'type': 'boolean',
                    'value': True,#proj['custom_attributes']['slate_rename_for_client'],
                    'name': 'rename_for_client'
                },{
                    'label': ' + <i>Rename with Tags</i>',
                    'type': 'text',
                    'value': '{project}{episode}_{sequence}_{shot}_v{version}',#proj['custom_attributes']['slate_rename_with_tags'],
                    'name': 'rename_text'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
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
                    'value': 'Client Review',#proj['custom_attributes']['slate_description_text'],
                    'name': 'description_text'
                },{
                    'label': 'Custom Text',
                    'type': 'text',
                    'value': '',#proj['custom_attributes']['slate_custom_text'],
                    'name': 'custom_text'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': '<font color="pink">Project Title</font>',
                    'type': 'enumerator',
                    'value': '{projectname}',#proj['custom_attributes']['slate_frame_project_title'],
                    'data' : slate_txt_positions,
                    'name': 'slate_frame_project_title'
                },{
                    'label': '<font color="pink">Slate Info</font>',
                    'type': 'enumerator',
                    'value': '{description} : {date}',#proj['custom_attributes']['slate_frame_description'],
                    'data' : slate_txt_positions,
                    'name': 'slate_frame_description'
                },{
                    'label': '<font color="pink">Shot Title</font>',
                    'type': 'enumerator',
                    'value': '{project}{episode}_{sequence}_{shot}',#proj['custom_attributes']['slate_frame_shot_title'],
                    'data' : slate_txt_positions,
                    'name': 'slate_frame_shot_title'
                },{
                    'label': '<font color="pink">Frame Range Info</font>',
                    'type': 'enumerator',
                    'value': '{duration} frames',#proj['custom_attributes']['slate_frame_range_info'],
                    'data' : slate_txt_positions,
                    'name': 'slate_frame_range_info'
                },{
                    'label': '<font color="pink">Timecode Info</font>',
                    'type': 'enumerator',
                    'value': '{timecode}',#proj['custom_attributes']['slate_frame_timecode_info'],
                    'data' : slate_txt_positions,
                    'name': 'slate_frame_timecode_info'
                },{
                    'label': '<font color="pink">Version Info</font>',
                    'type': 'enumerator',
                    'value': '{task} Version {version}',#proj['custom_attributes']['slate_frame_version_info'],
                    'data' : slate_txt_positions,
                    'name': 'slate_frame_version_info'
                },{
                    'value': '<hr>',
                    'type': 'label'
                },{
                    'label': '<font color="pink">Top Left</font>',
                    'type': 'enumerator',
                    'value': '{logo}',#proj['custom_attributes']['slate_top_left'],
                    'data' : slate_txt_positions,
                    'name': 'slate_top_left'
                },{
                    'label': '<font color="pink">Top Right</font>',
                    'type': 'enumerator',
                    'value': '{date}',#proj['custom_attributes']['slate_top_right'],
                    'data' : slate_txt_positions,
                    'name': 'slate_top_right'
                },{
                    'label': '<font color="pink">Bottom Left</font>',
                    'type': 'enumerator',
                    'value': '{assetname}',#proj['custom_attributes']['slate_bottom_left'],
                    'data' : slate_txt_positions,
                    'name': 'slate_bottom_left'
                },{
                    'label': '<font color="pink">Bottom Right</font>',
                    'type': 'enumerator',
                    'value': '{framecounter}',#proj['custom_attributes']['slate_bottom_right'],
                    'data' : slate_txt_positions,
                    'name': 'slate_bottom_right'
                },{
                    'label': '<font color="pink">Top Center</font>',
                    'type': 'enumerator',
                    'value': '{none}',#proj['custom_attributes']['slate_top_center'],
                    'data' : slate_txt_positions,
                    'name': 'slate_top_center'
                },{
                    'label': '<font color="pink">Bottom Center</font>',
                    'type': 'enumerator',
                    'value': '{description}',#proj['custom_attributes']['slate_bottom_center'],
                    'data' : slate_txt_positions,
                    'name': 'slate_bottom_center'
                },{
                    'value': '<hr>',
                    'type': 'label'
                }]
                
        #Add the slate text options
        for item in slate_settings[::-1]:
            shot_items.insert(0, item)

        shot_items = slate_settings

        retUI = {'items': shot_items}

        if 'values' in data:

            # Do something with the values or return a new form.
            values = data['values']

            self.logger.info(u'Got values: {0}'.format(values))


            print values

            slate_name = values['slate_name']


            slate_folder = session.query('Folder where project.id is {} and name is "Slates"'.format(project_id)).all()
            if not slate_folder:
                slate_folder = session.create('Folder', {
                    'name': 'Slates',
                    'parent': proj
                })
            else:
                slate_folder = slate_folder[0]


            slate = session.create('Slate', {
                'name': slate_name,
                'parent': slate_folder
            })

            slate['custom_attributes']['slate_type']                         = values['slate_type']
            slate['custom_attributes']['slate_codec']                        = values['slate_codec']
            slate['custom_attributes']['slate_format']                       = values['slate_format']
            slate['custom_attributes']['slate_output']                       = values['slate_output']
            slate['custom_attributes']['slate_template']                     = values['slate_template']
            slate['custom_attributes']['slate_colorspace_in']                = values['slate_colorspace_in']
            slate['custom_attributes']['slate_colorspace_out']               = values['slate_colorspace_out']
            slate['custom_attributes']['slate_data_type']                    = values['slate_data_type']

            slate['custom_attributes']['slate_slateframe']                   = values['slate_slateframe']
            slate['custom_attributes']['slate_overlays']                     = values['slate_overlays']

            slate['custom_attributes']['slate_rename']                       = values['rename_for_client']
            slate['custom_attributes']['slate_assetname_rename']             = values['rename_text']

            slate['custom_attributes']['slate_overlays_description_text']    = values['description_text']
            slate['custom_attributes']['slate_overlays_custom_text']         = values['custom_text']

            slate['custom_attributes']['slate_overlays_top_left']            = values['slate_top_left']
            slate['custom_attributes']['slate_overlays_top_right']           = values['slate_top_right']
            slate['custom_attributes']['slate_overlays_top_center']          = values['slate_top_center']
            slate['custom_attributes']['slate_overlays_bottom_left']         = values['slate_bottom_left']
            slate['custom_attributes']['slate_overlays_bottom_right']        = values['slate_bottom_right']
            slate['custom_attributes']['slate_overlays_bottom_center']       = values['slate_bottom_center']

            slate['custom_attributes']['slate_slateframe_project_title']     = values['slate_frame_project_title']
            slate['custom_attributes']['slate_slateframe_description']       = values['slate_frame_description']
            slate['custom_attributes']['slate_slateframe_shot_title']        = values['slate_frame_shot_title']
            slate['custom_attributes']['slate_slateframe_range_info']        = values['slate_frame_range_info']
            slate['custom_attributes']['slate_slateframe_timecode_info']     = values['slate_frame_timecode_info']
            slate['custom_attributes']['slate_slateframe_version_info']      = values['slate_frame_version_info']

            session.commit()

            retSuccess = {
                'success': True,
                'message': 'Slate {} created under {}'.format(slate_name, proj['full_name'])
            }

            return retSuccess

        return retUI

        
def register(session, **kw):
    '''Register plugin.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    action = CreateSlate(session)
    action.register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    register(session)

    # Wait for events.
    session.event_hub.wait()