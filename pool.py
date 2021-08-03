from io import BytesIO
from mongo import get_client, safe_operation
import struct
from typing import List
from FoundMap import FileMap
from constants import BYTE_PATTERN, CR_TABLE_HEADER_JASPAR, CR_TABLE_HEADER_SSMART, CR_TABLE_HEADER_SUMMIT, DATABASE_NAME, DROP, FIND_ONE, IMPORTANT_LOG, INSERT_ONE, INT_SIZE, POOLS_COLLECTION, POOL_LIMITED, POOL_NAME, POOL_SIZE, POOL_TAG, PWM, P_VALUE, SCORES, SEQUENCES, SEQUENCE_BUNDLES, SUMMIT, FUNCTION_KEY, ARGUMENT_KEY, SIGN_KEY, TABLES, TABLE_HEADER_KEY, TOP_TEN_REPORT_HEADER, UPDATE
from misc import ExtraPosition, binary_add_return_position, bytes_to_int, int_to_bytes, pwm_score_sequence
from TrieFind import ChainNode, initial_chainNodes

class AKAGIPool:

    class Entity:
        def __init__(self, data:ChainNode=None, scores=None, document=None, collection_name=None):
            if document:
                self.read_document(document, collection_name)
            else:
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

        def documented(self):
            return {BYTE_PATTERN:self.data.to_byte(), SCORES:self.scores}

        def read_document(self, document, collection_name):
            self.data = ChainNode.byte_to_object(BytesIO(document[BYTE_PATTERN]), collection=collection_name)
            self.scores = document[SCORES]


    def __init__(self, pool_descriptions, collection_name='default_pool'):
        self.descriptions = pool_descriptions
        self.tables: list[list[AKAGIPool.Entity]] = []
        self.collection_name = collection_name
        for _ in pool_descriptions:self.tables.append([])

    
    def judge(self, pattern:ChainNode, mongo_client=None):

        # calculating pattern scores
        scores = []
        for description in self.descriptions:
                new_score = description[FUNCTION_KEY](pattern, description[ARGUMENT_KEY], mongo_client) * description[SIGN_KEY]
                if not isinstance(new_score, float):
                    with open(IMPORTANT_LOG, 'a') as log:log.write(f'[JUDGE] error was occurred while judging pattern:{pattern.label}\n')
                    return new_score # as error
                scores.append(new_score)

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

    def to_document(self):
        document = {POOL_NAME:self.collection_name}

        documented_tables = []
        for table in self.tables:
            documented_tables.append([entity.documented() for entity in table])

        document.update({TABLES:documented_tables})
        return document


    '''
    create a snap-shot of all current pool data including ChainNode objects
        can restore object capable of restoring patterns foundmap and their calculated scores

        TASKS:
            1. preserve data to locate all pattern appearances (foundmaps) in seperated collection
                - first drop the related collection if exist then initial gathered unique chain nodes on that collection
            2. save object in pool collection
            3. save object in file with byte conversion (redundant backup to recover data from chaotic working collection)
    '''
    def save(self, mongo_client=None):

        if not mongo_client:mongo_client = get_client();should_close = True
        else                                           :should_close = False

        # # # # # #    TASK.1   # # # # # #
        #         preserve data           #
        # # # # # # # # # # # # # # # # # #

        collection = mongo_client[DATABASE_NAME][self.collection_name]

        # droping older version collection
        error = safe_operation(collection, DROP)
        if error:
            with open(IMPORTANT_LOG, 'a') as log:log.write(f'[POOL][DROP] error: {error}\n')

        # gather data (chain nodes)
        collected_patterns:List[ChainNode] = []
        seen = []

        for table in self.tables:
            for entity in table:
                first = entity.data.label not in seen
                if first:
                    seen.append(entity.data.label)
                    collected_patterns.append(entity.data)

        # preserve data on seperated collection
        new_patterns = initial_chainNodes([(pattern.label, pattern.foundmap) for pattern in collected_patterns], 
                                            self.collection_name, 
                                            client=mongo_client)

        # - if database failed there will be no replacement of chain_nodes
        #   [WARNING] preserve default collection data in order to object file to be valid
        if not isinstance(new_patterns, list):
            new_patterns = collected_patterns
            with open(IMPORTANT_LOG, 'a') as log:
                log.write(f'[WARNING][POOL] preserve default collection data in order to {self.collection_name+POOL_TAG} to be valid\n')

        # # # # # #    TASK.3   # # # # # #
        #      saving pool in file        #
        #   (also replace new objects)    #
        # # # # # # # # # # # # # # # # # #

        # again but this time put those maps instead of the older ones and save objects
        seen = [] 
        newdata_iterator = iter(new_patterns)

        with open(self.collection_name+POOL_TAG, 'wb') as disk:
            for table in self.tables:
                disk.write(int_to_bytes(len(table)))
                for entity in table:
                    first = entity.data.label not in seen # TODO [WARNING] linear search 
                    if first:
                        newdata = next(newdata_iterator)

                        # check for algorithm error (can be removed in future)
                        if entity.data.label != newdata.label:
                            with open(IMPORTANT_LOG, 'a') as log:
                                log.write(f'[POOL][ERROR] gathered data in contrast of new data\n{entity.data.label} != {newdata.label}\n')
                            if should_close:mongo_client.close()
                            raise Exception('can not sort data as it should')

                        # replace pool object with new object
                        seen.append(entity.data.label)
                        entity.data = newdata

                    # save object with its score in object file
                    scores_pack = struct.pack('d'*len(entity.scores), *entity.scores)
                    disk.write(
                        int_to_bytes(len(scores_pack)) +
                        scores_pack +
                        entity.data.to_byte()
                    )

        # # # # # #    TASK.2   # # # # # #
        #     saving pool document        #
        # # # # # # # # # # # # # # # # # #

        pool_collection = mongo_client[DATABASE_NAME][POOLS_COLLECTION]
        error = safe_operation(pool_collection, UPDATE, order_filter={POOL_NAME:self.collection_name}, order={'$set':self.to_document()})
        if error:
            with open(IMPORTANT_LOG, 'a') as log:log.write(f'[POOL][INSERT] error: {error}\n')

        if should_close:mongo_client.close()


    def readfile(self):

        with open(self.collection_name+POOL_TAG, 'rb') as disk:
            for table_index in range(len(self.tables)):
                table_len = bytes_to_int(disk.read(INT_SIZE))

                for _ in range(table_len):
                    pack_len = bytes_to_int(disk.read(INT_SIZE))
                    scores = list(struct.unpack('d'*len(self.descriptions), disk.read(pack_len)))
                    pattern = ChainNode.byte_to_object(disk, collection=self.collection_name)
                    self.tables[table_index].append(AKAGIPool.Entity(pattern, scores))


    def read_document(self, mongo_client=None):

        if not mongo_client:mongo_client = get_client()
        pools_collection = mongo_client[DATABASE_NAME][POOLS_COLLECTION]

        item_or_error = safe_operation(pools_collection, FIND_ONE, {POOL_NAME:self.collection_name})

        if not item_or_error:
            with open(IMPORTANT_LOG, 'a') as log:log.write(f'[POOL] pool object not found | name: {self.collection_name}\n')
        elif not isinstance(item_or_error, dict):
            with open(IMPORTANT_LOG, 'a') as log:log.write(f'[POOL][ERROR] error: {item_or_error}\n')

        self.tables = []
        documented = item_or_error[TABLES]
        for table in documented:
            new_table = [self.Entity(document=document, collection_name=self.collection_name) for document in table]
            self.tables.append(new_table[:])


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


