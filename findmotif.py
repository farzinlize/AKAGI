from TrieFind import TrieNode
from GKmerhood import GKmerhood
from misc import heap_encode, alphabet_to_dictionary
import os, platform, json


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
            # file address spliter is different in windows and linux
            operating_system = platform.system()
            if operating_system == 'Windows':
                spliter = '\\'
            else:   # operating_system == 'Linux'
                spliter = '/'

            self.read_metadata(filename)
            self.read_tree(filename)
            self.directory = os.getcwd() + spliter + directory_name + spliter
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
        node = self.gkhood.trie.find(kmer)
        return node.dneighbours(dmax)


    def dneighbours(self, kmer, dmax):

        # from memory
        if hasattr(self, 'gkhood'):
            return self.dneighbours_mem(kmer, dmax)

        # from dataset
        line = heap_encode(kmer, self.dictionary) - self.metadata['bias']
        dn_length = self.tree[line+1][1] - self.tree[line][1]
        dneghbours = []
        with open(self.directory + self.tree[line][0], 'r') as host:

            # skip lines
            for _ in range(self.tree[line][1]):
                next(host)
            
            # read part
            for _ in range(dn_length):
                line_data = host.readline().split()
                if int(line_data[1]) > dmax:
                    break
                dneghbours += [(line_data[0], int(line_data[1]))]
        
        return dneghbours

        

'''
    motif finding function -> first version of motif-finding algorithm using gkhood
        an empty trie tree will save all seen kmers in sequence
        all frames of any sequences and its d-neighbours will be considered as seen kmers
        the trie will return motifs (kmers that are present in all sequences)
'''
def find_motif_all_neighbours(gkhood_tree, dmax, frame_size, sequences):
    motifs_tree = TrieNode()
    for seq_id in range(len(sequences)):
        frame_start = 0
        frame_end = frame_size
        while frame_end < len(sequences[seq_id]):
            frame = sequences[seq_id][frame_start:frame_end]
            dneighbours = gkhood_tree.dneighbours(frame, dmax)
            motifs_tree.add_frame(frame, seq_id)
            for each in dneighbours:
                motifs_tree.add_frame(each[0].kmer, seq_id)
            frame_start += 1
            frame_end += 1
    return motifs_tree.extract_motif(len(sequences))



# extract sequences from a fasta file
def read_fasta(filename):
    sequences = []
    fasta = open(filename, 'r')
    for line in fasta:
        if line[0] == '>':
            continue
        sequences += [line]
    return sequences

# ########################################## #
#           main fucntion section            #
# ########################################## #

# real main function for finding motifs using gkhood object in memory
def main():
    print('generating gkhood (it will take some time)')
    gkhood = GKmerhood(5, 8)
    print('gkhood is generated successfully')
    sequences = read_fasta('data/Real/dm01r.fasta')
    tree = GKHoodTree(gkhood=gkhood)
    motifs = find_motif_all_neighbours(tree, 3, 7, sequences)
    print('number of motifs->', len(motifs))
    print(motifs)


def test_json_read():
    with open('gkhood5_8.metadata', 'r') as meta:
        data = json.load(meta)
        print(data['kmin'])
        print(data['kmin'] + data['bias'])
        print(type(data['alphabet']))


# testing read_fasta
def test_main():
    sequences = sequences = read_fasta('data/Real/dm01r.fasta')
    print(sequences)


# ########################################## #
#           main fucntion call               #
# ########################################## #

# main function call
if __name__ == "__main__":
    main()