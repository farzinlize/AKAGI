# python libraries 
import os
from functools import reduce
from queue import Empty
from time import sleep
from datetime import datetime
from multiprocessing import Process, Queue
from typing import List

# project modules
from mongo import get_client
from FoundMap import initial_readonlymaps
from checkpoint import lock_checkpoint, query_resumable_checkpoints, remove_checkpoint
from networking import AssistanceService
from report_email import send_files_mail
from pause import save_the_rest, time_has_ended
from pool import AKAGIPool, get_AKAGI_pools_configuration
from misc import QueueDisk
from TrieFind import ChainNode
from onSequence import OnSequenceDistribution
from findmotif import next_chain

# settings and global variables
from constants import CHAINING_EXECUTION_STATUS, CHAINING_PERMITTED_SIZE, CHECK_TIME_INTERVAL, CR_FILE, DATASET_NAME, DEFAULT_COLLECTION, EXECUTION, GOOD_HIT, HELP_CLOUD, HELP_PORTION, HOPEFUL, IMPORTANT_LOG, MAIL_SERVICE, MAXIMUM_MEMORY_BALANCE, MAX_CORE, MEMORY_BALANCING_REPORT, MINIMUM_CHUNK_SIZE, NEAR_EMPTY, NEAR_FULL, NEED_HELP, PARENT_WORK, POOL_HIT_SCORE, POOL_TAG, PROCESS_ENDING_REPORT, PROCESS_REPORT_FILE, TIMER_CHAINING_HOURS, EXIT_SIGNAL

MANUAL_EXIT = -3
ERROR_EXIT = -2
TIMESUP_EXIT = -1
END_EXIT = 0


def chaining_thread_and_local_pool(message: Queue, work: Queue, merge: Queue, on_sequence: OnSequenceDistribution, dataset_dict, overlap, gap, q):

    def error_exit(error):
        merge.put(local_pool)
        report.write('EXIT ON FAILURE\n' + PROCESS_ENDING_REPORT%(jobs_done_by_me, chaining_done_by_me))
        report.close()
        raise error

    # local ranking pools
    local_pool = AKAGIPool(get_AKAGI_pools_configuration(dataset_dict))
    jobs_done_by_me = 0
    chaining_done_by_me = 0
    client = get_client(connect=True)

    # open process report file
    report = open(PROCESS_REPORT_FILE%(os.getpid()), 'w')

    while True:

        # check for exit signal (higher priority queue check)
        try         :signal = message.get_nowait()
        except Empty:signal = None

        if signal:

            # Merge and Finish
            if signal == EXIT_SIGNAL:
                merge.put(local_pool)
                report.write(PROCESS_ENDING_REPORT%(jobs_done_by_me, chaining_done_by_me))
                report.close()
                return # exit

        # obtaining a job
        motif: ChainNode = work.get()
        jobs_done_by_me += 1

        # evaluation the job (motif)
        good_enough = 0
        go_merge = False
        judge_decision = local_pool.judge(motif)

        # check for error
        if not isinstance(judge_decision, list):error_exit(judge_decision)
        
        for rank, multiplier in zip(judge_decision, [1, 1, 2]):
            good_enough += int(rank <= GOOD_HIT)*multiplier

            # merge request policy
            if rank == 0:go_merge = True
        if go_merge:merge.put(local_pool)

        if len(motif.label) <= CHAINING_PERMITTED_SIZE:
            good_enough += POOL_HIT_SCORE + 1

        # ignouring low rank motifs
        if good_enough <= POOL_HIT_SCORE:continue

        # chaining
        last_time = datetime.now()
        next_motifs, used_nodes_or_error = next_chain(motif, on_sequence, overlap, gap, q, report=report, chain_id=chaining_done_by_me, client=client)
        report.write(f'CHAINING({datetime.now() - last_time}) | ')

        # check for database error
        if not next_motifs:error_exit(used_nodes_or_error)

        # report and close
        report.write('USED NODES COUNT %d | '%used_nodes_or_error)

        # mongoDB insertion and checking for error
        last_time = datetime.now()
        inserted_maps = initial_readonlymaps([motif.foundmap for motif in next_motifs], DEFAULT_COLLECTION, client=client)
        if not isinstance(inserted_maps, list):error_exit(inserted_maps)

        report.write(f'MONGO({datetime.now() - last_time}) | ')

        # insert next generation jobs
        for next_motif, foundmap in zip(next_motifs, inserted_maps):
            work.put(ChainNode(motif.label + next_motif.label, foundmap))
            del next_motif

        chaining_done_by_me += 1
        report.flush()
        

