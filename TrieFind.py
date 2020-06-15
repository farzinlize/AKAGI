from Nodmer import Nodmer

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
    def __init__(self, lable='', level=0):
        self.label = lable
        self.childs = []
        self.level = level


    # ########################################## #
    #             searching section              #
    # ########################################## #

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
        self.childs = [TrieNode(self.label + letter, self.level+1) for letter in gkhood.alphabet]
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

    '''
        any node with found_list attribute is considered a leaf presenting motif
        found_list is an abstract structure that is constructed by lists
        a found_list has two list:
            found_list[0] -> seq_ids
            found_list[1] -> position of occurence on each sequence
        each element with same index in both list are related described below:
            any element in second list such as found_list[1][i] is a list of position that
            this node of tree occures in sequence number of found_list[0][i]
    '''
    def add_frame(self, kmer, seq_id, position):

        if len(kmer) == 0:
            # end of the path
            if not hasattr(self, 'found_list'):
                self.found_list = [[], []]
            self.found_list = binery_special_add(self.found_list, seq_id, position)
            return
        
        # searching for proper path
        for child in self.childs:
            if child.label[-1] == kmer[0]:
                return child.add_frame(kmer[1:], seq_id, position)

        # proper child (path) dose not exist
        new_child = TrieNode(self.label + kmer[0], self.level+1)
        self.childs += [new_child]
        return new_child.add_frame(kmer[1:], seq_id, position)


    '''
        extracting motifs, nodes that are present in q number of sequences
            result_kmer -> indicates output type: 0 for object and 1 for kmer only
    '''
    def extract_motifs(self, q, result_kmer=1):
        motifs = []
        if hasattr(self, 'found_list'):
            if len(self.found_list[0]) >= q:
                if result_kmer:
                    motifs += [self.label]
                else:
                    motifs += [self]
        for child in self.childs:
            motifs += child.extract_motifs(q, result_kmer)
        return motifs


    # ########################################## #
    #              chain section                 #
    # ########################################## #

    '''
        add chain arrtibutes to motif nodes:
            end_chain_position: a structured list just like found_list that indicates
                where could a chain continue
            close_chain: any links is assumed open untill it is chained to all possible condidates
                unless there isn't any. after that the chain is closed.
            chain_level: level of the link in chain
            next_chains: a list of links that are chained down from this node

        [WARNING] only nodes with found_list attribute could be chained (or could be a motif)
    '''
    def make_chain(self, chain_level=0):
        if not hasattr(self, 'found_list'):
            raise Exception('should be a motif')
        self.end_chain_positions = self.found_list
        self.close_chain = False
        self.chain_level = chain_level
        self.next_chains = []
        return self


    def add_chain(self, other):
        self.next_chains += [other]

    
    def chained_done(self):
        self.close_chain = True


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


# add an item to a sorted list using binery search
def binery_add(lst, item):
    start = 0
    end = len(lst)-1
    while start <= end:
        mid = (start+end)//2
        if lst[mid] == item:
            return lst
        elif lst[mid] < item:
            start = mid + 1
        else:
            end = mid - 1
    return lst[:start] + [item] + lst[start:]


# ########################################## #
#           main fucntion section            #
# ########################################## #

# testing binery search-add
def test_main():
    lst = []
    lst = binery_add(lst, 5)
    lst = binery_add(lst, 8)
    lst = binery_add(lst, 2)
    lst = binery_add(lst, 3)
    lst = binery_add(lst, 10)
    lst = binery_add(lst, 3)
    print(lst)


##########################################
# main function call
# test_main()