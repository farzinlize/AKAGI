from TrieFind import TrieNode
from Nodmer import Nodmer
from misc import FileHandler, heap_decode
import json

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
        first_code = (4**(self.kmin) - 1)//3 + 1
        last_code = (4**(self.kmax) - 1)//3
        with open('gkhood'+str(self.kmin)+'_'+str(self.kmax)+'.tree', 'w+') as tree:
            for code in range(first_code, last_code+1):
                node = self.trie.find(heap_decode(code, self.alphabet))
                if node == None:
                    print('ERROR: node couldnt be found, code -> ' + code)
                    continue
                dneighbourhood = node.dneighbours(dmax)
                file_index, position = handler.put(dneighbourhood)
                tree.write(str(file_index) + '\t' + str(position) + '\n')

        self.generate_dataset_metadata(dmax)
        

    '''
        generating metadata json file to store dataset information described in code
    '''
    def generate_dataset_metadata(self, dmax):
        with open('gkhood'+str(self.kmin)+'_'+str(self.kmax)+'.metadata', 'w+') as meta:
            first_code = (4**(self.kmin) - 1)//3 + 1 
            metadata_dict = { 
                'kmax':self.kmax,
                'kmin':self.kmin,
                'dmax':dmax,
                'bias':first_code,
                'alphabet':self.alphabet
            }
            meta.write(json.dumps(metadata_dict))



# ########################################## #
#           main fucntion section            #
# ########################################## #


# real main function for generating gkhood dataset
def main():
    print("generating GKmerHood (it will take a while)")
    gkhood = GKmerhood(5, 8)
    print("finished!")
    gkhood.generate_dataset(4)


# repairing dataset
def repair():
    print("generating GKmerHood (it will take a while)")
    gkhood = GKmerhood(5, 8)
    print("finished!")
    dmax = 4
    handler = FileHandler(gkhood, 'repair')
    real_first_code = (4**(gkhood.kmin) - 1)//3 + 1
    last_remaining_code = (4**(gkhood.kmin+1) - 1)//3
    with open('repair.tree', 'w+') as repair_tree:
        for code in range(real_first_code, last_remaining_code+1):
            node = gkhood.trie.find(heap_decode(code, gkhood.alphabet))
            if node == None:
                print('ERROR: node couldnt be found, code -> ' + code)
                continue
            dneighbourhood = node.dneighbours(dmax)
            file_index, position = handler.put(dneighbourhood)
            repair_tree.write(str(file_index) + '\t' + str(position) + '\n')


# generating metadata seperatly
def metadata_main():
    print('METADATA - main')
    print("generating GKmerHood (it will take a while)")
    gkhood = GKmerhood(5, 8)
    print("finished!")
    gkhood.generate_dataset_metadata(4)


# merge tree (tested)
def merge_tree():
    tree1 = open('gkhood5_8.tree', 'r')
    tree2 = open('repair.tree', 'r')
    merged = open('gkhood5_8_REPAIRED.tree', 'w+')
    for line in tree2:
        merged.write('R'+line)
    for line in tree1:
        merged.write(line)
    tree1.close()
    tree2.close()
    merged.close()


def test_main_3():
    print("[TEST-3] generating GKmerHood (it will take a while)")
    gkhood = GKmerhood(5, 8)
    first_code = int( (4**(gkhood.kmin+1) - 1)/3 + 1 )
    last_code = len(gkhood.nodes)-1
    kmer = heap_decode(first_code, gkhood.alphabet)
    lmer = heap_decode(last_code, gkhood.alphabet)
    print('first: kmer and code -> ', kmer, first_code)
    print('last: kmer and code -> ', lmer, last_code)
    node = gkhood.trie.find(kmer)
    if node == None:
        print('oh shit')
    dn = node.dneighbours(4)
    print(len(dn))
    for each in dn:
        if each[1] == 1:
            print(each[0].kmer)


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
    gkhood = GKmerhood(5, 8)

    sample = 'GGGGG'
    print('test 1 : all neighbours of ' + sample)
    node = gkhood.trie.find(sample)
    print(len(node.neighbours))
    for each in node.neighbours:
        print(each.kmer)

    neighbours_list = node.generate_neighbours()
    print(len(neighbours_list))
    for each in neighbours_list:
        print(each)


# ########################################## #
#           main fucntion call               #
# ########################################## #

# main function call
if __name__ == "__main__":
    metadata_main()