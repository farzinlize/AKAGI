import socket
from time import sleep
from constants import ACCEPT_REQUEST, AGENTS_MAXIMUM_COUNT, AGENTS_PORT_START, AKAGI_PREDICTION_EXPERIMENTAL, AKAGI_PREDICTION_STATISTICAL, CR_FILE, CR_TABLE_HEADER_SSMART, CR_TABLE_HEADER_SUMMIT, EXTRACT_OBJ, FOUNDMAP_MEMO, HOST_ADDRESS, LIVE_REPORT, REJECT_REQUEST, REQUEST_PORT, TRY_COUNT, TRY_DELAY
from pool import RankingPool, distance_to_summit_score, objective_function_pvalue
from misc import ExtraPosition, QueueDisk, bytes_to_int, clear_screen, int_to_bytes
from TrieFind import ChainNode, WatchNode, WatchNodeC
from multiprocessing import Lock, Process, Queue, Array
from onSequence import OnSequenceDistribution
import os
from typing import List



def chaining_thread(id, work: Queue, activity_array, done: Queue, on_sequence: OnSequenceDistribution, overlap, gap, q):
    
    while True:

        # obtaining a job
        motif: ChainNode = work.get()
        activity_array[id] = 1

        # chaining
        bundle = motif.foundmap.get_list()
        next_tree = WatchNodeC(custom_foundmap_type=FOUNDMAP_MEMO)
        for index, seq_id in enumerate(bundle[0]):
            position: ExtraPosition
            for position in bundle[1][index]:
                for sliding in [i for i in range(-overlap, gap+1)]:
                    next_position = position.end_position() + sliding
                    if next_position >= len(on_sequence.struct[seq_id]):continue
                    for next_condidate in on_sequence.struct[seq_id][next_position]:
                        next_tree.add_frame(
                            next_condidate, 
                            seq_id, 
                            ExtraPosition(position.start_position, len(next_condidate) + sliding))
        
        next_motif: WatchNodeC
        for next_motif in next_tree.extract_motifs(q, EXTRACT_OBJ):
            done.put(ChainNode(
                motif.label + next_motif.label, 
                next_motif.foundmap.turn_to_filemap()))

        activity_array[id] = 0
        


def ranking_thread(ready_to_judge: Queue, pools:List[RankingPool], work: Queue, queue_lock, judge_activity):

    while True:
        motif: ChainNode = ready_to_judge.get()

        good_hit = False
        for pool in pools:good_hit |= pool.add(motif)
        # big_queue.insert(motif, lock=queue_lock)

        if good_hit:
            work.put(motif)

        # updating score board
        if LIVE_REPORT:
            clear_screen()
            print(CR_TABLE_HEADER_SSMART + pools[0].top_ten_table())
            print(CR_TABLE_HEADER_SUMMIT + pools[1].top_ten_table())
            print('work queue -> %d\t|\tnext queue -> %d'%(work.qsize(), ready_to_judge.qsize()))
        else:
            with open(CR_FILE, 'w') as window:
                window.write(CR_TABLE_HEADER_SSMART + pools[0].top_ten_table() + '\n')
                window.write(CR_TABLE_HEADER_SUMMIT + pools[1].top_ten_table() + '\n')
                window.write('work queue -> %d\t|\tnext queue -> %d\n'%(work.qsize(), ready_to_judge.qsize()))


def agent_thread(port_id, work:Queue, merge_request:Queue):
    pass


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



def multicore_chaining_main(cores, zero_motifs: List[WatchNode], sequences, bundles, overlap, gap, q, network=False):

    # initial necessary data
    on_sequence = OnSequenceDistribution(zero_motifs, sequences)
    pool_ssmart = RankingPool(bundles, objective_function_pvalue, sign=-1)
    pool_summit = RankingPool(bundles, distance_to_summit_score)

    # initializing work-queue
    work = Queue()
    for motif in zero_motifs:
        turn_to_chain = ChainNode(motif.label, motif.foundmap)
        work.put_nowait(turn_to_chain)
        pool_ssmart.add(turn_to_chain)
        pool_summit.add(turn_to_chain)

    # each thread result will be putted here (producer/consumer)
    next_generation = Queue()

    # initial disk queue for saving big data
    disk_queue = QueueDisk(ChainNode)
    disk_queue_lock = Lock()

    # initial merge request queue
    merge_queue = Queue()

    # initial threads
    activity_array = Array('B', [1 for _ in range(cores)])
    judge_activity = Array('B', [1])
    workers = [Process(target=chaining_thread, args=(i, work, activity_array, next_generation, on_sequence, overlap, gap, q)) for i in range(cores)]
    the_judge = Process(target=ranking_thread, args=(next_generation,[pool_ssmart, pool_summit], work, disk_queue_lock, judge_activity))
    for worker in workers:worker.start()
    the_judge.start()

    # initial server listener (in case of network computing)
    if network:
        server = Process(target=server_thread, args=(on_sequence,))
        server.start()

    try_more = TRY_COUNT

    # working loop
    while True:
        if try_more:
            try:
                pass
            #     work.put(disk_queue.pop(lock=disk_queue_lock))
            #     try_more = TRY_COUNT
            # except QueueDisk.QueueEmpty:
            #     print('QUEUE_EMPTY SIGNAL')
            #     if sum(activity_array) == 0 and not next_generation.empty():
            #         try_more -= 1
            #     sleep(TRY_DELAY)
            except KeyboardInterrupt:
                break
        else:break
        
    # killing processes/threads
    for worker in workers:worker.terminate()
    the_judge.terminate()
    # judge_activity[0] = 1
    # the_judge.join()

    # pool_ssmart.all_ranks_report(AKAGI_PREDICTION_STATISTICAL, sequences)
    # pool_summit.all_ranks_report(AKAGI_PREDICTION_EXPERIMENTAL, sequences)        

