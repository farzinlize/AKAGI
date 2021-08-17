# python libraries 
import os
from functools import reduce
from queue import Empty
from time import sleep
from datetime import datetime
from multiprocessing import Process, Queue
from typing import List
from pymongo.errors import ServerSelectionTimeoutError

# project modules
from mongo import get_bank_client, get_client, initial_akagi_database, serve_database_server
from checkpoint import lock_checkpoint, query_resumable_checkpoints, remove_checkpoint
from networking import AssistanceService
from report_email import send_files_mail
from pause import save_the_rest, time_has_ended
from pool import AKAGIPool, get_AKAGI_pools_configuration
from misc import QueueDisk, log_it
from TrieFind import ChainNode, initial_chainNodes, pop_chain_node
from onSequence import OnSequenceDistribution
from findmotif import next_chain

# settings and global variables
from constants import APPDATA_PATH, BANK_NAME, BANK_PATH, BANK_PORTS_REPORT, CHAINING_EXECUTION_STATUS, CHAINING_PERMITTED_SIZE, CHECK_TIME_INTERVAL, COMMAND_WHILE_CHAINING, CONTINUE_SIGNAL, CR_FILE, DATASET_NAME, DEFAULT_COLLECTION, EXECUTION, GLOBAL_POOL_NAME, GOOD_HIT, HELP_CLOUD, HELP_PORTION, HOPEFUL, IMPORTANT_LOG, MAIL_SERVICE, MAXIMUM_MEMORY_BALANCE, MAX_CORE, MEMORY_BALANCING_REPORT, MINIMUM_CHUNK_SIZE, MONGOD_SHUTDOWN_COMMAND, MONGO_PORT, NEAR_EMPTY, NEAR_FULL, NEED_HELP, PARENT_WORK, PERMIT_RESTORE_AFTER, POOL_HIT_SCORE, POOL_TAG, PROCESS_ENDING_REPORT, PROCESS_REPORT_FILE, QUEUE_COLLECTION, SAVE_SIGNAL, STATUS_RUNNING, STATUS_SUSSPENDED, TIMER_CHAINING_HOURS, EXIT_SIGNAL

# global multi variables
MANUAL_EXIT = -3
ERROR_EXIT = -2
TIMESUP_EXIT = -1
END_EXIT = 0


def chaining_thread_and_local_pool(bank_port, message: Queue, merge: Queue, on_sequence: OnSequenceDistribution, dataset_dict, overlap, gap, q):

    def error_handler(error):

        # save the working motif in file if exist as chain node
        if isinstance(motif, ChainNode):
            with open('process_%d.error', 'w') as errorfile:
                errorfile.write(motif.to_byte())

        # in case of database server down -> infrom administration and wait for signal in message
        if isinstance(error, ServerSelectionTimeoutError):
            with open(IMPORTANT_LOG, 'a') as log:log.write(f'[PID:{os.getpid()}] server down (port :{bank_port})')
            signal = message.get()

            # exit signal
            if signal == EXIT_SIGNAL:
                merge.put(local_pool)
                report.write('EXIT ON FAILURE\n' + PROCESS_ENDING_REPORT%(jobs_done_by_me, chaining_done_by_me))
                report.close()
                raise error
            
            # back to normal (but with an initial wait)
            # wait for all processes to get their messages and then go
            elif signal == CONTINUE_SIGNAL:sleep(5);return

        # cant handle that shit I guess
        else:
            merge.put(local_pool)
            report.write('EXIT ON FAILURE\n' + PROCESS_ENDING_REPORT%(jobs_done_by_me, chaining_done_by_me))
            report.close()
            raise error


    # local ranking pools
    local_pool = AKAGIPool(get_AKAGI_pools_configuration(dataset_dict))
    jobs_done_by_me = 0
    chaining_done_by_me = 0
    bank_client = get_bank_client(bank_port, connect=True)

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
            
            # in case of mistakenly pick someone else's signal
            elif signal == CONTINUE_SIGNAL:
                message.put(CONTINUE_SIGNAL)

        # obtaining a job
        motif: ChainNode = pop_chain_node(bank_client)
        if not isinstance(motif, ChainNode):error_handler(motif);continue
        jobs_done_by_me += 1

        # evaluation the job (motif)
        good_enough = 0
        go_merge = False
        judge_decision = local_pool.judge(motif)
        
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
        next_motifs, used_nodes_or_error = next_chain(motif, on_sequence, overlap, gap, q, report=report, chain_id=chaining_done_by_me)
        report.write(f'CHAINING({datetime.now() - last_time}) | ')

        # report and close
        report.write('USED NODES COUNT %d | '%used_nodes_or_error)

        # mongoDB insertion and checking for error
        last_time = datetime.now()
        next_patterns = initial_chainNodes([(motif.label + nexty.label, nexty.foundmap) for nexty in next_motifs], QUEUE_COLLECTION, bank_client)
        if not isinstance(next_patterns, list):error_handler(next_patterns);continue

        report.write(f'MONGO({datetime.now() - last_time})\n')

        # delete unnecessary parts
        for next_motif in next_motifs:del next_motif
        del motif

        chaining_done_by_me += 1
        report.flush()
        

