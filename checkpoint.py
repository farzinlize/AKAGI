from datetime import datetime
import pickle
from typing import List
from pymongo import MongoClient
import os, mongo
from FoundMap import MemoryMap, ReadOnlyMap
from TrieFind import ChainNode, initial_chainNodes
from constants import CHECKPOINT_TAG, COLLECTION, DATABASE_LOG, DATABASE_NAME, LABEL, LOCK_PREFIX, MONGO_ID

'''
    saving motifs using their serialization methode AND on_sequence object using pickle
        UPDATE: motifs foundmap are considered to be stored at a collection with the same name as object_file

        -> change_collection=True: moving each foundmap of motifs to another collection name as objects_file (without extention)
        -> move=True: clear foundmaps from previously given motifs an replace new ones (in case of changing collection)
        -> if object_file ends with checkpoint extention: create a file containing objects
        -> resumable=True: adding meta-information necessary for resuming (in case of creating object file)
            additional argument -> on_sequence, q, dataset_name
        -> compact=True: make objects file independent, saving all data on a single file (in case of creating object file)
'''
def save_checkpoint(motifs:List[ChainNode], 
                    objects_file:str, 
                    change_collection=False, 
                    move=True,
                    compact=False,
                    resumable=False, 
                    on_sequence=None, 
                    q=None, 
                    dataset_name=None, 
                    mongo_client=None):

    if change_collection:
        these_motifs = initial_chainNodes([(motif.label, motif.foundmap) for motif in motifs], objects_file.split('.')[0], mongo_client)
        if not isinstance(these_motifs, list):return these_motifs

        if move: # clear older foundmaps and replace new ones for previously given motifs
            for motif, newmotif in zip(motifs, these_motifs):
                motif.foundmap.clear()
                motif.foundmap = newmotif.foundmap
    
    # consider previously given motifs for furthur use
    else:these_motifs = motifs

    if objects_file.endswith(CHECKPOINT_TAG):
        with open(objects_file, 'wb') as f:

            # meta-data for resuming
            if resumable:
                pickle.dump(on_sequence, f)
                pickle.dump(q, f) 
                pickle.dump(dataset_name, f)

            # writing motifs and their binary information alongside them in one single file
            if compact:
                for motif in these_motifs:f.write(ChainNode(motif.label, MemoryMap(motif.foundmap.get_list())).to_byte())
            
            # save motifs as they are (data may depend on external databases)
            else:
                for motif in these_motifs:f.write(motif.to_byte())


# resumable files containing motifs plus additional data
def load_checkpoint_file(objects_file:str, resumable=False):
    
    if not os.path.isfile(objects_file):
        print("[CHECK-POINT] checkpoint doesn't exist")
        return None

    # collection_name = objects_file.split('.')[0]

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


'''
    generate observation name based on configuration
        returns name with or without checkpoint extention for file or collection use
'''
def observation_checkpoint_name(dataset: str, f, d, multilayer, extention=True):

    dataset_name = dataset.split('/')[-1]

    if multilayer:
        assert isinstance(d, list) and isinstance(f, list)
        name =  '%s_f%s_d%s'%(dataset_name, '-'.join([str(a) for a in f]), '-'.join([str(a) for a in d]))
    else:
        assert isinstance(d, int) and isinstance(f, int)
        name = '%s_f%d_d%d'%(dataset_name, f, d)
    
    if extention:return name + CHECKPOINT_TAG
    else        :return name


# return a name based on time (with R suffix)
def unique_checkpoint_name():
    checkpoint = datetime.now().strftime(f"R%Y-%m-%d(%H-%M-%S){CHECKPOINT_TAG}")
    while os.path.isfile(checkpoint):
        checkpoint = datetime.now().strftime(f"R%Y-%m-%d(%H-%M-%S){CHECKPOINT_TAG}")
    return checkpoint


def query_resumable_checkpoints() -> str:
    return [checkpoint for checkpoint in os.listdir() if checkpoint.startswith('R') and checkpoint.endswith(CHECKPOINT_TAG)]


def remove_checkpoint(checkpoint:str, locked=False):
    if locked:os.remove(LOCK_PREFIX + checkpoint)
    else     :os.remove(checkpoint)


def lock_checkpoint(checkpoint):
    with open(checkpoint, 'rb') as data:
        databytes = data.read()
    with open(LOCK_PREFIX + checkpoint, 'wb') as locked:
        locked.write(databytes)
    os.remove(checkpoint)


def load_collection(collection_name, client:MongoClient=None) -> List[ChainNode]:

    if not client:client = mongo.get_client();should_close = True
    else                                     :should_close = False

    collection = client[DATABASE_NAME][collection_name]
    items_or_error = mongo.safe_operation(collection, COLLECTION)
    if should_close:client.close()

    if not isinstance(items_or_error, list):
        with open(DATABASE_LOG, 'a') as log:log.write(f'[MONGO][LOAD] error: {items_or_error}\n')
        return items_or_error
    
    return [ChainNode(item[LABEL], ReadOnlyMap(collection_name, item[MONGO_ID])) for item in items_or_error]


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