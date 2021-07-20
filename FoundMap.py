from random import randrange
from io import BufferedReader
from typing import List
from pymongo import MongoClient
from bson.objectid import ObjectId
from misc import Bytable, ExtraPosition, get_random_free_path, binary_add, bytes_to_int, int_to_bytes, make_location
import os, sys, mongo
from constants import APPDATA_PATH, BATCH_SIZE, BINARY_DATA, DATABASE_NAME, DISK_QUEUE_NAMETAG, END, FOUNDMAP_NAMETAG, ID_LENGTH, MONGO_ID, STR, DEL, INT_SIZE, FOUNDMAP_DISK, FOUNDMAP_MEMO, FOUNDMAP_MODE


'''
    Father structure for Found Map and its children described below:
        MemoryMap: saving data in python list structure (object version of found_list)
        FileMap: saving data in byte-file
'''
class FoundMap:

    # abstract functions
    def add_location(self, seq_id, position):raise NotImplementedError
    def get_q(self):raise NotImplementedError
    def get_sequences(self):raise NotImplementedError
    def get_positions(self):raise NotImplementedError
    def get_list(self) -> List[List]:raise NotImplementedError
    def clone(self): raise NotImplementedError
    def clear(self): raise NotImplementedError


    def instances_to_string_fastalike(self, label, sequences: List[str]):
        result = '>pattern\n%s\n>instances\n'%(label)
        bundle = self.get_list()
        for index, seq_id in enumerate(bundle[0]):
            position: ExtraPosition
            for position in bundle[1][index]:
                end_index = position.end_position()
                start_index = position.start_position
                
                result += '%d,%d,%s,%d\n'%(
                    seq_id, 
                    (start_index-len(sequences[seq_id])), 
                    sequences[seq_id][start_index:end_index], 
                    (end_index-start_index))
        return result


# static foundmap choose based on global variable of FOUNDMAP_MODE
def get_foundmap(batch_limit=BATCH_SIZE, foundmap_type=FOUNDMAP_MODE) -> FoundMap:
    if foundmap_type == FOUNDMAP_DISK:return FileMap(batch_limit=batch_limit)
    elif foundmap_type == FOUNDMAP_MEMO:return MemoryMap()
    else:raise Exception('[FoundMap] FOUNDMAP_MODE variable unrecognized')


class MemoryMap(FoundMap):

    def __init__(self):self.found_list = [[],[]]

    def add_location(self, seq_id, position):
        self.found_list = binary_special_add(self.found_list, seq_id, position)

    def get_q(self):return len(self.found_list[0])
    def get_sequences(self):return self.found_list[0]
    def get_positions(self):return self.found_list[1]
    def get_list(self):return self.found_list

    def __str__(self) -> str:
        return str(self.found_list)

    def clone(self):
        return MemoryMap([self.found_list[0][:]] + [self.found_list[1][:]])

    def turn_to_filemap(self):
        return FileMap().dump_list(self.found_list)


