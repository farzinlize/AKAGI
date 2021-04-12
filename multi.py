from queue import Empty
import socket
from time import sleep
from datetime import datetime
from constants import ACCEPT_REQUEST, AGENTS_MAXIMUM_COUNT, AGENTS_PORT_START, AKAGI_PREDICTION_EXPERIMENTAL, AKAGI_PREDICTION_STATISTICAL, CHAINING_PERMITTED_SIZE, CR_FILE, CR_TABLE_HEADER_JASPAR, CR_TABLE_HEADER_SSMART, CR_TABLE_HEADER_SUMMIT, EXTRACT_OBJ, FOUNDMAP_MEMO, GOOD_HIT, HOST_ADDRESS, LIVE_REPORT, NEAR_EMPTY, NEAR_FULL, ON_SEQUENCE_ANALYSIS, PARENT_WORK, POOL_HIT_SCORE, PWM, REJECT_REQUEST, REQUEST_PORT, SEQUENCES, SEQUENCE_BUNDLES, TRY_COUNT, TRY_DELAY
from pool import RankingPool, distance_to_summit_score, objective_function_pvalue, pwm_score
from misc import ExtraPosition, QueueDisk, bytes_to_int, clear_screen, int_to_bytes, pfm_to_pwm
from TrieFind import ChainNode, WatchNode, WatchNodeC
from multiprocessing import Lock, Process, Queue, Array
from onSequence import OnSequenceDistribution
from findmotif import next_chain
import os
from typing import List


def chaining_thread_and_local_pool(work: Queue, merge: Queue, on_sequence: OnSequenceDistribution, dataset_dict, overlap, gap, q):
    
    # unpacking dataset dictionary
    sequences = dataset_dict[SEQUENCES]
    bundles = dataset_dict[SEQUENCE_BUNDLES]
    pwm = dataset_dict[PWM]

    # local ranking pools
    pool_ssmart = RankingPool(bundles, objective_function_pvalue, sign=-1)
    pool_summit = RankingPool(bundles, distance_to_summit_score)
    pool_jaspar = RankingPool((sequences,pwm), pwm_score, sign=-1)

    while True:

        # obtaining a job
        motif: ChainNode = work.get()

        # evaluation the job (motif)
        good_enough = 0
        for pool, multiplier in [(pool_ssmart, 1), (pool_summit, 1), (pool_jaspar, 2)]:
            rank = pool.add(motif)
            good_enough += int(rank <= GOOD_HIT)*multiplier

            # merge request policy
            if rank == 0:merge.put(pool)

        if len(motif.label) <= CHAINING_PERMITTED_SIZE:
            good_enough += POOL_HIT_SCORE + 1

        # ignouring low rank motifs
        if good_enough <= POOL_HIT_SCORE:continue

        # chaining and insert next generation jobs
        for next_motif in next_chain(motif, on_sequence, overlap, gap, q):
            work.put(ChainNode(
                motif.label + next_motif.label, 
                next_motif.foundmap.turn_to_filemap()))
        

def global_pool_thread(merge: Queue, dataset_dict):
    
    report_count = 0

    # unpacking dataset dictionary
    sequences = dataset_dict[SEQUENCES]
    bundles = dataset_dict[SEQUENCE_BUNDLES]
    pwm = dataset_dict[PWM]

    # global ranking pools
    pool_summit = RankingPool(bundles, distance_to_summit_score)
    pool_ssmart = RankingPool(bundles, objective_function_pvalue, sign=-1)
    pool_jaspar = RankingPool((sequences,pwm), pwm_score, sign=-1)

    while True:

        merge_request: RankingPool = merge.get()
        if merge_request.scoreing == pool_summit.scoreing:pool_summit.merge(merge_request)
        elif merge_request.scoreing == pool_ssmart.scoreing:pool_ssmart.merge(merge_request)
        elif merge_request.scoreing == pool_jaspar.scoreing:pool_jaspar.merge(merge_request)

        with open(CR_FILE, 'w') as window:

            # time stamp
            window.write(str(datetime.now()) + ' | report #%d\n\n'%report_count)
            report_count += 1

            window.write(CR_TABLE_HEADER_SSMART + pool_ssmart.top_ten_table() + '\n')
            window.write(CR_TABLE_HEADER_SUMMIT + pool_summit.top_ten_table() + '\n')
            window.write(CR_TABLE_HEADER_JASPAR + pool_jaspar.top_ten_table() + '\n\n\n')

            if pool_ssmart.pool:window.write('> SSMART\n' + pool_ssmart.pool[0].data.instances_str(sequences))
            if pool_summit.pool:window.write('> SUMMIT\n' + pool_summit.pool[0].data.instances_str(sequences))
            if pool_jaspar.pool:window.write('> JASPAR\n' + pool_jaspar.pool[0].data.instances_str(sequences))



def agent_thread(port_id, work:Queue, merge_request:Queue):
    raise NotImplementedError


