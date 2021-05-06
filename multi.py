import os
from report_email import send_files_mail
from pause import save_the_rest, time_has_ended
from queue import Empty
from time import sleep
from datetime import datetime
from constants import ACCEPT_REQUEST, AGENTS_MAXIMUM_COUNT, AGENTS_PORT_START, CHAINING_PERMITTED_SIZE, CR_FILE, DATASET_NAME, GOOD_HIT, HELP_PORTION, HOST_ADDRESS, NEAR_EMPTY, NEAR_FULL, NEED_HELP, PARENT_WORK, POOL_HIT_SCORE, PROCESS_ENDING_REPORT, PROCESS_REPORT_FILE, REJECT_REQUEST, REQUEST_PORT, SAVE_THE_REST_CLOUD, TIMER_CHAINING_HOURS, TIMER_HELP_HOURS
from pool import AKAGIPool, get_AKAGI_pools_configuration
from misc import QueueDisk, bytes_to_int, int_to_bytes
from TrieFind import ChainNode
from multiprocessing import Process, Queue
from onSequence import OnSequenceDistribution
from findmotif import next_chain
from typing import List

ERROR_EXIT = -2
TIMESUP_EXIT = -1
END_EXIT = 0


def chaining_thread_and_local_pool(message:Queue, work: Queue, merge: Queue, on_sequence: OnSequenceDistribution, dataset_dict, overlap, gap, q):

    # local ranking pools
    local_pool = AKAGIPool(get_AKAGI_pools_configuration(dataset_dict))
    jobs_done_by_me = 0
    chaining_done_by_me = 0

    while True:

        # obtaining a job
        motif: ChainNode = work.get()
        jobs_done_by_me += 1

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

        # open process report file
        report = open(PROCESS_REPORT_FILE%(os.getpid()), 'a+')

        # chaining
        next_motifs, used_nodes = next_chain(motif, on_sequence, overlap, gap, q, report=report, chain_id=chaining_done_by_me)

        # report and close
        report.write('USED NODES COUNT %d\n'%used_nodes)
        report.close()

        # insert next generation jobs
        for next_motif in next_motifs:
            work.put(ChainNode(
                motif.label + next_motif.label, 
                next_motif.foundmap.turn_to_filemap()))
            del next_motif
        
        chaining_done_by_me += 1

        try:
            command = message.get_nowait()
            if command == 'MK':
                merge.put(local_pool)
                with open(PROCESS_REPORT_FILE%(os.getpid()), 'a+') as last_report:
                    last_report.write(PROCESS_ENDING_REPORT%(jobs_done_by_me, chaining_done_by_me))
                return # exit
        except Empty:pass
        

def global_pool_thread(merge: Queue, dataset_dict, initial_pool:AKAGIPool):
    
    report_count = 0

    if initial_pool == None:
        global_pool = AKAGIPool(get_AKAGI_pools_configuration(dataset_dict))
    else:
        global_pool = initial_pool

    while True:

        # merging
        merge_request: AKAGIPool = merge.get()
        if type(merge_request)==str and merge_request=='PK':
            global_pool.savefile('akagi.pool')
            return

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


