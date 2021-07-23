from datetime import datetime
import pickle
import os
from constants import CHECKPOINT_TAG, LOCK_PREFIX
from TrieFind import ChainNode
from typing import List
from FoundMap import initial_readonlymaps

'''
    saving motifs using their serialization methode AND on_sequence object using pickle
        UPDATE: motifs foundmap are considered to be stored at a collection with the same name as object_file
'''
def save_checkpoint(motifs:List[ChainNode], objects_file:str, resumable=False, on_sequence=None, q=None, dataset_name=None, change_collection=False):

    if change_collection:
        newmaps = initial_readonlymaps([motif.foundmap for motif in motifs], objects_file.split('.')[0])
        if not isinstance(newmaps, list):return newmaps
        for motif, newmap in zip(motifs, newmaps):
            motif.foundmap.clear()
            motif.foundmap = newmap
            
    # write objects and protect their data under directory
    with open(objects_file, 'wb') as f:

        # save data needed for resuming
        if resumable:
            pickle.dump(on_sequence, f)
            pickle.dump(q, f) 
            pickle.dump(dataset_name, f)

        # save motifs
        for motif in motifs:
            f.write(motif.to_byte())


def load_checkpoint(objects_file:str, resumable=False):
    
    if not os.path.isfile(objects_file):
        print("[CHECK-POINT] checkpoint doesn't exist")
        return None

    collection_name = objects_file.split('.')[0]

    motifs=[]
    with open(objects_file, 'rb') as f:

        if resumable:
            on_sequence =   pickle.load(f)
            q =             pickle.load(f)
            dataset_name =  pickle.load(f)

        item = ChainNode.byte_to_object(f, collection_name)
        while item:
            motifs.append(item)
            item = ChainNode.byte_to_object(f, collection_name)

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
    checkpoint = datetime.now().strftime(f"R%Y-%m-%d(%H-%M-%S){CHECKPOINT_TAG}")
    while os.path.isfile(checkpoint):
        checkpoint = datetime.now().strftime(f"R%Y-%m-%d(%H-%M-%S){CHECKPOINT_TAG}")
    return checkpoint


def query_resumable_checkpoints() -> str:
    return [checkpoint for checkpoint in os.listdir() if checkpoint.startswith('R') and checkpoint.endswith(CHECKPOINT_TAG)]


def remove_checkpoint(checkpoint:str, locked=False):
    if locked:filename = os.remove(LOCK_PREFIX + checkpoint)
    else     :filename = os.remove(checkpoint)



def lock_checkpoint(checkpoint):
    with open(checkpoint, 'rb') as data:
        databytes = data.read()
    with open(LOCK_PREFIX + checkpoint, 'wb') as locked:
        locked.write(databytes)
    os.remove(checkpoint)


if __name__ == '__main__':
    # name = observation_checkpoint_name('hmchipdata/Human_hg18_peakcod/ENCODE_HAIB_GM12878_SRF_peak', [3, 5], [0, 2], True)
    a = query_resumable_checkpoints()
    print(a)
    name = a[0]

    # name = unique_checkpoint_name()

    # motif1 = ChainNode('ACTG', FileMap(initial=[[0, 1],[[ExtraPosition(5, 3)],[ExtraPosition(8, 9)]]]))
    # motif2 = ChainNode('ACTGGGT', FileMap(initial=[[0, 2],[[ExtraPosition(7, 1)],[ExtraPosition(3, 8)]]]))

    # save_checkpoint([motif1, motif2], name)

    lock_checkpoint(name)
    remove_checkpoint(name, locked=True)

    # loaded_motifs = load_checkpoint(name)

    # motifs = load_checkpoint('test.test')
    # print()