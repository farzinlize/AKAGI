from abc import abstractmethod
from ast import Str
from io import BufferedReader
from typing import List
from misc import Bytable, ExtraPosition, get_random_free_path, get_random_path, binary_add, bytes_to_int, int_to_bytes
import os, sys
from constants import BATCH_SIZE, DISK_QUEUE_NAMETAG, END, FOUNDMAP_NAMETAG, STR, DEL, INT_SIZE, FOUNDMAP_DISK, FOUNDMAP_MEMO, FOUNDMAP_MODE


# static foundmap choose based on global variable of FOUNDMAP_MODE
def get_foundmap():
    if FOUNDMAP_MODE == FOUNDMAP_DISK:return FileMap()
    elif FOUNDMAP_MODE == FOUNDMAP_MEMO:return MemoryMap()
    else:raise Exception('[FoundMap] FOUNDMAP_MODE variable unrecognized')


'''
    Father structure for Found Map and its children described below:
        MemoryMap: saving data in python list structure (object version of found_list)
        FileMap: saving data in byte-file
'''
class FoundMap(Bytable):

    # abstract functions
    def add_location(self, seq_id, position):raise NotImplementedError
    def get_q(self):raise NotImplementedError
    def get_sequences(self):raise NotImplementedError
    def get_positions(self):raise NotImplementedError
    def get_list(self) -> List[List]:raise NotImplementedError
    def clone(self): raise NotImplementedError


    def instances_to_string_fastalike(self, label, sequences: List[str], end_margin=0):
        try:
            result = '>pattern\n%s\n>instances\n'%(label)
            bundle = self.get_list()
            for index, seq_id in enumerate(bundle[0]):
                position: ExtraPosition
                for position in bundle[1][index]:
                    end_index = int(position) + len(label) + end_margin
                    start_index = position.start_position
                    # if len(position.chain) != 0:
                    #     start_index = position.chain[0]
                
                    result += '%d,%d,%s,%d\n'%(
                        seq_id, 
                        (start_index-len(sequences[seq_id])), 
                        sequences[seq_id][start_index:end_index], 
                        (end_index-start_index))
            return result

        except NotImplementedError:
            print('[ERROR][FOUNDMAP] not implemented for class:%s'%(str(self.__class__)))



class MemoryMap(FoundMap):

    def __init__(self, foundlist=[[],[]]):self.found_list = [[],[]]

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


class FileMap(FoundMap, Bytable):

    class FileHandler:

        '''
            Provides memory-disk transform using byte stream files for saving on disk
            functions:
                init -> new born object loads data from its file (if exists)
                update -> updating data in memory using batch (temporary data saved on memory)
                save -> transform data into byte stream and save it on file

            [PROTOCOL] byte stream portocol descried here:
                int value -> fixed integer size at constants module (INT_SIZE)
                vectors -> size of vectors are restored at the begining of each
                special bytes -> special bytes are consider to prevent file errors defined at constants 
                    module (STR `start`, END `end`, DEL `delimitter`)
        '''
        def __init__(self, path):

            self.path = path

            self.sequences = []
            self.positions = []

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
                        margin = bytes_to_int(mapfile.read(INT_SIZE), signed=True)
                        positions += [ExtraPosition(position, margin)]
                    self.positions += [positions[:]]
                
                assert mapfile.read(1) == END


        def update(self, seq_id, position, virgin):

            # batch-stream
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
                    for position in self.positions[index]:
                        mapfile.write(int_to_bytes(position.start_position))
                        mapfile.write(int_to_bytes(position.end_margin, signed=True))

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
    def __init__(self, initial=[[],[]], batch_size=0, batch_limit=BATCH_SIZE, q=0, path=None, virgin=True):
        self.batch = initial
        self.batch_size = batch_size
        self.batch_limit = batch_limit
        self.q = q
        self.virgin = virgin

        if path:
            self.path = path


    '''
        dumping temporary data from memory to disk
        [WARNING] will raise exception if batch is empty
    '''
    def dump(self, return_map=False):

        # there must be an item in batch to dump
        assert self.batch[0]

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

        # WARNING: map could be heavy in memory
        if return_map:
            return map
        del map

    
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

        # dumping batch to file
        if self.batch_size == self.batch_limit:
            self.dump()
            self.virgin = False


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

        return int_to_bytes(self.q) +\
               int_to_bytes(len(self.path)) +\
               bytes(self.path, encoding='ascii')

    @staticmethod
    def byte_to_object(buffer: BufferedReader):
        q = buffer.read(INT_SIZE)
        path = str(buffer.read(bytes_to_int(buffer.read(INT_SIZE))), encoding='ascii')
        return FileMap(virgin=False, path=path, q=q)


    def clear(self):
        if hasattr(self, 'path'):
            os.remove(self.path)
            del self.path

    
    def clone(self):
        if self.virgin:
            return FileMap(batch_size=self.batch_size, q=self.q, initial=([self.batch[0][:] + self.batch[1][:]]))
        
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
            


# ########################################## #
#                 functions                  #
# ########################################## #

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
    garbages = [f for f in os.listdir() if f.endswith(extension)]
    print('[CLEAN] %d number of temp file are found and ... '%len(garbages), end='')
    for garbage in garbages:
        garbage_size += os.stat(garbage).st_size
        os.remove(os.path.join(garbage))
    print('cleared\ngarbage size = %d'%garbage_size)


def test_main():
    map = FileMap()

    map.add_location(0, ExtraPosition(5, 0))
    map.add_location(0, ExtraPosition(6, 0))
    map.add_location(0, ExtraPosition(7, 0))
    map.add_location(0, ExtraPosition(8, 0))
    map.add_location(0, ExtraPosition(9, 0))
    map.add_location(0, ExtraPosition(9, 1))
    map.add_location(0, ExtraPosition(10, 0))
    map.add_location(0, ExtraPosition(13, 0))
    map.add_location(0, ExtraPosition(14, 0))
    map.add_location(0, ExtraPosition(15, 0))
    map.add_location(0, ExtraPosition(15, 1))
    map.add_location(0, ExtraPosition(16, 0))
    map.add_location(0, ExtraPosition(51, 0))
    map.add_location(1, ExtraPosition(0, 0))
    map.add_location(3, ExtraPosition(8, 0))

    print(map.batch)

    map.dump()
    map.virgin=False

    print(map.batch)


    print('DONE OBSERVE')

    bundle = map.get_list()

    print(bundle)

    print(map.get_sequences())
    for index, seq_id in enumerate(bundle[0]):
        for position in bundle[1][index]:
            print('seq-%d|index-%d|position-%d|extra-%d'%(seq_id, index, position.start_position, position.end_margin   ))

    print(map.get_q())
    print('virginity : %s'%str(map.virgin))


if __name__ == "__main__":
    test_main()
    if len(sys.argv) == 1:
        print('clearing FOUNDMAP/DISKQUEUE junks...')
        clear_disk(FOUNDMAP_NAMETAG)
        clear_disk(DISK_QUEUE_NAMETAG)
    elif len(sys.argv) == 2:
        print('clearing (extention=%s) junk...'%sys.argv[-1])
        clear_disk(sys.argv[-1])
    else:
        print('- NO OPERATION -')
    # garbages = [f for f in os.listdir() if f.endswith(FOUNDMAP_NAMETAG)]
    # print('size = %d'%)
    # test_main()