def global_pool_thread(merge: Queue, dataset_dict, initial_pool:AKAGIPool):
    
    report_count = 0

    if initial_pool :global_pool = initial_pool
    else            :global_pool = AKAGIPool(get_AKAGI_pools_configuration(dataset_dict))

    while True:

        # merging
        merge_request: AKAGIPool = merge.get()
        if type(merge_request)==str and merge_request==EXIT_SIGNAL:
            global_pool.savefile(EXECUTION+POOL_TAG)
            return # exit

        global_pool.merge(merge_request)

        # reporting
        with open(CR_FILE, 'w') as window:

            # time stamp
            window.write(str(datetime.now()) + ' | report #%d\n\n'%report_count)
            report_count += 1

            # table reports
            window.write(global_pool.top_ten_reports())


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
                next_motif.foundmap.readonly()))
            del next_motif
        
        chaining_done_by_me += 1

        # timout check
        if time_has_ended(since, TIMER_CHAINING_HOURS):
            merge.put(local_pool)
            with open(PROCESS_REPORT_FILE%(os.getpid()), 'a+') as last_report:
                last_report.write(PROCESS_ENDING_REPORT%(jobs_done_by_me, chaining_done_by_me))
            return TIMESUP_EXIT

        # need for help check
        if HOPEFUL:
            estimated_size = work.qsize()
            if estimated_size > NEED_HELP:

                help_me_with = []
                for _ in range(int(estimated_size*HELP_PORTION)):
                    help_me_with.append(work.get())

                # saving rest of the work as checkpoint
                save_the_rest(help_me_with, on_sequence, q, dataset_dict[DATASET_NAME], cloud=HELP_CLOUD)

                # inform by email
                if MAIL_SERVICE:
                    send_files_mail(
                        strings=['HELP HAS SENT - EXECUTION OF ANOTHER AKAGI INSTANCE IS REQUESTED'],
                        additional_subject=' HELP AKAGI')
    
    return END_EXIT


def network_handler(merge: Queue):

    # initial socket handeling (server socket)
    service = AssistanceService()

    while True:

        assistance = service.listen_for_assistance()

        # send resumable checkpoints to new assistants
        if assistance.isNew():
            checkpoints = query_resumable_checkpoints()

            if checkpoints:
                checkpoint = checkpoints[0] # send first one
                assistance.copy_checkpoint(checkpoint)
                lock_checkpoint(checkpoint)
            else:
                assistance.REFUSE('no need for help')
                continue

        # get reports from elder assistants
        else:
            working_checkpoint, report, finish_code = assistance.get_report()
            merge.put(report)

            if finish_code == TIMESUP_EXIT:
                assistance.get_checkpoint()

            remove_checkpoint(working_checkpoint, locked=True)

        