class FileMap(FoundMap, Bytable):

    class FileHandler:

        '''
            Provides memory-disk transform using byte stream files for saving on disk
            functions:
                init -> new born object loads data from its file
                update -> updating data in memory using batch (temporary data saved on memory)
                save -> transform data into byte stream and save it on file

            [PROTOCOL] byte stream portocol descried here:
                int value -> fixed integer size at constants module (INT_SIZE)
                vectors -> size of vectors are restored at the begining of each
                special bytes -> special bytes are consider to prevent file errors defined at constants 
                    module (STR `start`, END `end`, DEL `delimitter`)
        '''
        def __init__(self, path, dont_read=False):

            self.path = path

            self.sequences = []
            self.positions = []

            if dont_read:return

            with open(path, 'rb') as mapfile:

                # check header byte signature
                assert mapfile.read(1) == STR

                # reading sequence vector
                for _ in range(bytes_to_int(mapfile.read(INT_SIZE))):
                    self.sequences += [bytes_to_int(mapfile.read(INT_SIZE))]
                    
                assert mapfile.read(1) == DEL

                # reading 2D-position vector
                for _ in range(len(self.sequences)):
                    positions = []
                    for _ in range(bytes_to_int(mapfile.read(INT_SIZE))):
                        position = bytes_to_int(mapfile.read(INT_SIZE))
                        size = bytes_to_int(mapfile.read(INT_SIZE))
                        positions += [ExtraPosition(position, size)]
                    self.positions += [positions[:]]

                    assert mapfile.read(1) == DEL
                
                assert mapfile.read(1) == END


        def update(self, seq_id, position, virgin):

            # batch-stream in order if virgin
            if virgin:
                if len(self.sequences) == 0 or self.sequences[-1] != seq_id:
                    self.sequences += [seq_id]
                    self.positions += [[position]]
                else:
                    self.positions[-1] += [position]
                return

            self.sequences, self.positions = binary_special_add([self.sequences, self.positions], seq_id, position)
        

        def save(self):
            with open(self.path, 'wb') as mapfile:

                # header byte signature
                mapfile.write(STR)

                # writing sequence vector
                mapfile.write(int_to_bytes(len(self.sequences)))
                for seq_id in self.sequences:
                    mapfile.write(int_to_bytes(seq_id))
                
                mapfile.write(DEL)

                # writing 2D-position vector
                for index in range(len(self.sequences)):
                    mapfile.write(int_to_bytes(len(self.positions[index])))
                    position: ExtraPosition
                    for position in self.positions[index]:
                        mapfile.write(int_to_bytes(position.start_position))
                        mapfile.write(int_to_bytes(position.size))
                
                    mapfile.write(DEL)

                mapfile.write(END)
        
            return len(self.sequences)


    '''
        FileMap object implements FoundMap interface functions, handeling hybrid memory-disk data
            memory -> batch is a python list structure containing sequence and 2D-position vectors
            disk -> for disk interaction a FileHandler object will be initiated, loading disk data
                in memory. after any necessary update operation on data in memory, the object saves
                data in disk.

        batch vectors: sequence vector containing sorted sequence id of founded sequences
            2D-position vector containing `n` array of positions (ExtraPosition class) which are found
            in a coresponding sequence at the same index

        virginity: FileMap is considered virgin if total data size is below batch limit
            therefore a virgin FileMap respond is based on only memory-data (no disk interaction)
            Also, a non-virgin FileMap batch data is invalid and FileMap only saves Q in memory which is 
            the length of sequence vector
    '''
    def __init__(self, initial=None, batch_size=0, batch_limit=BATCH_SIZE, q=0, path=None, virgin=True):
        
        if initial:
            self.batch = initial
        else:
            self.batch = [[],[]]

        self.batch_size = batch_size
        self.batch_limit = batch_limit
        self.q = q
        self.virgin = virgin

        if path:
            self.path = path


    '''
        dumping temporary data from memory to disk
        [WARNING] will raise exception if batch is empty
            update -> no exception will be thrown (printing error and return)
    '''
    def dump(self, return_map=False):

        # there must be an item in batch to dump
        # assert self.batch[0]
        if len(self.batch[0]) == 0:
            print('[ERROR] batch is empty for dumping: batch=%s'%(str(self.batch)))
            return

        # assign a path if doesn't exist
        if not hasattr(self, 'path'):
            self.path = get_random_free_path(FOUNDMAP_NAMETAG)
            
            with open(self.path, 'wb') as newfile:
                newfile.write(STR);newfile.write(int_to_bytes(0));newfile.write(DEL);newfile.write(END)

        map = self.FileHandler(self.path)
        for index, seq_id in enumerate(self.batch[0]):
            for position in self.batch[1][index]:
                map.update(seq_id, position, self.virgin)
        self.q = map.save()
        self.batch = [[], []]
        self.batch_size = 0

        self.virgin = False

        # WARNING: map could be heavy in memory
        if return_map:
            return map
        del map


    def dump_list(self, foundlist):
        
        self.virgin = False

        # clearing already existed data in foundmap
        if len(self.batch[0]) != 0:self.batch = [[],[]]
        if hasattr(self, 'path'):os.remove(self.path)

        self.path = get_random_free_path(FOUNDMAP_NAMETAG)
        map = self.FileHandler(self.path, dont_read=True)
        map.sequences = foundlist[0]
        map.positions = foundlist[1]
        self.q = map.save()

        return self



    def __str__(self):
        if hasattr(self, 'path'):
            return "<(FileMap) path '%s'>"%self.path
        else:
            return "<(FileMap) virgin - " + str(self.batch) + '>'


    # ########################################## #
    #  father abstract function implementation   #
    # ########################################## #

    # return the q value -> indicating number of seen-sequences
    def get_q(self):

        if self.virgin:
            return len(self.batch[0])

        if self.batch[0]:
            self.dump()
            
        return self.q


    def add_location(self, seq_id, position):
        self.batch = binary_special_add(self.batch, seq_id, position)
        self.batch_size += 1

        if self.virgin:
            self.q = len(self.batch[0])

        # dumping batch to file
        if self.batch_size == self.batch_limit:
            self.dump()


    # make a 2D array of ExtraPosition objects in foundmap 
    def get_positions(self):

        if self.virgin:
            return self.batch[1]

        if self.batch[0]:
            map = self.dump(return_map=True)
        else:
            map = self.FileHandler(self.path)

        return [map.positions[i] for i in range(len(map.positions))]


    def get_sequences(self):

        if self.virgin:
            return self.batch[0]

        if self.batch[0]:
            map = self.dump(return_map=True)
        else:
            map = self.FileHandler(self.path)

        return map.sequences

    
    def get_list(self):
        
        if self.virgin:
            return self.batch

        if self.batch[0]:
            map = self.dump(return_map=True)
        else:
            map = self.FileHandler(self.path)
        
        return [map.sequences, map.positions]


    def to_byte(self):
        if self.virgin:
            self.dump()

        return int_to_bytes(self.q) + int_to_bytes(len(self.path)) + bytes(self.path, encoding='ascii')


    @staticmethod
    def byte_to_object(buffer: BufferedReader):
        q = bytes_to_int(buffer.read(INT_SIZE))
        path = str(buffer.read(bytes_to_int(buffer.read(INT_SIZE))), encoding='ascii')
        return FileMap(virgin=False, path=path, q=q)


    def clear(self):
        if hasattr(self, 'path'):
            os.remove(self.path)
            del self.path

    # ########################################## #
    #                other functions             #
    # ########################################## #
    
    def clone(self):
        if self.virgin:
            return FileMap(batch_size=self.batch_size, q=self.q, initial=([self.batch[0][:]] + [self.batch[1][:]]))
        
        with open(self.path, 'rb') as original:
            data = original.read()

        clone_path = get_random_free_path(FOUNDMAP_NAMETAG)
        with open(clone_path, 'wb') as clone:
            clone.write(data)
            
        return FileMap(initial=([self.batch[0][:] + self.batch[1][:]]), 
                batch_size=self.batch_size,
                batch_limit=self.batch_limit,
                q=self.q,
                path=clone_path,
                virgin=False)
            
    
    def protect(self, directory):

        if self.virgin:self.dump()

        with open(self.path, 'rb') as original:
            data = original.read()
        
        protected_path = get_random_free_path(FOUNDMAP_NAMETAG, directory=directory)
        with open(protected_path, 'wb') as protected:
            protected.write(data)
        
        self.path = protected_path


