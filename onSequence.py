from TrieFind import WatchNode
from misc import ExtraPosition


'''
    generate a 3-dimensional list to access motifs that occurs at a specific location
        dimensions are described below:
            1. sequence_id -> there is a list for any sequence
            2. position -> there is a list of motifs for any position on a specific sequence
            3. motif -> reference for motifs that occurs at a specific location (position) and a specific sequence
'''
class OnSequenceDistribution:

    class Entry:
        def __init__(self, label, end_margin):
            self.label = label
            self.end_margin = end_margin

    def __init__(self, motifs, sequences):
        self.struct = self.generate_list(motifs, sequences)

    def generate_list(self, motifs: list[WatchNode], sequences):
        struct = [[[] for _ in range(len(sequence))] for sequence in sequences]
        for motif in motifs:
            bundle = motif.foundmap.get_list()
            for index, seq_id in enumerate(bundle[0]):
                position: ExtraPosition
                for position in bundle[1][index]:
                    try:
                        struct[seq_id][position.start_position] += [self.Entry(motif.label, position.end_margin)]
                    except IndexError:
                        print('[ERROR] IndexError raised | seq_id=%d, position=%d, len(sequence[index])=%d'%(
                            seq_id, position.start_position, len(sequences[index])
                        ))
        return struct