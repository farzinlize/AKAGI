from TrieFind import SearchNode
from Nodmer import Nodmer
from misc import FileHandler, heap_decode, heap_encode, alphabet_to_dictionary
import os, platform, json

'''
    Graph object -> hold all information of nodes and graph properties
        dimensions: kmin and kmax indicate minimum and maximum size of kmers that are presented in graph
        alphabet: a set of possible letters for kmers in graph (it could be any iterable like string)
        trie tree: a search tree, bonded to graph for finding nodes with specific kmer
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
            all works are done by trie, bonded to graph
    '''
    def initial_trie_nodes(self):
        self.trie = SearchNode()
        return self.trie.child_birth(self)

    
    '''
        initializing process for establishing neighbours (generating edges)
            each node will generate a set of neighbour-kmers at a edit-distance of one
            for each neighbour-kmer, coresponding node (variable->nodebour) will be found by trie
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
        handler = FileHandler('dataset')
        first_code = (4**(self.kmin) - 1)//3 + 1
        last_code = (4**(self.kmax+1) - 1)//3
        gkhood_tree_name = 'gkhood'+str(self.kmin)+'_'+str(self.kmax)
        with open(gkhood_tree_name+'.tree', 'w+') as tree:
            for code in range(first_code, last_code+1):
                node = self.trie.find(heap_decode(code, self.alphabet))
                if node == None:
                    print("ERROR: node couldn't be found, code -> " + code)
                    continue
                dneighbourhood = node.dneighbours(dmax)
                file_index, position = handler.put(dneighbourhood)
                tree.write(str(file_index) + '\t' + str(position) + '\n')

            number_of_files_minus, last_position = handler.close()
            tree.write(str(number_of_files_minus) + '\t' + str(last_position) + '\n')

        self.generate_dataset_metadata(gkhood_tree_name, first_code, dmax, number_of_files_minus+1)


    '''
        special function to generate single level dataset
    '''
    def single_level_dataset(self, dmax, level):
        handler = FileHandler(directory_name='single_level_%s'%(str(level)))
        first_code = (4**(level) - 1)//3 + 1
        last_code = (4**(level+1) - 1)//3
        sgkhood_tree_filename = 'sgkhood'+str(level)
        with open(sgkhood_tree_filename+'.tree', 'w+') as tree:
            for code in range(first_code, last_code+1):
                node = self.trie.find(heap_decode(code, self.alphabet))
                if node == None:
                    print("ERROR: node couldn't be found, code -> " + code)
                    continue
                dneighbourhood = node.dneighbours(dmax)
                file_index, position = handler.put(dneighbourhood)
                tree.write(str(file_index) + '\t' + str(position) + '\n')

            number_of_files_minus, last_position = handler.close()
            tree.write(str(number_of_files_minus) + '\t' + str(last_position) + '\n')

        self.generate_dataset_metadata(sgkhood_tree_filename, first_code, dmax, number_of_files_minus+1)


    def special_dataset_generate(self, dmax, first_level, last_level):
        handler = FileHandler(directory_name='cache%s'%(str(first_level)+str(last_level)))
        first_code = (4**(first_level) - 1)//3 + 1
        last_code = (4**(last_level+1) - 1)//3
        gkhood_tree_filename = 'gkhood'+str(first_level)+str(last_level)
        with open(gkhood_tree_filename+'.tree', 'w+') as tree:
            for code in range(first_code, last_code+1):
                node = self.trie.find(heap_decode(code, self.alphabet))
                if node == None:
                    print("ERROR: node couldn't be found, code -> " + code)
                    continue
                dneighbourhood = node.dneighbours(dmax)
                file_index, position = handler.put(dneighbourhood)
                tree.write(str(file_index) + '\t' + str(position) + '\n')

            number_of_files_minus, last_position = handler.close()
            tree.write(str(number_of_files_minus) + '\t' + str(last_position) + '\n')

        self.generate_dataset_metadata(gkhood_tree_filename, first_code, dmax, number_of_files_minus+1, fl=(first_level, last_level))


    '''
        generating metadata json file to store dataset information described in code
    '''
    def generate_dataset_metadata(self, tree_name, bias, dmax, number_of_files, single_level=None, fl=None):
        with open(tree_name+'.metadata', 'w+') as meta:

            metadata_dict = { 
                'kmax':self.kmax,
                'kmin':self.kmin,
                'dmax':dmax,
                'bias':bias,
                'alphabet':self.alphabet,
                'files':number_of_files
            }

            if single_level != None:
                metadata_dict.update({'level':single_level})

            if fl != None:
                metadata_dict.update({'first-level':fl[0], 'last-level':fl[1]})

            meta.write(json.dumps(metadata_dict))


'''
    Graph interface object -> responsible for returning d-neighbourhood, extracted from GKhood
        if an instance of gkhood is already in memory, the object will use the instance
        and if not, the object will extract a location of requested data from a tree-like file