# a copy of 'chaining_thread_and_local_pool' function but with keeping eye on work queue for finish
def parent_chaining(work: Queue, merge: Queue, on_sequence: OnSequenceDistribution, dataset_dict, overlap, gap, q):

    # timer first stamp
    since = datetime.now()
    # since_last_help = datetime.now()

    local_pool = AKAGIPool(get_AKAGI_pools_configuration(dataset_dict))

    counter = 0
    chaining_done_by_me = 0
    jobs_done_by_me = 0

    while counter < 10:

        # reports before work
        with open('parent.report', 'w') as report:
            report.write("work queue size => %d\nmerge queue size => %d"%(work.qsize(), merge.qsize()))

        # obtaining a job if available
        try:
            motif: ChainNode = work.get(timeout=5)
            jobs_done_by_me += 1
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

        # open process report file
        report = open(PROCESS_REPORT_FILE%(os.getpid()), 'a+')

        # chaining
        next_motifs, used_nodes = next_chain(motif, on_sequence, overlap, gap, q, report=report, chain_id=chaining_done_by_me)

        # report and close
        report.write('USED NODES COUNT %d\n'%used_nodes)
        report.close()

        # insert next generation jobs
        for next_motif in next_motifs:
            work.put(ChainNode(
                motif.label + next_motif.label, 
                next_motif.foundmap.turn_to_filemap()))
            del next_motif
        
        chaining_done_by_me += 1

        # timout check
        if time_has_ended(since, TIMER_CHAINING_HOURS):
            merge.put(local_pool)
            with open(PROCESS_REPORT_FILE%(os.getpid()), 'a+') as last_report:
                last_report.write(PROCESS_ENDING_REPORT%(jobs_done_by_me, chaining_done_by_me))
            return TIMESUP_EXIT

        # need for help check
        estimated_size = work.qsize()
        if estimated_size > NEED_HELP:

            help_me_with = []
            for _ in range(int(estimated_size*HELP_PORTION)):
                help_me_with.append(work.get())

            try:
                # uploading to drive
                save_the_rest(help_me_with, on_sequence, q, dataset_dict[DATASET_NAME], cloud=True)

                # inform by email
                send_files_mail(
                    strings=['HELP HAS SENT - EXECUTION OF ANOTHER AKAGI INSTANCE IS REQUESTED'],
                    additional_subject=' HELP AKAGI')
            except:
                print('[ERROR] something went wrong when sending help')
                return ERROR_EXIT
    
    return END_EXIT


def multicore_chaining_main(cores, initial_works: List[ChainNode], on_sequence:OnSequenceDistribution, dataset_dict, overlap, gap, q, network=False, initial_pool=None):
    
    # initializing synchronized queues
    work =    Queue()   # chaining jobs with type of chain nodes
    merge =   Queue()   # merging requests to a global pool
    message = Queue()   # message box to terminate workers loop

    for motif in initial_works:
        work.put_nowait(motif)

    # initial disk queue for memory balancing
    disk_queue = QueueDisk(ChainNode)

    # initial threads
    workers = [Process(target=chaining_thread_and_local_pool, args=(message,work,merge,on_sequence,dataset_dict,overlap,gap,q)) for _ in range(cores)]
    global_pooler = Process(target=global_pool_thread, args=(merge,dataset_dict,initial_pool))
    for worker in workers:worker.start()
    global_pooler.start()

    # initial server listener (in case of network computing)
    if network:raise NotImplementedError

    # parent also is a worker
    # [WARNING] may results in memory full
    if PARENT_WORK:
        exit = parent_chaining(work, merge, on_sequence, dataset_dict, overlap, gap, q)

    # parent is in charge of memory balancing 
    else:
        exit = END_EXIT
        since = datetime.now()
        # call_for_help = datetime.now()
        counter = 0

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
            else:
                sleep(10)

            # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
            # TODO: send for help policy when parent is in charge of memory balancing
            # challenge: jobs are both in disk and memory -> send disk jobs for help
            #
            # if time_has_ended(call_for_help, TIMER_HELP_HOURS) and memory_balance:
            #     help_jobs = []
            #     for _ in range(memory_balance*HELP_PORTION):
            #         try:help_jobs.append(work.get(timeout=5))

            if time_has_ended(since, TIMER_CHAINING_HOURS):exit = TIMESUP_EXIT;break

    # message the workers to terminate their job and merge for last time
    for _ in workers:
        message.put_nowait('MK')

    # waiting for workers to die
    for worker in workers:
        worker.join()

    # message global_pooler to terminate
    merge.put('PK')
    global_pooler.join()

    # send rest of the jobs to cloud in case of timeout
    if exit == TIMESUP_EXIT:

        rest_work = []
        while True:
            try:rest_work.append(work.get_nowait())
            except Empty:break
        
        save_the_rest(rest_work, on_sequence, q, dataset_dict[DATASET_NAME], cloud=SAVE_THE_REST_CLOUD)
        send_files_mail(
            strings=['REST OF JOBS HAS SENT - unfinished program has sent its remaining data into cloud'],
            additional_subject=' an unfinished end')

    elif exit == ERROR_EXIT:return

    assert work.qsize() == 0 