def multicore_chaining_main(cores_order, initial_works: List[ChainNode], on_sequence:OnSequenceDistribution, dataset_dict, overlap, gap, q, network=False, initial_pool=None):
    
    try   :available_cores = len(os.sched_getaffinity(0))
    except:available_cores = 'unknown'

    print(f'[CHAINING][MULTICORE] number of available cores: {available_cores}')

    # making status file
    with open(CHAINING_EXECUTION_STATUS, 'w') as status:status.write('running')

    # auto maximize core usage (1 worker per core)
    if cores_order == MAX_CORE:
        if available_cores == 'unknown':
            print('[FATAL][ERROR] number of available cores are unknown')
            return None, ERROR_EXIT
        cores = available_cores - int(PARENT_WORK)

    # order custom number of workers
    else:cores = cores_order

    # initializing synchronized queues
    work =    Queue()   # chaining jobs with type of chain nodes
    merge =   Queue()   # merging requests to a global pool
    message = Queue()   # message box to terminate workers loop (higher priority)

    for motif in initial_works:
        work.put_nowait(motif)

    # initial disk queue for memory balancing
    disk_queue = QueueDisk(ChainNode)

    # initial threads
    workers = [Process(target=chaining_thread_and_local_pool, args=(message, work,merge,on_sequence,dataset_dict,overlap,gap,q)) for _ in range(cores)]
    global_pooler = Process(target=global_pool_thread, args=(merge,dataset_dict,initial_pool))
    for worker in workers:worker.start()
    global_pooler.start()

    # initial server listener (in case of network computing)
    if network:
        nh = Process(target=network_handler, args=(merge,))
        nh.start()
        # raise NotImplementedError

    # parent also is a worker
    # [WARNING] may results in memory overflow
    if PARENT_WORK:
        exit_code = parent_chaining(work, merge, on_sequence, dataset_dict, overlap, gap, q)

    # parent is in charge of memory balancing 
    else:
        exit_code = END_EXIT
        since = datetime.now()
        m = (MAXIMUM_MEMORY_BALANCE - MINIMUM_CHUNK_SIZE)/(MAXIMUM_MEMORY_BALANCE - NEAR_FULL)
        allow_restore_from_disk = False

        counter = 0
        while counter <= 100:

            # just wait for next check round
            sleep(CHECK_TIME_INTERVAL)

            # queue size report
            with open(MEMORY_BALANCING_REPORT, 'w') as report:
                report.write("work => %d\nmerge => %d\n%s"%(work.qsize(), merge.qsize(), message_report))

            # check for timeout
            if time_has_ended(since, TIMER_CHAINING_HOURS):
                exit_code = TIMESUP_EXIT;break

            # check for status
            if not os.path.isfile(CHAINING_EXECUTION_STATUS):
                exit_code = MANUAL_EXIT;break

            # check for processes activity
            if not reduce(lambda a, b:a or b, [worker.is_alive() for worker in workers]):
                exit_code = ERROR_EXIT;break

            # queue memory balancing
            memory_balance = work.qsize()
            message_report = ''

            # save memory
            if memory_balance > NEAR_FULL:
                items = []
                how_much = int(m * (memory_balance - MAXIMUM_MEMORY_BALANCE) + MAXIMUM_MEMORY_BALANCE)

                # warning for high memory usage
                if memory_balance > MAXIMUM_MEMORY_BALANCE:
                    with open(IMPORTANT_LOG, 'a') as log:log.write(f'[WARNING] more than {MAXIMUM_MEMORY_BALANCE} units are on memory!\n')
                    how_much = MAXIMUM_MEMORY_BALANCE
                    allow_restore_from_disk = False

                while len(items) == how_much:
                    get_one:ChainNode = work.get()

                    # avoid adding works that are not in working collection (first generation motifs)
                    if get_one.foundmap.collection != DEFAULT_COLLECTION:work.put(get_one)
                    else                                                :items.append(get_one)

                message_report += 'stored a chunk into disk\n'
                disk_queue.insert_all(items)

            # restore from disk
            elif memory_balance < NEAR_EMPTY:
                
                if not allow_restore_from_disk:
                    allow_restore_from_disk = True
                    continue

                items = disk_queue.pop_many(how_many=MINIMUM_CHUNK_SIZE)

                if items:
                    message_report += 'restored a chunk from disk (size=%d)\n'%(len(items))
                    for item in items:work.put(item)
                
                # there was no work on disk
                else:
                    if memory_balance == 0:counter += 1
                    else:counter = 0
                    message_report += 'failed to load work from disk (exit counter => %d)\n'%counter

    ############### end of processing #######################

    # IN CASE OF ERROR, KILL EVERYONE AND LEAVE
    # if exit_code == ERROR_EXIT:
    #     for worker in workers:worker.kill()
    #     global_pooler.kill()
    #     return exit_code
    
    # message the workers to terminate their job and merge for last time
    for _ in workers:
        message.put(EXIT_SIGNAL)

    is_there_alive = reduce(lambda a, b:a or b, [worker.is_alive() for worker in workers])
    join_timeout = 30 # minutes

    # should wait on workers but in limited time
    while is_there_alive and join_timeout:
        
        # 5 minute wait
        sleep(60 * 5)
        join_timeout -= 5

        is_there_alive = reduce(lambda a, b:a or b, [worker.is_alive() for worker in workers])

    # kill whoever is alive ignoring its merge signal
    for worker in workers:
        if worker.is_alive():
            print('[ERROR][PROCESS] worker (pid=%d) resist to die (killed by master)'%worker.pid)
            worker.kill()

    ########### all working process are dead #############
    # message global_pooler to terminate
    merge.put(EXIT_SIGNAL)
    global_pooler.join()

    rest_checkpoint = None

    # save rest of the works if not end
    if exit_code != END_EXIT:

        rest_work = []
        while True:
            try:rest_work.append(work.get_nowait())
            except Empty:break
        
        rest_checkpoint = save_the_rest(rest_work, on_sequence, q, dataset_dict[DATASET_NAME])
        # save_checkpoint(rest_work,
        #     unique_checkpoint_name(), 
        #     resumable=True, 
        #     on_sequence=on_sequence, 
        #     q=q, 
        #     dataset_name=dataset_dict[DATASET_NAME],
        #     change_collection=False)

        # save rest of the works only on files
        if not isinstance(rest_checkpoint, str):
            exit_code = ERROR_EXIT

        if MAIL_SERVICE:
            send_files_mail(
                strings=['REST OF JOBS HAS SENT - unfinished jobs has been saved'],
                additional_subject=' an unfinished end')

    return rest_checkpoint, exit_code



def test_process(queue:Queue):
    while True:
        item = queue.get()
        print(type(item))
        if item:continue
        break


if __name__ == '__main__':
    # test
    queue = Queue()
    process1 = Process(target=test_process, args=(queue,))
    process1.start()