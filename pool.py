from FoundMap import FileMap
import struct
from typing import List
from constants import APPDATA_PATH, CR_TABLE_HEADER_JASPAR, CR_TABLE_HEADER_SSMART, CR_TABLE_HEADER_SUMMIT, INT_SIZE, POOL_LIMITED, POOL_SIZE, PWM, P_VALUE, SEQUENCES, SEQUENCE_BUNDLES, SUMMIT, FUNCTION_KEY, ARGUMENT_KEY, SIGN_KEY, TABLE_HEADER_KEY, TOP_TEN_REPORT_HEADER
from misc import ExtraPosition, binary_add_return_position, bytes_to_int, int_to_bytes, make_location, pwm_score_sequence
from TrieFind import ChainNode

class AKAGIPool:

    class Entity:
        def __init__(self, data:ChainNode, scores):
            self.data = data
            self.scores = scores
            self.sorted_by = None

        def __eq__(self, other):
            if self.sorted_by != None:
                return self.scores[self.sorted_by] == other.scores[self.sorted_by]
            else:raise Exception('sorted by is not configured for comparison')

        def __lt__(self, other):
            if self.sorted_by != None:
                return self.scores[self.sorted_by] < other.scores[self.sorted_by]
            else:raise Exception('sorted by is not configured for comparison')


    def __init__(self, pool_descriptions):
        self.descriptions = pool_descriptions
        self.tables: list[list[AKAGIPool.Entity]] = []
        for _ in pool_descriptions:self.tables.append([])

    
    def judge(self, pattern:ChainNode):

        # calculating pattern scores
        scores = []
        for description in self.descriptions:
            scores.append(description[FUNCTION_KEY](pattern, description[ARGUMENT_KEY]) * description[SIGN_KEY])

        # inserting the pattern to each sorted table for each score
        ranks = []
        entity = self.Entity(pattern, scores)
        for sorted_by, table in enumerate(self.tables):
            entity.sorted_by = sorted_by
            table, rank = binary_add_return_position(table, entity)
            
            if rank == POOL_SIZE:ranks.append(-1)
            else:ranks.append(rank)

            if POOL_LIMITED and len(table) == POOL_SIZE + 1:
                table = table[:-1]

            self.tables[sorted_by] = table
        
        return ranks
    

    def top_ten_reports(self):
        report = TOP_TEN_REPORT_HEADER

        if POOL_SIZE < 10:
            global_top = POOL_SIZE
        else:
            global_top = 10

        for sorted_by, table in enumerate(self.tables):
            report += self.descriptions[sorted_by][TABLE_HEADER_KEY]
            report += '> table count -> %d\n'%len(table)

            if len(table) < global_top:
                top = len(table)
            else:
                top = global_top

            # top ranks
            for rank in range(top):
                entity: AKAGIPool.Entity = table[rank]
                report += '[%d] "%s"\t'%(rank, entity.data.label)
                for index, score in enumerate(entity.scores):
                    report += '%.2f\t'%(score * self.descriptions[index][SIGN_KEY])
                report += '\n'

            # last rank
            if len(table) > top:
                entity: AKAGIPool.Entity = table[-1]
                report += '...\n[%d] "%s"\t'%(len(table)-1, entity.data.label)
                for index, score in enumerate(entity.scores):
                    report += '%.2f\t'%(score * self.descriptions[index][SIGN_KEY])
                report += '\n'
        
        return report


    def merge(self, other):

        assert len(self.tables) == len(other.tables)

        for sorted_by, self_table, other_table in zip([i for i in range(len(self.tables))], self.tables, other.tables):

            if len(other_table) == 0:
                print('[POOL] empty merge request on table index of %d (sorted_by)'%sorted_by)
                continue

            merged = []
            self_index = 0 
            other_index = 0

            while self_index < len(self_table) and other_index < len(other_table) and len(merged) < POOL_SIZE:

                self_table[self_index].sorted_by = sorted_by
                other_table[other_index].sorted_by = sorted_by

                if self_table[self_index] < other_table[other_index]:
                    merged.append(self_table[self_index])
                    self_index += 1

                elif self_table[self_index] == other_table[other_index]:
                    merged.append(self_table[self_index])

                    # prevent adding same entities 
                    if self_table[self_index].data.label == other_table[other_index].data.label:other_index += 1
                    self_index += 1

                else:
                    merged.append(other_table[other_index])
                    other_index += 1

            while self_index < len(self_table) and len(merged) < POOL_SIZE:
                merged.append(self_table[self_index])
                self_index += 1

            while other_index < len(other_table) and len(merged) < POOL_SIZE:
                merged.append(other_table[other_index])
                other_index += 1

            self.tables[sorted_by] = merged


    # ########################################## #
    #            pool disk operations            #
    # ########################################## #

    def savefile(self, filename:str):
        pool_collection = filename.split('.')[0]

        seen = []
        with open(filename, 'wb') as disk:
            for table in self.tables:
                disk.write(int_to_bytes(len(table)))

                for entity in table:

                    first = entity.data.label not in seen # TODO [WARNING] linear search 
                    if first:seen.append(entity.data.label)

                    scores_pack = struct.pack('d'*len(entity.scores), *entity.scores)
                    disk.write(
                        int_to_bytes(len(scores_pack)) +
                        scores_pack +
                        entity.data.to_byte(protect=first, directory=pool_collection)
                    )


    def readfile(self, filename:str):
        pool_collection = filename.split('.')[0]

        with open(filename, 'rb') as disk:
            for table_index in range(len(self.tables)):
                table_len = bytes_to_int(disk.read(INT_SIZE))

                for _ in range(table_len):
                    pack_len = bytes_to_int(disk.read(INT_SIZE))
                    scores = list(struct.unpack('d'*len(self.descriptions), disk.read(pack_len)))
                    pattern = ChainNode.byte_to_object(disk, collection=pool_collection)
                    self.tables[table_index].append(AKAGIPool.Entity(pattern, scores))


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

    while sequence_index < len(sequences_bundles):

        # + pscore
        if foundlist_index < len(foundlist_seq_vector) and foundlist_seq_vector[foundlist_index] == sequence_index:
            psum += sequences_bundles[sequence_index][P_VALUE]
            foundlist_index += 1
        
        # - nscore
        else:nsum += sequences_bundles[sequence_index][P_VALUE]

        sequence_index += 1

    if nsum != 0:
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
    pwm = arg_bundle[1][0]
    r_pwm = arg_bundle[1][1]
    
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
            r_score, _ = pwm_score_sequence(sequence, r_pwm)
            aggregated += max(score, r_score)
            count += 1
    return aggregated / count