class ReadOnlyMap(FoundMap, Bytable):            

    def __init__(self, collection, address:bytes):
        self.collection = collection
        self.address = address


    def to_byte(self):
        return self.address


    def byte_to_object(buffer: BufferedReader, collection):
        address = buffer.read(ID_LENGTH)
        return ReadOnlyMap(collection, address=address)


    def get_list(self):return mongo.read_list(self.address, collection_name=self.collection)
    def clear(self):          mongo.clear_list(self.address, collection_name=self.collection)

    def protect(self, collection):
        mongo.protect_list(address=self.address, collection_name=collection)


# ########################################## #
#                 functions                  #
# ########################################## #

def initial_readonlymaps(foundmaps:list[FoundMap], collection_name, client:MongoClient=None)->list[ReadOnlyMap]:
    
    if not client:client = mongo.get_client()
    
    order = []      # list of dictionaries for mongod process 
    objects = []    # return result objects of ReadOnlyMap
    collection = client[DATABASE_NAME][collection_name]
    
    for foundmap in foundmaps:
        readonlymap = ReadOnlyMap(collection_name, ObjectId())
        order.append({MONGO_ID:readonlymap.address, BINARY_DATA:mongo.list_to_binary(foundmap.get_list())})
        objects.append(readonlymap)

    collection.insert_many(order, ordered=False)
    return objects


