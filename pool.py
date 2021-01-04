from constants import FDR_SCORE, P_VALUE
from misc import ExtraPosition, binary_add
from TrieFind import TrieNode

class RankingPool:

    class Entity:
        def __init__(self, score, data):
            self.score = score
            self.data = data

        def __eq__(self, other):
            return self.score == other.score
        
        def __lt__(self, other):
            return self.score < other.score

    def __init__(self, sequences_bundle, score_function):
        self.bundles = sequences_bundle
        self.scoreing = score_function
        self.pool = []

    
    def add(self, pattern:TrieNode):
        score = self.scoreing(pattern, self.bundles)
        self.pool = binary_add(self.pool, RankingPool.Entity(score, pattern))

    
    def all_ranks_report(self, report_filename, sequences):
        with open(report_filename, 'w') as report:
            item:RankingPool.Entity
            for index, item in enumerate(self.pool):
                report.write('index:%d|score:%f\n%s\n'%(index, item.score, item.data.instances_str(sequences)))
            

def objective_function_pvalue(pattern: TrieNode, sequences_bundles):
    foundlist_seq_vector = pattern.foundmap.get_list()[0]
    foundlist_index = 0
    sequence_index = 0
    psum = 0
    nsum = 0
    while sequence_index < len(sequences_bundles):
        if foundlist_seq_vector[foundlist_index] == sequence_index: # hit
            psum += sequences_bundles[sequence_index][P_VALUE]
            foundlist_index += 1
        else:   # miss
            nsum += sequences_bundles[sequence_index][P_VALUE]
        sequence_index += 1
    return (psum/len(foundlist_seq_vector)) \
        - (nsum/(len(sequences_bundles)-len(foundlist_seq_vector)))


def distance_to_summit_score(pattern: TrieNode, sequences_bundles):
    pass


