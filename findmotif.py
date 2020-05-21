from TrieFind import TrieNode
from GKmerhood import GKmerhood

class GKHoodTree:
    def __init__(self, filename='', gkhood=None):
        if gkhood != None:
            self.gkhood = gkhood
    

    def dneighbours_mem(self, kmer, dmax):
        node = self.gkhood.trie.find(kmer)
        return node.dneighbours(dmax)


    def dneighbours(self, kmer, dmax):
        if hasattr(self, 'gkhood'):
            return self.dneighbours_mem(kmer, dmax)

        

def find_motif_all_neighbours(gkhood_tree, dmax, fram_size, sequences):
    motifs_tree = TrieNode()
    for seq_id in range(len(sequences)):
        frame_start = 0
        frame_end = fram_size
        while frame_end < len(sequences[seq_id]):
            frame = sequences[seq_id][frame_start:frame_end]
            dneighbours = gkhood_tree.dneighbours(frame, dmax)
            motifs_tree.add_frame(frame, seq_id)
            for each in dneighbours:
                motifs_tree.add_frame(each[0].kmer, seq_id)
            frame_start += 1
            frame_end += 1
    return motifs_tree.extract_motif(len(sequences))


def read_fasta(filename):
    sequences = []
    fasta = open(filename, 'r')
    for line in fasta:
        if line[0] == '>':
            continue
        sequences += [line]
    return sequences


def main():
    print('generating gkhood (it will take some time)')
    gkhood = GKmerhood(5, 8)
    print('gkhood is generated successfully')
    sequences = read_fasta('data/Real/dm01r.fasta')
    tree = GKHoodTree(gkhood=gkhood)
    motifs = find_motif_all_neighbours(tree, 3, 7, sequences)
    print('number of motifs->', len(motifs))
    print(motifs)

main()