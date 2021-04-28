from datetime import datetime
import pickle
import os
from misc import ExtraPosition, make_location
from FoundMap import FileMap
from constants import APPDATA_PATH, CHECKPOINT_TAG
from TrieFind import ChainNode
from typing import List

'''
    saving motifs using their serialization methode AND on_sequence object using pickle
    motif data on disk will be protected under a directory at:
        APPDATA_PATH/(object_file without dot tag)/
'''
def save_checkpoint(motifs:List[ChainNode], objects_file:str, resumable=False, on_sequence=None, q=None, dataset_name=None):

    # creating protected directory
    directory_name = APPDATA_PATH + objects_file.split('.')[0] + '/'
    make_location(directory_name)

    # write objects and protect their data under directory
    with open(objects_file, 'wb') as f:

        # save data needed for resuming
        if resumable:
            pickle.dump(on_sequence, f)
            pickle.dump(q, f) 
            pickle.dump(dataset_name, f)

        # save motifs
        for motif in motifs:
            f.write(motif.to_byte(protect=True, directory=directory_name))

    return directory_name


def load_checkpoint(objects_file, resumable=False):
    
    if not os.path.isfile(objects_file):
        print("[CHECK-POINT] checkpoint doesn't exist")
        return None

    motifs=[]
    with open(objects_file, 'rb') as f:

        if resumable:
            on_sequence =   pickle.load(f)
            q =             pickle.load(f)
            dataset_name =  pickle.load(f)

        item = ChainNode.byte_to_object(f)
        while item:
            motifs.append(item)
            item = ChainNode.byte_to_object(f)

    if resumable:
        return motifs, on_sequence, q, dataset_name
    return motifs


def observation_checkpoint_name(dataset: str, f, d, multilayer):

    dataset_name = dataset.split('/')[-1]

    if multilayer:
        assert isinstance(d, list) and isinstance(f, list)
        return '%s_f%s_d%s'%(dataset_name, '-'.join([str(a) for a in f]), '-'.join([str(a) for a in d])) + CHECKPOINT_TAG
    else:
        assert isinstance(d, int) and isinstance(f, int)
        return '%s_f%d_d%d'%(dataset_name, f, d) + CHECKPOINT_TAG


# return a name based on time (with R suffix)
def unique_checkpoint_name():
    checkpoint = datetime.now().strftime(f"R%Y-%m-%d(%H:%M:%S){CHECKPOINT_TAG}")
    while os.path.isfile(checkpoint):
        checkpoint = datetime.now().strftime(f"R%Y-%m-%d(%H:%M:%S){CHECKPOINT_TAG}")
    return checkpoint


if __name__ == '__main__':
    name = observation_checkpoint_name('hmchipdata/Human_hg18_peakcod/ENCODE_HAIB_GM12878_SRF_peak', [3, 5], [0, 2], True)

    motif1 = ChainNode('ACTG', FileMap(initial=[[0, 1],[[ExtraPosition(5, 3)],[ExtraPosition(8, 9)]]]))
    motif2 = ChainNode('ACTGGGT', FileMap(initial=[[0, 2],[[ExtraPosition(7, 1)],[ExtraPosition(3, 8)]]]))

    save_checkpoint([motif1, motif2], name)

    loaded_motifs = load_checkpoint(name)

    # motifs = load_checkpoint('test.test')
    # print()