def binary_special_add(found_list, seq_id, position):
    start = 0
    end = len(found_list[0]) - 1
    while start <= end:
        mid = (start+end)//2
        if found_list[0][mid] == seq_id:
            found_list[1][mid] = binary_add(found_list[1][mid], position)
            return found_list
        elif found_list[0][mid] < seq_id:
            start = mid + 1
        else:
            end = mid - 1
    found_list[0] = found_list[0][:start] + [seq_id] + found_list[0][start:]
    found_list[1] = found_list[1][:start] + [[position]] + found_list[1][start:]
    return found_list


def clear_disk(extension=FOUNDMAP_NAMETAG):
    garbage_size = 0
    garbages = [f for f in os.listdir(APPDATA_PATH) if f.endswith(extension)]
    print('[CLEAN] %d number of temp file are found and ... '%len(garbages), end='')
    for garbage in garbages:
        garbage_size += os.stat(APPDATA_PATH + garbage).st_size
        os.remove(os.path.join(APPDATA_PATH + garbage))
    print('cleared\ngarbage size = %d'%garbage_size)


def test_main():
    map = FileMap()
    print('Q=%d (0) TEST -> %s'%(map.get_q(), str(map.get_q()==0)))

    map.add_location(0, ExtraPosition(5, 0))
    print('Q=%d (1) TEST -> %s'%(map.get_q(), str(map.get_q()==1)))

    map.add_location(0, ExtraPosition(6, 0))
    map.add_location(1, ExtraPosition(7, 0))
    print('Q=%d (2) TEST -> %s'%(map.get_q(), str(map.get_q()==2)))

    map.add_location(3, ExtraPosition(8, 0))
    print('Q=%d (3) TEST -> %s'%(map.get_q(), str(map.get_q()==3)))

    map.add_location(0, ExtraPosition(9, 0))
    map.add_location(0, ExtraPosition(9, 1))
    map.add_location(0, ExtraPosition(10, 0))
    map.add_location(3, ExtraPosition(13, 0))
    map.add_location(0, ExtraPosition(14, 0))
    map.add_location(0, ExtraPosition(15, 0))

    map.dump()

    map.add_location(0, ExtraPosition(15, 1))
    map.add_location(0, ExtraPosition(16, 0))
    map.add_location(0, ExtraPosition(51, 0))
    map.add_location(1, ExtraPosition(0, 0))
    map.add_location(3, ExtraPosition(8, 0))
    map.add_location(5, ExtraPosition(0, 0))

    print('not empty batch, right?', end=' | batch=')
    print(map.batch)

    map.dump()

    print(map.batch)
    print('Q=%d'%map.get_q())


    print('DONE OBSERVE')

    bundle = map.get_list()

    print(bundle)

    print(map.get_sequences())
    for index, seq_id in enumerate(bundle[0]):
        position: ExtraPosition
        for position in bundle[1][index]:
            print('seq-%d|index-%d|position-%d|extra-%d'%(seq_id, index, position.start_position, position.size))

    print(map.get_q())
    print('virginity : %s'%str(map.virgin))

    make_location('test/test/')
    map.protect('test/test/')

    return map


