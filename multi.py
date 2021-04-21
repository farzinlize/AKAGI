from queue import Empty
import socket
from time import sleep
from datetime import datetime
from constants import ACCEPT_REQUEST, AGENTS_MAXIMUM_COUNT, AGENTS_PORT_START, AKAGI_PREDICTION_EXPERIMENTAL, AKAGI_PREDICTION_STATISTICAL, ARGUMENT_KEY, CHAINING_PERMITTED_SIZE, CR_FILE, CR_TABLE_HEADER_JASPAR, CR_TABLE_HEADER_SSMART, CR_TABLE_HEADER_SUMMIT, EXTRACT_OBJ, FOUNDMAP_MEMO, FUNCTION_KEY, GOOD_HIT, HOST_ADDRESS, LIVE_REPORT, NEAR_EMPTY, NEAR_FULL, ON_SEQUENCE_ANALYSIS, PARENT_WORK, POOL_HIT_SCORE, PWM, REJECT_REQUEST, REQUEST_PORT, SEQUENCES, SEQUENCE_BUNDLES, SIGN_KEY, TABLE_HEADER_KEY, TRY_COUNT, TRY_DELAY
from pool import AKAGIPool, RankingPool, distance_to_summit_score, get_AKAGI_pools_configuration, objective_function_pvalue, pwm_score
from misc import ExtraPosition, QueueDisk, bytes_to_int, clear_screen, int_to_bytes, pfm_to_pwm
from TrieFind import ChainNode, WatchNode, WatchNodeC
from multiprocessing import Lock, Process, Queue, Array
from onSequence import OnSequenceDistribution
from findmotif import next_chain
import os
from typing import List


def chaining_thread_and_local_pool(work: Queue, merge: Queue, on_sequence: OnSequenceDistribution, dataset_dict, overlap, gap, q):

    # local ranking pools
    local_pool = AKAGIPool(get_AKAGI_pools_configuration(dataset_dict))

    while True:

        # obtaining a job
        motif: ChainNode = work.get()

        # evaluation the job (motif)
        good_enough = 0
        go_merge = False
        for rank, multiplier in zip(local_pool.judge(motif), [1, 1, 2]):
            good_enough += int(rank <= GOOD_HIT)*multiplier

            # merge request policy
            if rank == 0:go_merge = True
        if go_merge:merge.put(local_pool)

        if len(motif.label) <= CHAINING_PERMITTED_SIZE:
            good_enough += POOL_HIT_SCORE + 1

        # ignouring low rank motifs
        if good_enough <= POOL_HIT_SCORE:continue

        # chaining and insert next generation jobs
        for next_motif in next_chain(motif, on_sequence, overlap, gap, q):
            work.put(ChainNode(
                motif.label + next_motif.label, 
                next_motif.foundmap.turn_to_filemap()))
            del next_motif
        

def global_pool_thread(merge: Queue, dataset_dict):
    
    report_count = 0

    global_pool = AKAGIPool(get_AKAGI_pools_configuration(dataset_dict))

    while True:

        # merging
        merge_request: AKAGIPool = merge.get()
        global_pool.merge(merge_request)

        # reporting
        with open(CR_FILE, 'w') as window:

            # time stamp
            window.write(str(datetime.now()) + ' | report #%d\n\n'%report_count)
            report_count += 1

            # table reports
            window.write(global_pool.top_ten_reports())

            # best entity instances report
            # for table in global_pool.tables:
            #     if table:window.write('>\n' + table[0].data.instances_str(dataset_dict[SEQUENCES]))




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

    local_pool = AKAGIPool(get_AKAGI_pools_configuration(dataset_dict))

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
        go_merge = False
        for rank, multiplier in zip(local_pool.judge(motif), [1, 1, 2]):
            good_enough += int(rank <= GOOD_HIT)*multiplier

            # merge request policy
            if rank == 0:go_merge = True
        if go_merge:merge.put(local_pool)

        if len(motif.label) <= CHAINING_PERMITTED_SIZE:
            good_enough += POOL_HIT_SCORE + 1

        # ignouring low rank motifs
        if good_enough <= POOL_HIT_SCORE:continue

        # chaining and insert next generation jobs
        for next_motif in next_chain(motif, on_sequence, overlap, gap, q):
            work.put(ChainNode(
                motif.label + next_motif.label, 
                next_motif.foundmap.turn_to_filemap()))
            del next_motif


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
