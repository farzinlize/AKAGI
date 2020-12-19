from FoundMap import get_foundmap
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
    def __init__(self, label='', level=0):
        self.label = label
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
            found_list[1] -> position of occurrence on each sequence
        each element with same index in both list are related described below:
            any element in second list such as found_list[1][i] is a list of position that
            this node of tree occurs in sequence number of found_list[0][i]

        [UPDATE]: experiment shows that saving all data in memory results in RAM overflow!
            a class named FoundMap implemented to save such data in memory and disk instead 
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
        new_child = TrieNode(self.label + kmer[0], self.level+1)
        self.childs += [new_child]
        return new_child.add_frame(kmer[1:], seq_id, position)


    '''
        extracting motifs, nodes that are present in q number of sequences
            result_kmer -> indicates output type: 0 for object and 1 for kmer (string-fromat) only

        greaterthan
            True   (on): include all motifs with q-value greater than input q variable
            False (off): only include motifs with q-value equal to input variable
    '''
    def extract_motifs(self, q, result_kmer=1, greaterthan=True):
        motifs = []
        if hasattr(self, 'foundmap'):
            if self.foundmap.get_q() >= q:
                if greaterthan or self.foundmap.get_q() == q:
                    if result_kmer  :motifs += [self.label]
                    else            :motifs += [self]
        for child in self.childs:
            motifs += child.extract_motifs(q, result_kmer)
        return motifs


    def find_max_q(self, q_old=-1):
        my_q = -1
        if hasattr(self, 'foundmap'):
            my_q = self.foundmap.get_q()

        childs_max_q = []
        for child in self.childs:
            childs_max_q += [child.find_max_q(q_old)]

        return max(childs_max_q + [my_q, q_old])


    # ########################################## #
    #              chain section                 #
    # ########################################## #

    '''
        add chain attributes to motif nodes:
            end_chain_position: a structured list just like found_list that indicates
                where could a chain continue
            close_chain: any links is assumed open until it is chained to all possible candidates
                unless there isn't any. after that the chain is closed.
            chain_level: level of the link in chain
            next_chains: a list of links that are chained down from this node

        [WARNING] only nodes with found_list attribute could be chained (or could be a motif)
    '''
    def make_chain(self, chain_level=0, up_chain=None):
        if not hasattr(self, 'foundmap'):
            raise Exception('should be a motif')
        self.chain_level = chain_level
        self.next_chains = []
        self.up_chain = up_chain
        return self


    def add_chain(self, other):
        self.next_chains += [other]


    # ########################################## #
    #             report section                 #
    # ########################################## #

    def chain_sequence(self):
        if self.chain_level == 0:
            return self.label
        return self.up_chain.chain_sequence() + '|' + self.label

    
    def chain_locations_str(self):
        return str(self.foundmap)

    
    def instances_str(self, sequences):
        result = '>pattern\n%s\n>instances\n'%(self.chain_sequence())
        bundle = self.foundmap.get_list()
        for index, seq_id in enumerate(bundle[0]):
            for position in bundle[1][index]:
                end_index = int(position) + self.level
                start_index = position.start_position
                if len(position.chain) != 0:
                    start_index = position.chain[0]
                
                result += '%d,%d,%s,%d\n'%(
                    seq_id, 
                    (start_index-len(sequences[seq_id])), 
                    sequences[seq_id][start_index:end_index], 
                    (end_index-start_index))

        return result

    def set_color(self, color):
        if hasattr(self, 'color'):
            return False
        self.color = color
        return True


# ########################################## #
#           main function section            #
# ########################################## #

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
    test_main()