def test_hard():
    mem = MemoryMap()
    dis = FileMap()

    map_manual = [[],[]]

    for _ in range(100000):
        random_seq_id = randrange(100)
        random_location = ExtraPosition(randrange(5000), randrange(10))
        cloned_location = ExtraPosition(random_location.start_position, random_location.size)
        cloned_location_2 = ExtraPosition(random_location.start_position, random_location.size)

        map_manual = binary_special_add(map_manual, random_seq_id, cloned_location_2)

        mem.add_location(random_seq_id, random_location)
        dis.add_location(random_seq_id, cloned_location)

    assert mem.get_q() == dis.get_q() and dis.get_q() == len(map_manual[0])

    bundle_mem = mem.get_list()
    bundle_dis = dis.get_list()

    assert bundle_mem[0] == bundle_dis[0]
    # assert bundle_mem[1] == bundle_dis[1]

    error_seq = 0
    no_error_seq = 0
    for i in range(len(bundle_mem[0])):
        if bundle_mem[1][i] != bundle_dis[1][i]:
            error_seq+=1
            print('ERROR FOUND at index=%d vec_size mem VS disk equal=%s'%(i, str(len(bundle_mem[1][i])==len(bundle_dis[1][i]))))
            for j in range(len(bundle_mem[1][i])):
                # print('mem %s | disk %s'%(str(bundle_mem[1][i][j]), bundle_dis[1][i][j]))
                if j < len(bundle_dis[1][i]):
                    if bundle_mem[1][i][j] != bundle_dis[1][i][j]:
                        print('ERROR EXACT LOCATION -> i=%d, j=%d'%(i, j))
                else:
                    print('ERROR %d index out of range for disk bundle'%j)
        else:
            no_error_seq+=1

    print('errors=%d | right=%d'%(error_seq, no_error_seq))

    return bundle_mem, bundle_dis, map_manual


def test_readonly():
    mapA = MemoryMap()
    mapA.add_location(0, ExtraPosition(0, 5))
    mapA.add_location(0, ExtraPosition(3, 4))
    mapA.add_location(1, ExtraPosition(0, 5))
    mapA.add_location(2, ExtraPosition(8, 6))
    mapA.add_location(3, ExtraPosition(13, 6))

    mapB = MemoryMap()
    mapB.add_location(0, ExtraPosition(0, 9))
    mapB.add_location(1, ExtraPosition(1, 4))
    mapB.add_location(1, ExtraPosition(0, 8))
    mapB.add_location(2, ExtraPosition(6, 6))
    mapB.add_location(2, ExtraPosition(3, 16))

    raps = initial_readonlymaps([mapA, mapB], 'testy')

    return raps


if __name__ == "__main__":
    # m, d, t = test_hard()
    rs = test_readonly()
    if len(sys.argv) == 1:
        print('clearing FOUNDMAP/DISKQUEUE junks...')
        clear_disk(FOUNDMAP_NAMETAG)
        clear_disk(DISK_QUEUE_NAMETAG)
    elif len(sys.argv) == 2:
        if sys.argv[-1] == 'NOP':
            pass
        else:
            print('clearing (extention=%s) junk...'%sys.argv[-1])
            clear_disk(sys.argv[-1])
    else:
        print('- WRONG INPUT -')
    # garbages = [f for f in os.listdir() if f.endswith(FOUNDMAP_NAMETAG)]
    # print('size = %d'%)
    # test_main()