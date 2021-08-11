from io import BufferedReader, BytesIO
from typing import List, Tuple
from pymongo import MongoClient
from bson.objectid import ObjectId

import mongo
from misc import Bytable, bytes_to_int, int_to_bytes
from FoundMap import FoundMap, MemoryMap, ReadOnlyMap, get_foundmap, read_foundmap
from Nodmer import Nodmer

from constants import BINARY_DATA, DATABASE_NAME, DEFAULT_COLLECTION, EXTRACT_KMER, EXTRACT_OBJ, FOUNDMAP_MEMO, FOUNDMAP_MODE, INSERT_MANY, INT_SIZE, LABEL, MAXIMUM_ORDER_SIZE, MONGO_ID, POP, QUEUE_COLLECTION

'''
    Trie node object -> two purposed object for <searching> and <saving> kmers
        each node belongs to a level of tree and has a label indicating coresponding kmer

    <searching>: a trie binding to gkhood is used for searching a specific node for its kmer
        also this object will generate all nodes (child_birth) for its gkhood.
        each node within gkhood dimensions has a reference to coreponding node in gkhood
    
    <saving>: also known as motif tree, this object will save kmers occurrence information
        starting with a single root node, for each new kmer the coresponding path will be traversed
        or generated if it isn't exist. each node, in this mode, holds a sorted seen-list
            seen-list -> a list containing sequence IDs that coresponding kmer had been seen
'''
class TrieNode:
    def __init__(self, label='', level=0):
        self.label = label
        self.childs = []
        self.level = level

    
# ########################################## #
#             searching section              #
# ########################################## #

class SearchNode(TrieNode):

    # root node is in first (zero) level
    def is_root(self):
        return self.level == 0


    def get_node(self):
        if hasattr(self, 'node'):
            return self.node


    def create_node(self, gkhood):
        self.node = Nodmer(gkhood, self.label)
        return self.node


    '''
        recursively, initial a complete tree up to gkhood maximum size level
            each node that is within gkhood dimensions will generate a new node
    '''
    def child_birth(self, gkhood):
        if self.level == gkhood.kmax:
            return [self.create_node(gkhood)]
        self.childs = [SearchNode(self.label + letter, self.level+1) for letter in gkhood.alphabet]
        grandchildsNodmers = []
        for child in self.childs:
            grandchildsNodmers += child.child_birth(gkhood)
        if self.level >= gkhood.kmin:
            grandchildsNodmers += [self.create_node(gkhood)]
        return grandchildsNodmers


    # recursively will find a specific node coresponding to a specific kmer
    def find(self, kmer):
        if len(kmer) == 0:
            return self.get_node()
        if len(self.childs) == 0:
            return None
        for child in self.childs:
            if child.label[-1] == kmer[0]:
                return child.find(kmer[1:])


# ########################################## #
#         saving seen kmers section          #
# ########################################## #

class WatchNode(TrieNode):

    '''
        any node with found_list attribute is considered a leaf presenting motif
        found_list is an abstract structure that is constructed by lists
        a found_list has two list:
            found_list[0] -> seq_ids
            found_list[1] -> position of occurrence on each sequence
        each element with same index in both list are related described below:
            any element in second list such as found_list[1][i] is a list of position that
            this node of tree occurs in sequence number of found_list[0][i]

        [UPDATE]: experiment shows that saving all data in memory results in RAM overflow!
            a class named FoundMap implemented to save such data in both memory and disk instead 
            of found_list which is now removed from TrieFind class
    '''
    def add_frame(self, kmer, seq_id, position):

        if len(kmer) == 0:
            # end of the path
            if not hasattr(self, 'foundmap'):
                self.foundmap = get_foundmap()

            self.foundmap.add_location(seq_id, position)
            # self.found_list = binary_special_add(self.found_list, seq_id, position)
            return
        
        # searching for proper path
        for child in self.childs:
            if child.label[-1] == kmer[0]:
                return child.add_frame(kmer[1:], seq_id, position)

        # proper child (path) dose not exist
        new_child = WatchNode(self.label + kmer[0], self.level+1)
        self.childs += [new_child]
        return new_child.add_frame(kmer[1:], seq_id, position)


    '''
        extracting motifs, nodes that are present in q number of sequences
            result_kmer -> indicates output type: 0 for object and 1 for kmer (string-fromat) only

        greaterthan
            True   (on): include all motifs with q-value greater than input q variable
            False (off): only include motifs with q-value equal to input variable
    '''
    def extract_motifs(self, q, result_kmer=EXTRACT_KMER, greaterthan=True):
        motifs = []
        if hasattr(self, 'foundmap'):
            if self.foundmap.get_q() >= q:
                if greaterthan or self.foundmap.get_q() == q:
                    if result_kmer==EXTRACT_KMER  :motifs += [self.label]
                    elif result_kmer==EXTRACT_OBJ :motifs += [self]
        for child in self.childs:
            motifs += child.extract_motifs(q, result_kmer)
        return motifs

    
    '''
        special extraction function for chaining
            delete child attrubutes after extraction
            also return total number of nodes in tree
    '''
    def extract_motifs_and_delete_childs(self, q, result_kmer=EXTRACT_KMER): 
        motifs = []
        tree_node_count = 1
        if hasattr(self, 'foundmap'):
            if self.foundmap.get_q() >= q:
                if result_kmer==EXTRACT_KMER  :motifs += [self.label]
                elif result_kmer==EXTRACT_OBJ :motifs += [self]
        for child in self.childs:
            child_motifs, child_tree_count = child.extract_motifs_and_delete_childs(q, result_kmer)
            motifs += child_motifs
            tree_node_count += child_tree_count
        
        # delete childs references
        del self.childs
        return motifs, tree_node_count


    def find_max_q(self, q_old=-1):
        my_q = -1
        if hasattr(self, 'foundmap'):
            my_q = self.foundmap.get_q()

        childs_max_q = []
        for child in self.childs:
            childs_max_q += [child.find_max_q(q_old)]

        return max(childs_max_q + [my_q, q_old])


    def instances_str(self, sequences):
        return self.foundmap.instances_to_string_fastalike(self.label, sequences)


    def clear(self):
        if hasattr(self, 'foundmap'):
            self.foundmap.clear()
        for child in self.childs:
            child.clear()
            

