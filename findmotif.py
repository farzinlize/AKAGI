from TrieFind import TrieNode
from GKmerhood import GKmerhood
from misc import heap_encode, alphabet_to_dictionary
import os, platform, json
from time import time as currentTime


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
        with open(self.directory + self.tree[line][0] + '.data', 'r') as host:

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


    def get_position(self, kmer):

        # return None if there is no dataset
        if hasattr(self, 'gkhood'):
            return None

        line = heap_encode(kmer, self.dictionary) - self.metadata['bias']
        return self.tree[line]
        


'''
    motif finding function -> first version of motif-finding algorithm using gkhood
        an empty trie tree will save all seen kmers in sequence
        all frames of any sequences and its d-neighbours will be considered as seen kmers
        the trie will return motifs (kmers that are present in all sequences)

    [WARNING] function requires strings for d-neighbours kmer, but GKhoodTree class may provide Nodmers

    *************************** UPDATE *************************************
        function will return the whole motif tree for further processing
'''
# previous function definition :
# def find_motif_all_neighbours(gkhood_tree, dmax, frame_size, sequences, result_kmer=1, q=-1):

def find_motif_all_neighbours(gkhood_tree, dmax, frame_size, sequences):

    # define threshold to report progress
    PROGRESS_THRESHOLD = 100

    motifs_tree = TrieNode()
    for seq_id in range(len(sequences)):

        # progress value
        DSE_sum = 0
        A2T_sum = 0
        progress_time = currentTime()
        progress = 0
        print('processing sequence: ', seq_id)

        frame_start = 0
        frame_end = frame_size
        while frame_end < len(sequences[seq_id]):

            frame = sequences[seq_id][frame_start:frame_end]

            # dneighbours extraction
            now = currentTime()
            dneighbours = gkhood_tree.dneighbours(frame, dmax)
            dataset_extraction_time = currentTime() - now

            # adding motifs to tree
            now = currentTime()
            motifs_tree.add_frame(frame, seq_id, frame_start)
            for each in dneighbours:
                motifs_tree.add_frame(each[0], seq_id, frame_start)
            add_to_tree_time = currentTime() - now

            frame_start += 1
            frame_end += 1

            # average time calculation
            DSE_sum += dataset_extraction_time
            A2T_sum += add_to_tree_time

            progress += 1
            if progress == PROGRESS_THRESHOLD:
                print('progress checkout: ', currentTime() - progress_time, 'seconds')
                print('> DSE average: ', DSE_sum/progress, '\tA2T average: ', A2T_sum/progress)
                DSE_sum = 0
                A2T_sum = 0
                progress = 0
                progress_time = currentTime()

    # previous version return value
    # return motifs_tree.extract_motifs(q, result_kmer)

    return motifs_tree


# ########################################## #
#          chaining motifs section           #
# ########################################## #

def motif_chain(motifs, sequences, q=-1):

    if q == -1:
        q = len(sequences)

    on_sequence = on_sequence_found_structure(motifs, sequences, q)

    for motif in motifs:
        next_tree = TrieNode()
        for seq_id in motif.found_list[0]:
            for isomer_position in motif.found_list[1][seq_id]:
                next_position = isomer_position + motif.level
                if next_position >= len(sequences[seq_id]):
                    continue
                for next_motif in on_sequence[seq_id][next_position]:
                    next_tree.add_frame(next_motif, seq_id, next_position)
        for next_chain in next_tree.extract_motifs(q, 0):
            motif.add_chain(next_chain)

    

def on_sequence_found_structure(motifs, sequences, q):

    struct = [[[] for _ in range(len(sequence))] for sequence in sequences]

    for motif in motifs:
        for seq_id in motif.found_list[0]:
            for position in motif.found_list[1][seq_id]:
                struct[seq_id][position] += [motif]

    return struct


def chain_sort(motifs):
    for motif in motifs:
        if hasattr(motif, 'upchain'):
            continue


# extract sequences from a fasta file
def read_fasta(filename):
    sequences = []
    fasta = open(filename, 'r')
    for line in fasta:
        if line[0] == '>':
            continue
        sequences += [line[:-1]]
    return sequences


def sequence_dataset_files(filename, sequences, frame_size):
    tree = GKHoodTree('gkhood5_8', 'dataset')

    required_files_mask = [0 for i in range(tree.metadata['files'])]

    for sequence in sequences:
        frame_start = 0
        frame_end = frame_size
        while frame_end <= len(sequence):
            frame = sequence[frame_start:frame_end]
            file_index = int(tree.get_position(frame)[0])
            required_files_mask[file_index] += 1
            frame_start += 1
            frame_end += 1

    return [index for index in range(tree.metadata['files']) if required_files_mask[index] != 0]


# ########################################## #
#           main fucntion section            #
# ########################################## #

# real main function for finding motifs using a generated dataset
def main():
    sequences = read_fasta('data/Real/dm01r.fasta')
    tree = GKHoodTree('gkhood5_8', 'dataset')
    motifs = find_motif_all_neighbours(tree, 2, 6, sequences)
    print('number of motifs->', len(motifs))
    for motif in motifs:
        print(motif)


def main_required_files():
    sequences = read_fasta('data/Real/hm24r.fasta')
    req_files = sequence_dataset_files('dm01r.req', sequences, 7)
    print(len(req_files))
    print(req_files)


def test_main_2():
    tree = GKHoodTree('gkhood5_8', 'dataset')

    sample = 'GGGGGG'
    dn = tree.dneighbours(sample, 4)
    line = heap_encode(sample, tree.dictionary) - tree.metadata['bias']

    print('sample -> ', sample, ' line -> ', line)
    print(len(dn))
    for each in dn:
        if each[1] > 1:
            break
        print(each)

    print('##############################')

    sample_2 = 'AGCGCA'
    dn_2 = tree.dneighbours(sample_2, 1)
    line_2 = heap_encode(sample_2, tree.dictionary) - tree.metadata['bias']

    print('sample -> ', sample_2, ' line ->', line_2)
    print(len(dn_2))
    for each in dn_2:
        print(each)


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