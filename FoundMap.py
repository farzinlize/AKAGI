from misc import ExtraPosition, get_random_path, binery_add, bytes_to_int, int_to_bytes
import os
from constants import BATCH_SIZE, END, STR, DEL, INT_SIZE, FOUNDMAP_DISK, FOUNDMAP_MEMO, FOUNDMAP_MODE


# static foundmap choose based on global variable of FOUNDMAP_MODE
def get_foundmap():
    if FOUNDMAP_MODE == FOUNDMAP_DISK:
        return FileMap()
    elif FOUNDMAP_MODE == FOUNDMAP_MEMO:
        return MemoryMap()
    else:
        raise Exception('[FoundMap] FOUNDMAP_MODE variable unrecognized')


'''
    Father structure for Found Map and its children described below:
        MemoryMap: saving data in python list structure (object version of found_list)
        FileMap: saving data in byte-file
'''
class FoundMap:

    # abstract functions
    def add_location(self, seq_id, position):pass
    def get_q(self):pass
    def get_sequences(self):pass
    def get_positions(self):pass


class MemoryMap(FoundMap):

    def __init__(self, found_list=[[],[]]):
        self.found_list = found_list


    def add_location(self, seq_id, position):
        self.found_list = binery_special_add(self.found_list, seq_id, position)


    def get_q(self):
        return len(self.found_list)

    
    def get_sequences(self):
        return self.found_list[0]


class FileMap(FoundMap):

    class FileHandler:

        def __init__(self, path):

            self.path = path

            self.sequences = []
            self.positions = []

            with open(path, 'rb') as mapfile:

                assert mapfile.read(1) == STR
                for _ in range(mapfile.read(INT_SIZE)):

                    self.sequences += [bytes_to_int(mapfile.read(INT_SIZE))]
                    assert mapfile.read(1) == DEL

                    positions = []
                    for _ in range(mapfile.read(INT_SIZE)):
                        position = mapfile.read(INT_SIZE)
                        margin = mapfile.read(INT_SIZE)
                        positions += [ExtraPosition(position, margin)]

                    self.positions += positions[:]
                
                assert mapfile.read(1) == END


        def update(self, seq_id, position):
            self.sequences, self.positions = binery_special_add([self.sequences, self.positions], seq_id, position)
        

        def save(self):
            with open(self.path, 'wb') as mapfile:

                mapfile.write(STR)
                mapfile.write(int_to_bytes(len(self.sequences)))

                for index, seq_id in enumerate(self.sequences):
                    mapfile.write(int_to_bytes(seq_id))
                    mapfile.write(DEL)

                    mapfile.write(int_to_bytes(len(self.positions[index])))
                    for position in self.positions[index]:
                        mapfile.write(int_to_bytes(position.start_position))
                        mapfile.write(int_to_bytes(position.end_margin))
        
            return len(self.sequences)


    # FileMap init
    def __init__(self, batch=[], batch_limit=BATCH_SIZE, q=0):
        self.batch = batch
        self.batch_limit = batch_limit
        self.q = q


    def add_location_batch(self, seq_id, position):
        self.batch += [(seq_id, position)]

        # dumping batch to file
        if len(self.batch) == self.batch_limit:
            self.dump()


    def dump(self, return_map=False):

        # there must be an item in batch to dump
        assert self.batch

        # assign a path if dosen't exist
        if not hasattr(self, 'path'):
            self.path = get_random_path()+'.byte'
            while os.path.isfile(self.path):
                self.path = get_random_path()+'.byte'

        map = self.FileHandler(self.path)
        for seq_id, position in self.batch:
            map.update(seq_id, position)
        self.q = map.save()

        if return_map:
            return map
        del map

    
    #TODO
    def __str__(self):
        if hasattr(self, 'path'):
            return "<(FileMap) path '%s'>"%self.path


    # ########################################## #
    #  father abstract function implementation   #
    # ########################################## #

    # return the q value -> indicating number of seen-sequences
    def get_q(self):
        if self.batch:
            self.dump()
        return self.q


    def add_location(self, seq_id, position):
        self.add_location_batch(seq_id, position)


    # make a 2D array of ExtraPosition objects in foundmap 
    def get_positions(self):

        if self.batch:
            map = self.dump()
        else:
            map = self.FileHandler(self.path)

        return [map.positions[i] for i in range(len(map.positions))]


def binery_special_add(found_list, seq_id, position):
    start = 0
    end = len(found_list[0]) - 1
    while start <= end:
        mid = (start+end)//2
        if found_list[0][mid] == seq_id:
            found_list[1][mid] = binery_add(found_list[1][mid], position)
            return found_list
        elif found_list[0][mid] < seq_id:
            start = mid + 1
        else:
            end = mid - 1
    found_list[0] = found_list[0][:start] + [seq_id] + found_list[0][start:]
    found_list[1] = found_list[1][:start] + [[position]] + found_list[1][start:]
    return found_list


if __name__ == "__main__":
    map = FoundMap()
    print(map)