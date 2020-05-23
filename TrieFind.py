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

    def add_frame(self, kmer, seq_id):

        if len(kmer) == 0:
            # end of the path
            if not hasattr(self, 'found_list'):
                self.found_list = []
            self.found_list = binery_add(self.found_list, seq_id)
            return
        
        # searching for proper path
        for child in self.childs:
            if child.label[-1] == kmer[0]:
                return child.add_frame(kmer[1:], seq_id)

        # proper child (path) dose not exist
        new_child = TrieNode(self.label + kmer[0], self.level+1)
        self.childs += [new_child]
        return new_child.add_frame(kmer[1:], seq_id)

    
    def extract_motif(self, q):
        motifs = []
        if hasattr(self, 'found_list'):
            if len(self.found_list) >= q:
                motifs += [self.label]
        for child in self.childs:
            motifs += child.extract_motif(q)
        return motifs
        

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