'''
    googledrive.py module
        - all functions responsible of downloading and uploading checkpoints are safe
        to use with any kind of checkpoint (observation or jobs)
'''

import sys
from typing import List
from misc import make_location
from pydrive.files import GoogleDriveFile
import os
from constants import APPDATA_PATH, CHECKPOINT_TAG, GOOGLE_CREDENTIALS_FILE
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


def connect_and_save_credentials():
    auth = GoogleAuth()
    auth.CommandLineAuth()
    auth.SaveCredentialsFile(GOOGLE_CREDENTIALS_FILE)


def connect_drive():
    auth = GoogleAuth()
    auth.LoadCredentialsFile(GOOGLE_CREDENTIALS_FILE)
    return GoogleDrive(auth)


def download_checkpoint_from_drive(checkpoint_drive:GoogleDriveFile, drive=None):

    if drive==None:
        drive = connect_drive()

    # query from drive for checkpoint folder id
    folder_name = checkpoint_drive['title'].split('.')[0]
    query = "title = '%s' and trashed=false"%(folder_name)
    folders = drive.ListFile({'q': query}).GetList()

    if len(folders) > 1:print('[WARNING] XXX multiple folder with same name exist XXX')
    folder = folders[0]

    make_location(APPDATA_PATH + folder_name + '/')

    file_to_download = drive.ListFile({'q': f"'{folder['id']}' in parents"}).GetList()

    total = len(file_to_download)
    step = 20
    done = 0
    progress = 0
    print('|' + '-'*step + '|', end='\r')

    for google_file in file_to_download:
        google_file.GetContentFile(APPDATA_PATH + folder_name + '/' + google_file['title'])

        done += 1
        progress = done*step//total
        print('|' + '#'*progress + '-'*(step-progress) + '| %d/%d'%(done, total), end='\r')

    print('\nDone downloading folder')

    checkpoint_drive.GetContentFile(checkpoint_drive['title'])


def store_checkpoint_to_cloud(objects_file, protected_directory:str, only_objectfile=False, drive=None):

    if drive == None:
        drive = connect_drive()

    obj_file_drive = drive.CreateFile({'title': objects_file})
    obj_file_drive.SetContentFile(objects_file)
    obj_file_drive.Upload()

    if only_objectfile:return

    folder = drive.CreateFile({'title': protected_directory.split('/')[-2], "mimeType": "application/vnd.google-apps.folder"})
    folder.Upload()
    file_to_upload = [u for u in os.listdir(protected_directory)]
    total = len(file_to_upload)
    step = 20
    done = 0
    progress = 0
    print('|' + '-'*step + '|', end='\r')

    for f in file_to_upload:
        f_drive = drive.CreateFile({'title':f , 'parents': [{'id': folder['id']}]})
        f_drive.SetContentFile(protected_directory + f)
        f_drive.Upload()

        done += 1
        progress = done*step//total

        print('|' + '#'*progress + '-'*(step-progress) + '| %d/%d'%(done, total), end='\r')
    
    print('\ndone uploading')
    return drive


def query_download_checkpoint(checkpoint=None, filter_resumable=False) -> GoogleDriveFile:

    drive = connect_drive()

    checkpoint_drive: GoogleDriveFile
    result = []
    for checkpoint_drive in drive.ListFile({'q': f"title contains '{CHECKPOINT_TAG}'"}).GetList():
        if checkpoint and checkpoint_drive['title'] == checkpoint:
            return checkpoint_drive, drive
        else:
            if filter_resumable:
                if checkpoint_drive['title'][0] == 'R':
                    result.append(checkpoint_drive)
            else:result.append(checkpoint_drive)

    if checkpoint:
        raise FileNotFoundError
    return result, drive
    

def store_single_file(single_file:str, drive=None):

    if drive == None:
        drive = connect_drive()
    
    drive_file = drive.CreateFile({'title': single_file.split('/')[-1]})
    drive_file.SetContentFile(single_file)
    drive_file.Upload()


if __name__ == '__main__':
    # WARNING: this part of code is functional (no testing)
    connect_and_save_credentials()

    # directory_name = APPDATA_PATH + name.split('.')[0] + '/'
    # print(directory_name.split('/')[-2])
    # store_checkpoint_to_cloud(name, directory_name, only_objectfile=True)
    # drive = connect_drive()
    # connect_and_save_credentials()

