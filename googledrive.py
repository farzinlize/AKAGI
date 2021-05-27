'''
    googledrive.py module
        - all functions responsible of downloading and uploading checkpoints are safe
        to use with any kind of checkpoint (observation or jobs)
'''

import io
import sys
from datetime import datetime
from typing import List
from misc import bytes_to_int, int_to_bytes, make_location
from pydrive.files import GoogleDriveFile
import os
from constants import APPDATA_PATH, CHECKPOINT_TAG, GOOGLE_CREDENTIALS_FILE, INT_SIZE
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

CLOUD_FILE_SIZE_LIMIT = 100 * (2**20)

def connect_and_save_credentials():
    auth = GoogleAuth()
    auth.CommandLineAuth()
    auth.SaveCredentialsFile(GOOGLE_CREDENTIALS_FILE)


def connect_drive():
    auth = GoogleAuth()
    auth.LoadCredentialsFile(GOOGLE_CREDENTIALS_FILE)
    return GoogleDrive(auth)


def download_checkpoint_from_drive(checkpoint_drive:GoogleDriveFile, drive=None, clear_cloud=False):

    if drive==None:
        drive = connect_drive()

    since = datetime.now()

    # query from drive for checkpoint folder id
    compressed_name = checkpoint_drive['title'].split('.')[0]
    compressed_files = drive.ListFile({'q': f"title = '{compressed_name}.bin' and trashed=false"}).GetList()


    if len(compressed_files) > 1:print('[WARNING] XXX multiple compressed file with the same name exist XXX')
    compressed:GoogleDriveFile = compressed_files[0]
    compressed.GetContentFile('temp.bin')

    protected_directory = APPDATA_PATH + compressed_name + '/'
    make_location(protected_directory)

    with open('temp.bin', 'rb') as compressed_data:

        filename_size = bytes_to_int(compressed_data.read(INT_SIZE))
        while filename_size:
            filename = str(compressed_data.read(filename_size), encoding='ascii')
            with open(protected_directory + filename, 'wb') as protected:
                protected.write(compressed_data.read(bytes_to_int(compressed_data.read(INT_SIZE))))
            filename_size = bytes_to_int(compressed_data.read(INT_SIZE))

        assert len(compressed_data.read()) == 0

    os.remove('temp.bin')

    # object file
    name = checkpoint_drive['title']
    checkpoint_drive.GetContentFile(name)
    
    print('\n[CLOUD] download is done in %s time'%(datetime.now()-since))

    if clear_cloud:
        compressed.Delete()
        checkpoint_drive.Delete()

    return name


def store_checkpoint_to_cloud(objects_file, protected_directory:str, only_objectfile=False, drive=None):

    if drive == None:
        drive = connect_drive()

    since = datetime.now()

    obj_file_drive = drive.CreateFile({'title': objects_file})
    obj_file_drive.SetContentFile(objects_file)
    obj_file_drive.Upload()

    if only_objectfile:return

    compressed = b''
    for f in os.listdir(protected_directory):
        with open(protected_directory + f, 'rb') as data:
            content = data.read()
            compressed += int_to_bytes(len(f)) + bytes(f, 'ascii')
            compressed += int_to_bytes(len(content)) + content

    print(f'[CLOUD] compressing directory - total bytes count: {len(compressed)}')

    if len(compressed) > CLOUD_FILE_SIZE_LIMIT:
        print('[UPLOAD] WARNING: starting to upload a large file')
        # TODO: several compressed file instead of only one if necessary 

    compressed_drive = drive.CreateFile({'title': protected_directory.split('/')[-2]+'.bin', "mimeType": "application/octet-stream"})
    compressed_drive.content = io.BytesIO(compressed)
    compressed_drive.Upload()
    
    print('\n[CLOUD] upload is done in %s time'%(datetime.now()-since))
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
    
    # drive = connect_drive()
    # store_checkpoint_to_cloud('ENCODE_HAIB_GM12878_SRF_peak_f5-6_d1-1.checkpoint', 'appdata/ENCODE_HAIB_GM12878_SRF_peak_f5-6_d1-1/')
    # f, drive = query_download_checkpoint(checkpoint='ENCODE_HAIB_GM12878_SRF_peak_f5-6_d1-1.checkpoint')
    # download_checkpoint_from_drive(f, drive=drive, clear_cloud=True)
    # directory_name = APPDATA_PATH + name.split('.')[0] + '/'
    # print(directory_name.split('/')[-2])
    # store_checkpoint_to_cloud(name, directory_name, only_objectfile=True)
    # drive = connect_drive()
    # connect_and_save_credentials()

