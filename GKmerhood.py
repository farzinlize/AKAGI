from TrieFind import TrieNode
from Nodmer import Nodmer
from misc import FileHandler, heap_decode

'''
    Graph object -> hold all information of nodes and graph properties
        dimensions: kmin and kmax indicate minimum and maximum size of kmers that are presented in graph
        alphabet: a set of possible letters for kmers in graph (it could be any iterable like string)
        trie tree: a search tree, binded to graph for finding nodes with specific kmer
'''
class GKmerhood:
    def __init__(self, k_min, k_max, alphabet='ATCG'):
        self.kmin = k_min
        self.kmax = k_max
        self.alphabet = alphabet
        self.nodes = self.initial_trie_nodes()
        self.initial_neighbourhood()


    '''
        generate or return already presented dictionary of graph
            graph dictionary will return index of any letter in graph alphabet
    '''
    def get_dictionary(self):
        if hasattr(self, 'dictionary'):
            return self.dictionary
        self.dictionary = {}
        for i in range(len(self.alphabet)):
            self.dictionary.update({self.alphabet:i})
        return self.dictionary


    '''
        initializing process for generating graph nodes, within its dimensions
            all works are done by trie, binded to graph
    '''
    def initial_trie_nodes(self):
        self.trie = TrieNode()
        return self.trie.child_birth(self)

    
    '''
        initializing process for establishing neighbours (generating edges)
            each node will generate a set of neighbour-kmers at a edit-distance of one
            for each neighbour-kmer, coresponding node (vaeiable->nodebour) will be found by trie
            and will be added as a neighbour as an edge
    '''
    def initial_neighbourhood(self):
        for node in self.nodes:
            neighbours = node.generate_neighbours()
            for neighbour in neighbours:
                if len(neighbour) >= self.kmin and len(neighbour) <= self.kmax:
                    nodebour = self.trie.find(neighbour)
                    node.add_neighbour(nodebour)


    '''
        generating a dataset of neighbourhoods within dmax edit-distance from each other
            the process will generate a tree-like file that holds a location of each node neighbourhood
            each kmer-node has a unique code that will organized them in an array
                -> each line in tree-like file is related to these codes
            
        note: because of using heap_encode and heap_decode
        this function only works for DNA alphabet (or any 4 letter alphabet)
    '''
    def generate_dataset(self, dmax):
        handler = FileHandler(self, 'dataset')
        first_code = (4**(self.kmin+1) - 1)/3 + 1
        with open('gkhood'+str(self.kmin)+'_'+str(self.kmax)+'.tree', 'w+') as tree:
            for code in range(int(first_code), len(self.nodes)):
                node = self.trie.find(heap_decode(code, self.alphabet))
                if node == None:
                    print('ERROR: node couldnt be found, code -> ' + code)
                    continue
                dneighbourhood = node.dneighbours(dmax)
                file_index, position = handler.put(dneighbourhood)
                tree.write(str(file_index) + '\t' + str(position) + '\n')


# ########################################## #
#           main fucntion section            #
# ########################################## #


# real main function for generating gkhood dataset
def main():
    print("generating GKmerHood (it will take a while)")
    gkhood = GKmerhood(5, 8)
    print("finished!")
    gkhood.generate_dataset(4)


# test main function for analyzing neighbours count for different kmers
def test_main_2():
    print("generating GKmerHood (it will take a while)")
    gkhood = GKmerhood(5, 8)
    print("finished!")

    samples_5 = ['GTAGC', 'AATGC', 'TGCAT']
    samples_6 = ['ATCTGA', 'TTTACG', 'AATGCA', 'GTACCA', 'ATTTTC']
    samples_7 = ['ATCGTAC', 'TTATCGA', 'GTAGGGA', 'TTTTGTA']
    samples_8 = ['GGTAGGTA', 'GCGTAGCA']

    print('5-mers:')
    for fmer in samples_5:
        node = gkhood.trie.find(fmer)
        print(node.kmer, ' - neighbours count:', len(node.neighbours))

    print('6-mers:')
    for smer in samples_6:
        node = gkhood.trie.find(smer)
        print(node.kmer, ' - neighbours count:', len(node.neighbours))

    print('7-mers:')
    for vmer in samples_7:
        node = gkhood.trie.find(vmer)
        print(node.kmer, ' - neighbours count:', len(node.neighbours))

    print('8-mers:')
    for gmer in samples_8:
        node = gkhood.trie.find(gmer)
        print(node.kmer, ' - neighbours count:', len(node.neighbours))


# test main function for tseting gkhood implementation
def test_main():
    gkhood = GKmerhood(5, 7)

    sample = 'ATCTTA'
    print('test 1 : all neighbours of ' + sample)
    node = gkhood.trie.find(sample)
    print(len(node.neighbours))
    for each in node.neighbours:
        print(each.kmer)


# ########################################## #
#           main fucntion call               #
# ########################################## #

# main function call
if __name__ == "__main__":
    main()