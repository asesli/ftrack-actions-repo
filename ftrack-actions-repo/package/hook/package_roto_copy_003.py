import os, sys
import subprocess
from shutil import copyfile

print('Python Version: ', sys.version)

progress = 0
progress_inc = 0

package_items_dict = sys.argv[1]
package_items_dict = eval(package_items_dict)
#package_items_dict = {'CHM201_029_010':[{'Q:/Charmed_S2/CHM201/03_COORDINATION/RotoFrames/CHM201_029_010_ELEM02_O.1003.jpeg': u'Q:/Charmed_S2/CHM201/03_COORDINATION/Rotopackage_2019-11-26'}, {'Q:/Charmed_S2/CHM201/03_COORDINATION/RotoFrames/CHM201_029_010_ELEM02_O.1002.jpeg': u'Q:/Charmed_S2/CHM201/03_COORDINATION/Rotopackage_2019-11-26'}, {'Q:/Charmed_S2/CHM201/03_COORDINATION/RotoFrames/CHM201_029_010_ELEM02_O.1001.jpeg': u'Q:/Charmed_S2/CHM201/03_COORDINATION/Rotopackage_2019-11-26'}, {'Q:/Charmed_S2/CHM201/01_PLATES/CHM201_029_010/ELEM02/ELEM02_O/01_EXRS': u'Q:/Charmed_S2/CHM201/03_COORDINATION/Rotopackage_2019-11-26/CHM201_029_010'}, {'Q:/Charmed_S2/CHM201/01_PLATES/CHM201_029_010/ELEM02/ELEM02_O/02_FULL_RES_JPEGS': u'Q:/Charmed_S2/CHM201/03_COORDINATION/Rotopackage_2019-11-26/CHM201_029_010'}]}

def copyFilesIntoFolders(list_of_dics):
    #files must be a list
    #folder is a str

    global progress
    global progress_inc

    for ff in list_of_dics:

        folder = ff['folder']
        files  = ff['files']

        if folder[-1]!='/':
            folder +='/'

        for file in files:
            filename = file.split('/')[-1]
            new_file = folder + filename

            #print file
            #print '>',new_file

            if not os.path.exists(folder):
                os.makedirs(folder)

            copyfile(file, new_file)
            progress += progress_inc
            #print("Progress: {}%".format(round(progress,2)))
            print("Progress: {}%".format(int(progress)))


def copyFilesAndFolders(dic):

    global progress_inc

    img_types = ['jpg', 'jpeg', 'dpx', 'exr', 'tif', 'tiff', 'png', 'tga', 'targa']

    shot_code = dic.keys()[0]
    items = dic[shot_code]

    all_files = 0

    files_and_folders = []

    #print progress_inc

    for dic in items:

        files_folders = dic.keys()[0]
        output = dic.values()[0]
        files = []

        if os.path.isfile(files_folders):
            #files and folders is a file so append it to files.
            copy_into = output
            files = [files_folders]
            all_files += len(files)
            ff = {'folder':copy_into, 'files':files}
            files_and_folders.append(ff)
            #copyFilesIntoFolders(copy_into,files)


        elif os.path.isdir(files_folders):
            #print files_folders
            #files and folders is a folder so append all the image items inside of its subdirs to files.

            for p, d, f in os.walk(files_folders):
                [files.append(os.path.join(p,file).replace(os.sep, '/')) for file in f if file.split('.')[-1] in img_types]

            copy_into = output+files[0].split(shot_code)[1]

            all_files += len(files)
            ff = {'folder':copy_into, 'files':files}
            files_and_folders.append(ff)
            #copyFilesIntoFolders(copy_into,files)


    progress_inc = 100.0/all_files
    #print all_files

    copyFilesIntoFolders(files_and_folders)



copyFilesAndFolders(package_items_dict)