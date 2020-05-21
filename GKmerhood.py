from TrieFind import TrieNode
from Nodmer import Nodmer
from misc import FileHandler, heap_decode

class GKmerhood:
    def __init__(self, k_min, k_max, alphabet='ATCG'):
        self.kmin = k_min
        self.kmax = k_max
        self.alphabet = alphabet
        self.generate_dict(alphabet)
        self.nodes = self.initial_trie_nodes()
        self.initial_neighbourhood()


    def generate_dict(self, alphabet):
        self.dictionery = {}
        i = 0
        for letter in alphabet:
            self.dictionery.update({letter: i})
            i += 1


    def initial_trie_nodes(self):
        self.trie = TrieNode()
        return self.trie.child_birth(self)

    
    def initial_neighbourhood(self):
        for node in self.nodes:
            neighbours = node.generate_neighbours()
            for neighbour in neighbours:
                if len(neighbour) >= self.kmin and len(neighbour) <= self.kmax:
                    nodebour = self.trie.find(neighbour)
                    node.add_neighbour(nodebour)


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



############################################

def main():
    print("generating GKmerHood (it will take a while)")
    gkhood = GKmerhood(5, 8)
    print("finished!")
    gkhood.generate_dataset(4)


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


def test_main():
    gkhood = GKmerhood(5, 7)

    sample = 'ATCTTA'
    print('test 1 : all neighbours of ' + sample)
    node = gkhood.trie.find(sample)
    print(len(node.neighbours))
    for each in node.neighbours:
        print(each.kmer)

##########################################################
# main function call
# main()