class WatchNodeC(WatchNode):

    def __init__(self, label='', level=0, custom_foundmap_type=FOUNDMAP_MODE):
        super().__init__(label=label, level=level)
        self.custom_foundmap_type = custom_foundmap_type

    # override 
    def add_frame(self, kmer, seq_id, position):

        if len(kmer) == 0:
            # end of the path
            if not hasattr(self, 'foundmap'):
                self.foundmap = get_foundmap(foundmap_type=self.custom_foundmap_type)

            self.foundmap.add_location(seq_id, position)
            return
        
        # searching for proper path
        for child in self.childs:
            if child.label[-1] == kmer[0]:
                return child.add_frame(kmer[1:], seq_id, position)

        # proper child (path) dose not exist
        new_child = WatchNodeC(self.label + kmer[0], self.level+1, custom_foundmap_type=self.custom_foundmap_type)
        self.childs += [new_child]
        return new_child.add_frame(kmer[1:], seq_id, position)


# ########################################## #
#              chain section                 #
# ########################################## #

class ChainNode(Bytable):

    def __init__(self, label, foundmap: FoundMap):
        self.foundmap = foundmap
        self.label = label


    '''
        serialization methods for byte/object conversion 
    '''
    def to_byte(self):
        return int_to_bytes(len(self.label))    + \
            bytes(self.label, encoding='ascii') + \
            self.foundmap.to_byte()


    @staticmethod
    def byte_to_object(buffer: BufferedReader):
        first_read = buffer.read(INT_SIZE)
        if first_read:
            label = str(buffer.read(bytes_to_int(first_read)), 'ascii')
            foundmap = read_foundmap(buffer)
            return ChainNode(label, foundmap)
            
        
    def instances_str(self, sequences):
        return self.foundmap.instances_to_string_fastalike(self.label, sequences)


def initial_chainNodes(tuples:List[Tuple[str, FoundMap]], collection_name, client:MongoClient=None)->List[ChainNode]:

    if not client:client = mongo.get_client();should_close = True
    else                                     :should_close = False
    
    order = []      # list of dictionaries for mongod process 
    objects = []    # return result objects of ReadOnlyMap
    collection = client[DATABASE_NAME][collection_name]
    
    for label, foundmap in tuples:

        # check for order size limit
        if len(order) == MAXIMUM_ORDER_SIZE:
            error = mongo.safe_operation(collection, INSERT_MANY, order)
            if error:
                if should_close:client.close()
                return error
            else:order = []

        readonlymap = ReadOnlyMap(collection_name, ObjectId().binary)
        chain_node = ChainNode(label=label, foundmap=readonlymap)
        order.append({MONGO_ID   :readonlymap.address, 
                      BINARY_DATA:mongo.list_to_binary(foundmap.get_list()),
                      LABEL:label})
        objects.append(chain_node)

    error = mongo.safe_operation(collection, INSERT_MANY, order)
    if should_close:client.close()
    if error:return error
    else    :return objects


def pop_chain_node(client:MongoClient=None):

    if not client:client=mongo.get_client();should_close = True
    else                                   :should_close = False

    collection = client[DATABASE_NAME][QUEUE_COLLECTION]
    popy = mongo.safe_operation(collection, POP)
    if should_close:client.close()

    if not popy:return None
    if not isinstance(popy, dict):return popy # as error

    return ChainNode(popy[LABEL], MemoryMap(initial=mongo.binary_to_list(BytesIO(popy[BINARY_DATA]))))


# ########################################## #
#           main function section            #
# ########################################## #

def try_this():
    tree = WatchNodeC(custom_foundmap_type=FOUNDMAP_MEMO)
    tree.add_frame('AAT', 0, 0)
    tree.add_frame('ATT', 0, 2)
    tree.add_frame('AAT', 1, 5)
    tree.add_frame('AAT', 3, 43)
    tree.add_frame('AAT', 5, 0)
    return tree


# testing binary search-add
def test_main():
    t = TrieNode()
    t.add_frame('AAT', 0, 0)
    t.add_frame('ATT', 0, 0)
    t.add_frame('ATT', 1, 0)
    t.add_frame('ATT', 2, 1)
    t.add_frame('GGG', 1, 0)
    t.add_frame('GGG', 2, 0)
    t.add_frame('GGG', 0, 0)

    q = t.find_max_q()
    print(t.extract_motifs(q))


##########################################
# main function call
if __name__ == "__main__":
    # test_main()
    t = try_this()