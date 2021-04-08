from typing import List
from constants import FDR_SCORE, GOOD_HIT, POOL_LIMITED, POOL_SIZE, P_VALUE, SUMMIT
from misc import ExtraPosition, binary_add, binary_add_return_position, pwm_score_sequence
from TrieFind import ChainNode

class RankingPool:

    class Entity:
        def __init__(self, score, data:ChainNode):
            self.score = score
            self.data = data

        def __eq__(self, other):
            return self.score == other.score
        
        def __lt__(self, other):
            return self.score < other.score

    def __init__(self, function_argument, score_function, sign=1):
        self.args = function_argument
        self.scoreing = score_function
        self.pool: List[RankingPool.Entity] = []
        self.sign = sign

    
    def add(self, pattern:ChainNode):
        score = self.scoreing(pattern, self.args) * self.sign
        self.pool, rank = binary_add_return_position(self.pool, RankingPool.Entity(score, pattern), allow_equal=True)

        if POOL_LIMITED and len(self.pool) == POOL_SIZE + 1:
            # self.pool[-1].data.clear_foundmap()
            self.pool = self.pool[:-1]

        return rank

    
    def all_ranks_report(self, report_filename, sequences):
        with open(report_filename, 'w') as report:
            item:RankingPool.Entity
            for index, item in enumerate(self.pool):
                report.write('index:%d|score:%f\n%s\n'%(index, item.score, item.data.instances_str(sequences)))

    
    def top_ten_table(self):

        table = '[rank] "sequence"\tSCORE\n'

        if POOL_SIZE < 10:
            top = POOL_SIZE
        else:
            top = 10

        if len(self.pool) < top:
            top = len(self.pool)

        for rank in range(top):
            entity: RankingPool.Entity = self.pool[rank]
            table += '[%d] "%s"\t%.2f\n'%(rank, entity.data.label, entity.score * self.sign)

        return table

    
    def merge(self, other):
        
        merged = []
        self_index = 0 
        other_index = 0

        while self_index < len(self.pool) and other_index < len(other.pool) and len(merged) < POOL_SIZE:

            if self.pool[self_index] < other.pool[other_index]:
                merged.append(self.pool[self_index])
                self_index += 1

            elif self.pool[self_index] == other.pool[other_index]:
                merged.append(self.pool[self_index])

                # prevent adding same entities 
                if self.pool[self_index].data.label == other.pool[other_index].data.label:other_index += 1
                self_index += 1

            else:
                merged.append(other.pool[other_index])
                other_index += 1

        while self_index < len(self.pool) and len(merged) < POOL_SIZE:
            merged.append(self.pool[self_index])
            self_index += 1

        while other_index < len(other.pool) and len(merged) < POOL_SIZE:
            merged.append(other.pool[other_index])
            other_index += 1
        
        self.pool = merged


def objective_function_pvalue(pattern: ChainNode, sequences_bundles):
    foundlist_seq_vector = pattern.foundmap.get_list()[0]
    foundlist_index = 0
    sequence_index = 0
    psum = 0
    nsum = 0
    has_n = False

    while sequence_index < len(sequences_bundles):

        # + pscore
        if foundlist_index < len(foundlist_seq_vector) and foundlist_seq_vector[foundlist_index] == sequence_index:
            psum += sequences_bundles[sequence_index][P_VALUE]
            foundlist_index += 1
        
        # - nscore
        else:
            has_n = True
            nsum += sequences_bundles[sequence_index][P_VALUE]

        sequence_index += 1

    if has_n:
        nscore = (nsum/(len(sequences_bundles)-len(foundlist_seq_vector)))
    else:
        nscore = 0

    return (psum/len(foundlist_seq_vector)) - nscore


def distance_to_summit_score(pattern: ChainNode, sequences_bundles):
    pattern_foundlist = pattern.foundmap.get_list()
    sum_distances = 0
    num_instances = 0
    for index, seq_id in enumerate(pattern_foundlist[0]):

        if seq_id >= len(sequences_bundles):
            print('[ERROR] seq_id=%d out of range (len=%d)'%(seq_id, len(sequences_bundles)))
            continue

        position: ExtraPosition
        for position in pattern_foundlist[1][index]:
            end_index = position.end_position() # int(position) + len(pattern.label)
            start_index = position.start_position
            # if len(position.chain) != 0:
            #     start_index = position.chain[0]
            mid_index = (end_index + start_index)//2
            sum_distances += abs(sequences_bundles[seq_id][SUMMIT] - mid_index)
            num_instances += 1
    return sum_distances / num_instances
    

def pwm_score(pattern: ChainNode, arg_bundle):

    # unpacking arguments
    sequences = arg_bundle[0]
    pwm = arg_bundle[1]
    
    aggregated = 0
    count = 0
    bundle = pattern.foundmap.get_list()
    for index, seq_id in enumerate(bundle[0]):
        position: ExtraPosition
        for position in bundle[1][index]:
            end = position.end_position()
            start = position.start_position
            sequence = sequences[seq_id][start:end]
            score, _ = pwm_score_sequence(sequence, pwm)
            aggregated += score
            count += 1
    return aggregated / count