'''
class GKHoodTree:
    def __init__(self, filename='', directory_name='dataset', gkhood=None):

        # gkhood in memory
        if gkhood != None:
            self.gkhood = gkhood

        else:
            # file address splitter is different in windows and linux
            operating_system = platform.system()
            if operating_system == 'Windows':
                splitter = '\\'
            else:   # operating_system == 'Linux'
                splitter = '/'

            self.read_metadata(filename)
            self.read_tree(filename)
            self.directory = os.getcwd() + splitter + directory_name + splitter
            self.dictionary = alphabet_to_dictionary(self.metadata['alphabet'])
    

    def read_tree(self, filename):
        self.tree = []
        with open(filename + '.tree', 'r') as tree_file:
            for line in tree_file:
                row = line.split()
                self.tree += [(row[0], int(row[1]))]


    def read_metadata(self, filename):
        with open(filename + '.metadata', 'r') as metafile:
            self.metadata = json.load(metafile)


    def dneighbours_mem(self, kmer, dmax):
        assert hasattr(self, 'gkhood')
        node = self.gkhood.trie.find(kmer)
        return node.dneighbours(dmax)


    def dneighbours(self, kmer, dmax):

        # from dataset
        line = heap_encode(kmer, self.dictionary) - self.metadata['bias']

        if line < 0:
            raise Exception('[GKHoodTree] kmer %s dose not exist in this dataset'%kmer)

        # last line problem TODO
        if line == len(self.tree)-1:
            # dn_length = len(self.tree) - self.tree[line][1]
            pass

        dn_length = self.tree[line+1][1] - self.tree[line][1]
        dneighbours = []
        with open(self.directory + self.tree[line][0] + '.data', 'r') as host:

            # skip lines
            for _ in range(self.tree[line][1]):
                next(host)
            
            # read part
            for _ in range(dn_length):
                line_data = host.readline().split()
                if len(line_data) == 0 or int(line_data[1]) > dmax:
                    break
                dneighbours += [(line_data[0], int(line_data[1]))]
        
        return dneighbours


    def get_position(self, kmer):

        # return None if there is no dataset
        if hasattr(self, 'gkhood'):
            return None

        line = heap_encode(kmer, self.dictionary) - self.metadata['bias']
        return self.tree[line]
        

# dummy tree object for distance=0 observation
class DummyTree:
    def __init__(self, filename='', directory_name='', gkhood=None):pass
    def dneighbours(self, kmer, dmax):return []

# ########################################## #
#           main function section            #
# ########################################## #


# real main function for generating gkhood dataset
def main():
    print("generating GKmerHood (it will take a while)")
    gkhood = GKmerhood(5, 8)
    print("finished!")
    gkhood.generate_dataset(4)


# generating metadata separately
def metadata_main():
    print('METADATA - main')
    print("generating GKmerHood (it will take a while)")
    gkhood = GKmerhood(5, 8)
    print("finished!")
    gkhood.generate_dataset_metadata(4, 1800) # not real number of files as argument


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


# test main function for testing gkhood implementation
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
#           main function call               #
# ########################################## #

# main function call
if __name__ == "__main__":
    main()