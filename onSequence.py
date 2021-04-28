import pickle
from ast import Bytes
from checkpoint import load_checkpoint
from constants import BRIEFING, INT_SIZE
from io import BufferedReader
from socket import socket
from typing import List
from TrieFind import WatchNode
from misc import ExtraPosition, brief_sequence, int_to_bytes, read_bundle, read_fasta


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
        self.margins = [[[] for _ in range(len(sequence))] for sequence in sequences]
        for motif in motifs:
            bundle = motif.foundmap.get_list()
            for index, seq_id in enumerate(bundle[0]):
                position: ExtraPosition
                for position in bundle[1][index]:
                    try:
                        self.struct[seq_id][position.start_position] += [motif.label]
                        self.margins[seq_id][position.start_position] += [position.size]
                    except IndexError:
                        print('[ERROR] IndexError raised | seq_id=%d, position=%d, len(sequence[index])=%d'%(
                            seq_id, position.start_position, len(sequences[index])
                        ))


    def to_byte(self):
        result = int_to_bytes(len(self.struct))
        for sequence in self.struct:
            result += int_to_bytes(len(sequence))
            for positionlist in sequence:
                result += len(positionlist)
                for position in positionlist:
                    result += int_to_bytes(len(position))
                    result += bytes(position)
        return result


    @staticmethod
    def byte_to_object(buffer:BufferedReader):
        raise NotImplementedError


    def analysis(self):
        result = '[OnSequence][Analysis] id -> sequence id | z -> number of motifs in positions vector\n'
        total = 0
        position_without_motif = 0
        for seq_id in range(len(self.struct)):
            z = sum([len(positionlist) for positionlist in self.struct[seq_id]])
            if z == 0:
                position_without_motif += 1
            total += z
            result += 'id:%d|z=%d\n'%(seq_id, z)
        return result + '[OnSequence][Analysis] total=%d\t|\tempty positions -> %d\n'%(total, position_without_motif)


def test():
    checkpoint = 'ENCODE_HAIB_GM12878_SRF_peak_f5-6_d1-1.checkpoint'
    dataset_name = 'hmchipdata/Human_hg18_peakcod/ENCODE_HAIB_GM12878_SRF_peak'
    motifs = load_checkpoint(checkpoint)
    sequences = read_fasta('%s.fasta'%(dataset_name))
    bundles = read_bundle('%s.bundle'%(dataset_name))

    if BRIEFING:
        sequences, bundles = brief_sequence(sequences, bundles)
        assert len(sequences) == len(bundles)
        print('[BRIEFING] number of sequences = %d'%len(sequences))

    on_sequence = OnSequenceDistribution(motifs, sequences)
    with open('test.pickle', 'wb') as f:
        pickle.dump(398, f)
        pickle.dump('salam', f)
        pickle.dump(on_sequence, f)
        f.write(b'\xff\xaa')
    with open('test.pickle', 'rb') as f:
        numq = pickle.load(f)
        test = pickle.load(f)
        assert test == 'salam'
        assert numq == 398
        on_pickled = pickle.load(f)
        assert f.read(1) == b'\xff'
        assert f.read(1) == b'\xaa'

    return on_sequence, on_pickled


if __name__ == '__main__':
    o, p = test()