from typing import List
from TrieFind import ChainNode, WatchNode
from findmotif import find_motif_all_neighbours
from GKmerhood import GKHoodTree
from constants import DATASET_TREES, EXTRACT_OBJ, INT_SIZE_BIT, MARGIN_KEY, MOTIF_KEY, POSITION_KEY, SEQUENCE_KEY
from onSequence import OnSequenceDistribution
from misc import ExtraPosition, read_fasta

class CMap:

    def __init__(self, on_sequence:OnSequenceDistribution):

        self.get = [[[] for _ in sequence] for sequence in on_sequence.struct]

        self.array = []
        self.seq_start_indexes = []

        bit_index = 0
        compressed_int = []
        wasted_bits = 0

        for seq_id in range(len(on_sequence.struct)):

            self.seq_start_indexes += [len(self.array)]

            for position in range(len(on_sequence.struct[seq_id])):
                for motif_label, margin in zip(on_sequence.struct[seq_id][position], on_sequence.margins[seq_id][position]):

                    compressed_int += [{SEQUENCE_KEY:seq_id, POSITION_KEY:position, MOTIF_KEY:motif_label, MARGIN_KEY:margin}]
                    self.get[seq_id][position] += [(bit_index, len(self.array))]
                    bit_index += 1

                    if bit_index == INT_SIZE_BIT:
                        self.array += [compressed_int[:]]
                        compressed_int = []
                        bit_index = 0

            if compressed_int:

                while bit_index != INT_SIZE_BIT:
                    compressed_int += [{SEQUENCE_KEY:-1, POSITION_KEY:-1, MOTIF_KEY:'', MARGIN_KEY:0}]
                    bit_index += 1
                    wasted_bits += 1

                self.array += [compressed_int[:]]
                compressed_int = []
                bit_index = 0

            # if len(self.seq_start_indexes) == 0:
            #     self.seq_start_indexes += [len(self.array)]
            # else:
            #     self.seq_sizes += [len(self.array)-self.seq_sizes[-1]]

        print(wasted_bits)


def generates_zero_motifs_mask(motifs:List[WatchNode], data_map:CMap):

    motif_masks = []

    for motif in motifs:
        mask = [0 for _ in range(len(data_map.array))]
        bundle = motif.foundmap.get_list()
        for index, seq_id in enumerate(bundle[0]):
            position: ExtraPosition
            for position in bundle[1][index]:
                for bit, index_array in data_map.get[seq_id][position.start_position]:
                    if data_map.array[index_array][bit][MOTIF_KEY] == motif.label:
                        mask[index_array] |= 1<<(INT_SIZE_BIT-bit-1)
        motif_masks += [mask[:]]
    
    return motif_masks



def next_position_mask_from_picture(chain_node: ChainNode, hit_positions, data_map:CMap, overlap, gap, hit_motif_label):
    
    picture = [0 for _ in range(len(data_map.array))]

    for seq_index, uint in enumerate(hit_positions):
        for bit_index, bit in enumerate("{0:b}".format(int(uint))):
            if bit == '1':
                seq_id = data_map.array[seq_index][bit_index][SEQUENCE_KEY]
                position = data_map.array[seq_index][bit_index][POSITION_KEY]
                position_margin = data_map.array[seq_index][bit_index][MARGIN_KEY]
                for sliding in [i for i in range(-overlap, gap+1)]:
                    # next_position = position + len(chain_node.label) + len(hit_motif_label) + sliding
                    next_position = position + position_margin + len(hit_motif_label) + sliding
                    if next_position >= len(data_map.get[seq_id]):continue
                    for next_bit, next_index in data_map.get[seq_id][next_position]:
                        picture[next_index] |= 1<<(INT_SIZE_BIT-next_bit-1)
    
    return picture


def position_mask_from_foundmap(chain_node: ChainNode, data_map: CMap, overlap, gap):
    
    picture = [0 for _ in range(len(data_map.array))]

    bundle = chain_node.foundmap.get_list()
    for index_seq, seq_id in enumerate(bundle[0]):
        position: ExtraPosition
        for position in bundle[1][index_seq]:
            for sliding in [i for i in range(-overlap, gap+1)]:
                next_position = position.end_position() + sliding
                if next_position >= len(data_map.get[seq_id]):continue
                for bit, index in data_map.get[seq_id][next_position]:
                    picture[index] |= 1<<(INT_SIZE_BIT-bit-1)

    return picture
    

# ########################################## #
#             test functions                 #
# ########################################## #

def test_picture_factory():
    pass


def test_main():
    dataset_name = 'hmchipdata/Human_hg18_peakcod/ENCODE_HAIB_A549_Dex500pM_NR3C1_peak'
    gkhood_index = 1
    d = 1
    frame_size = 6

    sequences = read_fasta('%s.fasta'%(dataset_name))
    tree = GKHoodTree(DATASET_TREES[gkhood_index][0], DATASET_TREES[gkhood_index][1])
    motif_tree = find_motif_all_neighbours(tree, d, frame_size, sequences)
    motifs = motif_tree.extract_motifs(motif_tree.find_max_q(), result_kmer=EXTRACT_OBJ)

    on_sequence = OnSequenceDistribution(motifs, sequences)
    data_map = CMap(on_sequence)

    return on_sequence, data_map


if __name__ == "__main__":
    dataset_name = 'hmchipdata/Human_hg18_peakcod/ENCODE_HAIB_A549_Dex500pM_NR3C1_peak'
    gkhood_index = 1
    d = 1
    frame_size = 6

    sequences = read_fasta('%s.fasta'%(dataset_name))
    tree = GKHoodTree(DATASET_TREES[gkhood_index][0], DATASET_TREES[gkhood_index][1])
    motif_tree = find_motif_all_neighbours(tree, d, frame_size, sequences)
    motifs = motif_tree.extract_motifs(motif_tree.find_max_q(), result_kmer=EXTRACT_OBJ)

    on_sequence = OnSequenceDistribution(motifs, sequences)
    data_map = CMap(on_sequence)

    motif_masks = generates_zero_motifs_mask(motifs, data_map)

    motif:WatchNode = motifs[0]
    mask = motif_masks[0]

    print('motif -> %s'%motif.label)
    position_mask = position_mask_from_foundmap(ChainNode(motif.label, motif.foundmap), data_map, 3, 2)