def objective_function_pvalue(pattern: ChainNode, sequences_bundles, mongo_client):

    # error handeling
    try:foundlist_seq_vector = pattern.foundmap.get_list(client=mongo_client)[0]
    except Exception as e:return e

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


def distance_to_summit_score(pattern: ChainNode, sequences_bundles, mongo_client):

    # error handeling
    try:pattern_foundlist = pattern.foundmap.get_list(client=mongo_client)
    except Exception as e:return e

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
    

def pwm_score(pattern: ChainNode, arg_bundle, mongo_client):

    # unpacking arguments
    sequences = arg_bundle[0]
    pwm = arg_bundle[1][0]
    r_pwm = arg_bundle[1][1]
    
    aggregated = 0
    count = 0

    # error handeling
    try:bundle = pattern.foundmap.get_list(client=mongo_client)
    except Exception as e:return e
    
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
    pooly.collection_name = 'pooly'

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

    pooly.save()

    disk = AKAGIPool(get_AKAGI_pools_configuration({SEQUENCES:'', SEQUENCE_BUNDLES:'', PWM:''}), collection_name='pooly')
    disk.readfile()
    mon = AKAGIPool(get_AKAGI_pools_configuration({SEQUENCES:'', SEQUENCE_BUNDLES:'', PWM:''}), collection_name='pooly')
    mon.read_document()
    # pooly_disk.readfile()