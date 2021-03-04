from typing import List
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

    # class Entry:
    #     def __init__(self, label):
    #         self.label = label

    def __init__(self, motifs, sequences):
        self.generate_list(motifs, sequences)

    def generate_list(self, motifs: List[WatchNode], sequences):
        self.struct = [[[] for _ in range(len(sequence))] for sequence in sequences]
        for motif in motifs:
            bundle = motif.foundmap.get_list()
            for index, seq_id in enumerate(bundle[0]):
                position: ExtraPosition
                for position in bundle[1][index]:
                    try:
                        self.struct[seq_id][position.start_position] += [motif.label]
                    except IndexError:
                        print('[ERROR] IndexError raised | seq_id=%d, position=%d, len(sequence[index])=%d'%(
                            seq_id, position.start_position, len(sequences[index])
                        ))

    def analysis(self):
        result = '[OnSequence][Analysis] id -> sequence id | z -> number of motifs in positions vector\n'
        total = 0
        for seq_id in range(len(self.struct)):
            z = sum([len(positionlist) for positionlist in self.struct[seq_id]])
            total += z
            result += 'id:%d|z=%d\n'%(seq_id, z)
        return result + '[OnSequence][Analysis] total=%d\n'%total