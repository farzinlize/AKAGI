from onSequence import OnSequenceDistribution
from googledrive import download_checkpoint_from_drive, query_download_checkpoint, store_checkpoint_to_cloud, store_single_file
from checkpoint import save_checkpoint, unique_checkpoint_name
from constants import TIMER_CHAINING_HOURS
from datetime import datetime, timedelta


def save_the_rest(works, on_sequence:OnSequenceDistribution, q, dataset_name, cloud=True):

    # grant a free name for checkpoint
    checkpoint = unique_checkpoint_name()

    # store objects and protect their data under directory
    directory = save_checkpoint(works, checkpoint, resumable=True, on_sequence=on_sequence, q=q, dataset_name=dataset_name)

    # upload to cloud
    if cloud:store_checkpoint_to_cloud(checkpoint, directory)


def time_has_ended(since, hours):
    return (datetime.now() - since) > timedelta(hours=hours)


def resume_any_cloud():

    # query for resumable checkpoints
    resumable_checkpoints, drive = query_download_checkpoint(filter_resumable=True)
    if len(resumable_checkpoints) == 0:
        print('[PAUSE] found noting to resume')
        return

    # pick the first one in list and download
    checkpoint_drive = resumable_checkpoints[0]
    return download_checkpoint_from_drive(checkpoint_drive, drive, clear_cloud=True)


if __name__ == '__main__':
    s = datetime.now()
    # t = time_has_ended(datetime.now())