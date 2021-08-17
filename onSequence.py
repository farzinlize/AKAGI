from checkpoint import load_collection
from constants import DATABASE_NAME
import pickle
from mongo import get_client
from typing import List
from TrieFind import ChainNode
from misc import ExtraPosition


'''
    generate a 3-dimensional list to access motifs that occurs at a specific location
        dimensions are described below:
            1. sequence_id -> there is a list for any sequence
            2. position -> there is a list of motifs for any position on a specific sequence
            3. motif -> reference for motifs that occurs at a specific location (position) and a specific sequence
'''
class OnSequenceDistribution:

    def __init__(self, motifs=None, sequences=None, struct=None, compressed_data=None):
        if struct:
            self.struct = struct
        elif compressed_data:
            self.read_file(compressed_data)
        else:
            assert motifs and sequences
            self.generate_list(motifs, sequences)


    def read_file(self, filename):
        with open(filename, 'rb') as c:self.struct = pickle.load(c)
        

    def compress(self, filename):
        with open(filename, 'wb') as c:pickle.dump(self.struct, c)


    def generate_list(self, motifs: List[ChainNode], sequences):
        client = get_client()
        self.struct = [[[] for _ in range(len(sequence))] for sequence in sequences] 
        for motif in motifs:

            try   :bundle = motif.foundmap.get_list(client=client)
            except:bundle = motif.foundmap.get_list()

            if not isinstance(bundle, list):
                if bundle:raise bundle
                raise Exception(f'no data was found for motif address -> {motif.foundmap.address}')

            for index, seq_id in enumerate(bundle[0]):
                position: ExtraPosition
                for position in bundle[1][index]:
                    try:
                        self.struct[seq_id][position.start_position] += [motif.label]
                    except IndexError:
                        print('[ERROR] IndexError raised | seq_id=%d, position=%d, len(sequence[index])=%d'%(
                            seq_id, position.start_position, len(sequences[index])
                        ))
        client.close()
                

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


if __name__ == '__main__':
    pass