def get_AKAGI_pools_configuration(dataset_dict=None):

    if not dataset_dict:
        return [ 
                # ssmart table configuration
                {FUNCTION_KEY:objective_function_pvalue, 
                ARGUMENT_KEY:None, 
                SIGN_KEY:-1, 
                TABLE_HEADER_KEY:CR_TABLE_HEADER_SSMART}, 

                # summit table configuration
                {FUNCTION_KEY:distance_to_summit_score, 
                ARGUMENT_KEY:None, 
                SIGN_KEY:1, 
                TABLE_HEADER_KEY:CR_TABLE_HEADER_SUMMIT}, 
                
                # jaspar table configuration
                {FUNCTION_KEY:pwm_score, 
                ARGUMENT_KEY:(None,None), 
                SIGN_KEY:-1, 
                TABLE_HEADER_KEY:CR_TABLE_HEADER_JASPAR}
            ]

    # unpacking dataset dictionary
    sequences = dataset_dict[SEQUENCES]
    bundles = dataset_dict[SEQUENCE_BUNDLES]
    pwm = dataset_dict[PWM]

    return [ 
                # ssmart table configuration
                {FUNCTION_KEY:objective_function_pvalue, 
                ARGUMENT_KEY:bundles, 
                SIGN_KEY:-1, 
                TABLE_HEADER_KEY:CR_TABLE_HEADER_SSMART}, 

                # summit table configuration
                {FUNCTION_KEY:distance_to_summit_score, 
                ARGUMENT_KEY:bundles, 
                SIGN_KEY:1, 
                TABLE_HEADER_KEY:CR_TABLE_HEADER_SUMMIT}, 
                
                # jaspar table configuration
                {FUNCTION_KEY:pwm_score, 
                ARGUMENT_KEY:(sequences,pwm), 
                SIGN_KEY:-1, 
                TABLE_HEADER_KEY:CR_TABLE_HEADER_JASPAR}
            ]


if __name__ == '__main__':
    pooly = AKAGIPool(get_AKAGI_pools_configuration({SEQUENCES:'', SEQUENCE_BUNDLES:'', PWM:''}))

    a = FileMap()
    a.add_location(0, ExtraPosition(6, 4))
    a.add_location(0, ExtraPosition(6, 4))
    a.add_location(1, ExtraPosition(6, 4))
    a.add_location(2, ExtraPosition(6, 4))
    a.add_location(2, ExtraPosition(6, 4))
    a.add_location(3, ExtraPosition(6, 4))

    b = FileMap()
    b.add_location(0, ExtraPosition(8, 3))
    b.add_location(1, ExtraPosition(8, 3))
    b.add_location(1, ExtraPosition(8, 3))
    b.add_location(2, ExtraPosition(8, 3))
    b.add_location(2, ExtraPosition(8, 3))
    b.add_location(5, ExtraPosition(8, 3))

    pa = ChainNode('ATCGCCC', a)
    pb = ChainNode('TTCGAG', b)

    eb = AKAGIPool.Entity(pb, [12.67, 1.2, 6.7])
    ea = AKAGIPool.Entity(pa, [2.4, 5.7, 3.9])

    pooly.tables[0].append(ea)
    pooly.tables[1].append(ea)
    pooly.tables[2].append(ea)

    pooly.tables[0].append(eb)
    pooly.tables[1].append(eb)
    pooly.tables[2].append(eb)

    pooly.savefile()

    pooly_disk = AKAGIPool(get_AKAGI_pools_configuration({SEQUENCES:'', SEQUENCE_BUNDLES:'', PWM:''}))
    pooly_disk.readfile()