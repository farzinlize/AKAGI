import sys
from misc import make_location
from pydrive.files import GoogleDriveFile
from checkpoint import checkpoint_name
import os
from constants import APPDATA_PATH, GOOGLE_CREDENTIALS_FILE
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


def download_checkpoint_from_drive(checkpoint:str, object_file:GoogleDriveFile, drive=None):

    if drive==None:
        drive = connect_drive()

    # query from drive for checkpoint folder id
    folder_name = checkpoint.split('.')[0]
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

    object_file.GetContentFile(checkpoint)


def store_checkpoint_to_cloud(objects_file, protected_directory:str, only_objectfile=False):

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


def query_download_checkpoint(checkpoint_name) -> GoogleDriveFile:

    drive = connect_drive()

    checkpoint: GoogleDriveFile
    for checkpoint in drive.ListFile({'q': "title contains '.checkpoint'"}).GetList():
        if checkpoint['title'] == checkpoint_name:return checkpoint, drive
    

if __name__ == '__main__':
    # WARNING: this part of code is functional (no testing)
    connect_and_save_credentials()

    # name = checkpoint_name('hmchipdata/Human_hg18_peakcod/ENCODE_HAIB_GM12878_SRF_peak', [5, 6], [1, 1], True)
    # directory_name = APPDATA_PATH + name.split('.')[0] + '/'
    # print(directory_name.split('/')[-2])
    # store_checkpoint_to_cloud(name, directory_name, only_objectfile=True)
    # drive = connect_drive()
    # connect_and_save_credentials()