# not completed nor tested
def server_thread(on_sequence:OnSequenceDistribution):
    
    agents:List[Process] = []

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        # setup
        s.bind((HOST_ADDRESS, REQUEST_PORT))
        s.listen()

        while True:

            # making connection
            conn, _ = s.accept()

            n_agent = bytes_to_int(conn.recv())
            if n_agent > AGENTS_MAXIMUM_COUNT - len(agents):
                conn.sendall(REJECT_REQUEST)
                conn.close()
                continue
            
            conn.sendall(ACCEPT_REQUEST)

            # sending observation data (onSequence Distribution)
            conn.sendall(on_sequence.to_byte())

            previous_agents = len(agents)
            for port in [AGENTS_PORT_START+previous_agents+i for i in range(n_agent)]:
                conn.sendall(int_to_bytes(port))
                agents += [Process(target=agent_thread, args=(port,))]
                agents[-1].start()


# a copy of 'chaining_thread_and_local_pool' function but with keeping eye on work queue for finish
def parent_chaining(work: Queue, merge: Queue, on_sequence: OnSequenceDistribution, dataset_dict, overlap, gap, q):

    # unpacking dataset dictionary
    sequences = dataset_dict[SEQUENCES]
    bundles = dataset_dict[SEQUENCE_BUNDLES]
    pwm = dataset_dict[PWM]

    # local ranking pools
    pool_ssmart = RankingPool(bundles, objective_function_pvalue, sign=-1)
    pool_summit = RankingPool(bundles, distance_to_summit_score)
    pool_jaspar = RankingPool((sequences,pwm), pwm_score, sign=-1)

    counter = 0

    while counter < 10:

        # reports before work
        with open('parent.report', 'w') as report:
            report.write("work queue size => %d\nmerge queue size => %d"%(work.qsize(), merge.qsize()))

        # obtaining a job if available
        try:
            motif: ChainNode = work.get(timeout=5)
            counter = 0
        
        # no job is found - try again another time till the counter reaches its limit
        except Empty:
            counter += 1
            continue

        # evaluation the job (motif)
        good_enough = 0
        for pool, multiplier in [(pool_ssmart, 1), (pool_summit, 1), (pool_jaspar, 2)]:
            rank = pool.add(motif)
            good_enough += int(rank <= GOOD_HIT)*multiplier

            # merge request policy
            if rank == 0:merge.put(pool)

        if len(motif.label) <= CHAINING_PERMITTED_SIZE:
            good_enough += POOL_HIT_SCORE + 1

        # ignouring low rank motifs
        if good_enough <= POOL_HIT_SCORE:continue

        # chaining and insert next generation jobs
        for next_motif in next_chain(motif, on_sequence, overlap, gap, q):
            work.put(ChainNode(
                motif.label + next_motif.label, 
                next_motif.foundmap.turn_to_filemap()))


def multicore_chaining_main(cores, zero_motifs: List[WatchNode], dataset_dict, overlap, gap, q, network=False):

    # unpacking necessary parts of dataset dictionary
    sequences = dataset_dict[SEQUENCES]

    # generate on sequence distribution 
    on_sequence = OnSequenceDistribution(zero_motifs, sequences)

    # reports for analysis
    if ON_SEQUENCE_ANALYSIS:print(on_sequence.analysis())
    
    # initializing synchronized queues
    work = Queue()
    merge = Queue()
    for motif in zero_motifs:
        work.put_nowait(ChainNode(motif.label, motif.foundmap))

    # initial disk queue for memory balancing
    disk_queue = QueueDisk(ChainNode)

    # initial threads
    workers = [Process(target=chaining_thread_and_local_pool, args=(work, merge, on_sequence, dataset_dict, overlap, gap, q)) for _ in range(cores)]
    global_pooler = Process(target=global_pool_thread, args=(merge,dataset_dict))
    for worker in workers:worker.start()
    global_pooler.start()

    # initial server listener (in case of network computing)
    if network:
        server = Process(target=server_thread, args=(on_sequence,))
        server.start()

    counter = 0

    # parent also is a worker
    # [WARNING] may results in memory full
    if PARENT_WORK:
        parent_chaining(work, merge, on_sequence, dataset_dict, overlap, gap, q)

    # parent is in charge of memory balancing 
    else:
        while counter <= 100:
            memory_balance = work.qsize()
            if memory_balance > NEAR_FULL:
                item: ChainNode = work.get()
                disk_queue.insert(item)
            elif memory_balance < NEAR_EMPTY:
                try:
                    item: ChainNode = disk_queue.pop()
                    work.put(item)
                except QueueDisk.QueueEmpty:
                    if memory_balance == 0:counter += 1
                    else:counter = 0
                    sleep(5)

        
    # killing processes/threads
    for worker in workers:worker.terminate()
    global_pooler.terminate()

    assert work.qsize() == 0 