def global_pool_thread(merge: Queue, dataset_dict, initial_pool:AKAGIPool):
    
    report_count = 0
    # client = get_client(connect=True)

    if initial_pool :global_pool = initial_pool
    else            :global_pool = AKAGIPool(get_AKAGI_pools_configuration(dataset_dict), collection_name='-'.join([EXECUTION, GLOBAL_POOL_NAME]))

    while True:

        merge_request: AKAGIPool = merge.get()

        # check for message
        if isinstance(merge_request, str):

            global_pool.save_snap()
            if   merge_request==EXIT_SIGNAL:return
            elif merge_request==SAVE_SIGNAL:continue

        # merging
        global_pool.merge(merge_request)

        # top ten report in window file
        with open(CR_FILE, 'w') as window:

            # time stamp
            window.write(str(datetime.now()) + ' | report #%d\n\n'%report_count)
            report_count += 1

            # table reports
            window.write(global_pool.top_ten_reports())

        # saving in database
        # global_pool.save(mongo_client=client)


# a copy of 'chaining_thread_and_local_pool' function but with keeping eye on work queue for finish
# [WARNING] deprecated function dont use it!
# PARENT_WORK should be False


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

        
def multicore_chaining_main(cores_order, 
                            bank_order,
                            initial_works: List[ChainNode], 
                            on_sequence:OnSequenceDistribution, 
                            dataset_dict, 
                            overlap, 
                            gap, 
                            q, 
                            initial_flag=True,
                            network=False, 
                            initial_pool=None):
    
    try   :available_cores = len(os.sched_getaffinity(0))
    except:available_cores = 'unknown'

    print(f'[CHAINING][MULTICORE] number of available cores: {available_cores}')

    # making status file
    with open(CHAINING_EXECUTION_STATUS, 'w') as status:status.write(STATUS_RUNNING)

    # auto maximize core usage (1 worker per core)
    if cores_order == MAX_CORE:
        if available_cores == 'unknown':
            print('[FATAL][ERROR] number of available cores are unknown')
            return ERROR_EXIT
        cores = available_cores - int(PARENT_WORK)

    # order custom number of workers
    else:cores = cores_order

    # initializing synchronized queues
    merge =   Queue()   # merging requests to a global pool
    message = Queue()   # message box to terminate workers loop (higher priority)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #
    #                execute banks to resume
    #                           /
    #                initializing data banks
    #
    bank_ports = []
    for i in range(bank_order):
        new_bank_port = MONGO_PORT + 20 + i*10
        bank_ports.append(new_bank_port)

        # -> run and config mongod servers on different ports
        if initial_flag:
            try:initial_akagi_database(BANK_NAME%i, BANK_PATH%i, new_bank_port, serve=True)
            except Exception as e:print(f'[FATAL][ERROR] something went wrong {e}');return ERROR_EXIT
        # -> serve mongod on previously initiated banks 
        else:
            try:serve_database_server(BANK_NAME%i,BANK_PATH%i, new_bank_port)
            except Exception as e:print(f'[FATAL][ERROR] something went wrong {e}');return ERROR_EXIT

    # report bank and their ports
    with open(BANK_PORTS_REPORT, 'w') as pr:pr.write('\n'.join([f'bank{index}:{port}' for index, port in enumerate(bank_ports)]))

    # -> static job distribution between banks
    if initial_works:
        bank_initial_lists = [[] for _ in range(bank_order)]
        for index, motif in enumerate(initial_works):
            bank_initial_lists[index%bank_order].append(motif)

        # -> insert jobs into banks
        for index, port in enumerate(bank_ports):
            bank_client = get_bank_client(port)
            result = initial_chainNodes([(m.label, m.foundmap) for m in bank_initial_lists[index]], QUEUE_COLLECTION, bank_client)
            if not isinstance(result, list):print(f'[FATAL][ERROR] something went wrong {result}');return ERROR_EXIT
            del result # parent doesn't need job objects 
            bank_client.close()
    #
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # initial threads
    workers = [Process(target=chaining_thread_and_local_pool, args=(bank_ports[i%bank_order],message,merge,on_sequence,dataset_dict,overlap,gap,q)) for i in range(cores)]
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
        raise Exception('PARENT_WORK = True is deprecated, change app configuration')
        # exit_code = parent_chaining(work, merge, on_sequence, dataset_dict, overlap, gap, q)

    # parent is in charge of auto-administration
    else:
        exit_code = END_EXIT
        exec_time = datetime.now()
        counter = 0
        while counter <= 100:

            # just wait for next check round
            sleep(CHECK_TIME_INTERVAL)
            loop_time = datetime.now()

            ############## PHASE ONE: CHECKING ##############

            # check for timeout
            if time_has_ended(exec_time, TIMER_CHAINING_HOURS):
                exit_code = TIMESUP_EXIT;break

            # check for status
            if not os.path.isfile(CHAINING_EXECUTION_STATUS):
                exit_code = MANUAL_EXIT;break

            # check for processes activity
            if not reduce(lambda a, b:a or b, [worker.is_alive() for worker in workers]):
                exit_code = ERROR_EXIT;break

            # check for commands while chaining
            if os.path.isfile(COMMAND_WHILE_CHAINING):
                with open(COMMAND_WHILE_CHAINING, 'r') as commands:
                    for command in commands:

                        # manually command to save global pool
                        if   command == SAVE_SIGNAL:
                            merge.put(SAVE_SIGNAL)

                        # signal workers to continue 
                        elif command.startswith(CONTINUE_SIGNAL):
                            how_many = int(command.split()[1])
                            for _ in range(how_many):message.put(CONTINUE_SIGNAL)

                        elif command.startswith('reset'):
                            bank_index = int(command.split()[1])
                            try:serve_database_server(BANK_NAME%bank_index, BANK_PATH%bank_index, bank_ports[bank_index])
                            except Exception as e:log_it(IMPORTANT_LOG, f'[PARENT] can not run database server bank{bank_index}\n{e}')

                        # ignore and log wrong commands
                        else:log_it(IMPORTANT_LOG, f'[PARENT] command not recognized {command}')

                # delete executed commands
                os.remove(COMMAND_WHILE_CHAINING)

            ############## PHASE TWO: BALANCING (canceled) ##############

            # queue size report
            with open(MEMORY_BALANCING_REPORT, 'w') as report:
                report.write(f"merge => {merge.qsize()}\nmessage => {message.qsize()}\nloop time =>{datetime.now() - loop_time}")

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

    ######## shut down banks 
    for index in range(len(bank_ports)):os.system(MONGOD_SHUTDOWN_COMMAND%(BANK_PATH%index))

    return exit_code


def manual_command(commands):
    with open(COMMAND_WHILE_CHAINING, 'w') as commandline:
        for command in commands:
            commandline.write(command + '\n')


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