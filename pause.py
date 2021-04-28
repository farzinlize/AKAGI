from onSequence import OnSequenceDistribution
from googledrive import download_checkpoint_from_drive, query_download_checkpoint, store_checkpoint_to_cloud, store_single_file
from checkpoint import save_checkpoint, unique_checkpoint_name
from constants import TIMER_CHAINING_HOURS
from datetime import datetime, timedelta


def save_the_rest(works, on_sequence:OnSequenceDistribution, cloud=True):

    # grant a free name for checkpoint
    checkpoint = unique_checkpoint_name()

    # store objects and protect their data under directory
    directory = save_checkpoint(works, checkpoint, on_sequence=on_sequence)

    # upload to cloud
    if cloud:store_checkpoint_to_cloud(checkpoint, directory)


time_has_ended = lambda since:(datetime.now() - since) > timedelta(hours=TIMER_CHAINING_HOURS)


def resume_any_cloud():

    # query for resumable checkpoints
    resumable_checkpoints, drive = query_download_checkpoint(filter_resumable=True)
    if len(resumable_checkpoints) == 0:
        print('[PAUSE] found noting to resume')
        return

    # pick the first one in list and download
    checkpoint_drive = resumable_checkpoints[0]
    download_checkpoint_from_drive(checkpoint_drive, drive)
    return checkpoint_drive['title']


if __name__ == '__main__':
    s = datetime.now()
    # t = time_has_ended(datetime.now())