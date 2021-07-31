from datetime import datetime
import pickle
from typing import List
from pymongo import MongoClient
import os, mongo
from FoundMap import ReadOnlyMap
from TrieFind import ChainNode, initial_chainNodes
from constants import CHECKPOINT_TAG, COLLECTION, DATABASE_LOG, DATABASE_NAME, LABEL, LOCK_PREFIX, MONGO_ID

'''
    saving motifs using their serialization methode AND on_sequence object using pickle
        UPDATE: motifs foundmap are considered to be stored at a collection with the same name as object_file
        
        flags --/
            change_collection=True: moving each foundmap of motifs to another collection name
            resumable=True: creating checkpoint file to recover motifs and additional data compact ready for resuming
                additional argument -> on_sequence, q, dataset_name
        --/
'''
def save_checkpoint(motifs:List[ChainNode], 
                    objects_file:str, 
                    change_collection=False, 
                    resumable=False, 
                    on_sequence=None, 
                    q=None, 
                    dataset_name=None, 
                    mongo_client=None):

    if change_collection:
        newchainnodes = initial_chainNodes([(motif.label, motif.foundmap) for motif in motifs], objects_file.split('.')[0], mongo_client)
        if not isinstance(newchainnodes, list):return newchainnodes
        for motif, newmotif in zip(motifs, newchainnodes):
            motif.foundmap.clear()
            motif.foundmap = newmotif.foundmap
            del newmotif
            
    if resumable:

        # save data needed for resuming
        with open(objects_file, 'wb') as f:
            pickle.dump(on_sequence, f)
            pickle.dump(q, f) 
            pickle.dump(dataset_name, f)

        # save motifs
        for motif in motifs:
            f.write(motif.to_byte())


# resumable files containing motifs plus additional data
def load_checkpoint_file(objects_file:str):
    
    if not os.path.isfile(objects_file):
        print("[CHECK-POINT] checkpoint doesn't exist")
        return None

    collection_name = objects_file.split('.')[0]

    motifs=[]
    with open(objects_file, 'rb') as f:

        on_sequence =   pickle.load(f)
        q =             pickle.load(f)
        dataset_name =  pickle.load(f)

        item = ChainNode.byte_to_object(f, collection_name)
        while item:
            motifs.append(item)
            item = ChainNode.byte_to_object(f, collection_name)

    return motifs, on_sequence, q, dataset_name


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


def load_collection(collection_name, client:MongoClient=None) -> List[ChainNode]:

    if not client:client = mongo.get_client()

    collection = client[DATABASE_NAME][collection_name]
    items_or_error = mongo.safe_operation(collection, COLLECTION)

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