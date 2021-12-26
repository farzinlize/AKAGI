# python libraries 
import os
from pool import AKAGIPool, get_AKAGI_pools_configuration
from time import time as currentTime
from time import strftime, gmtime
from getopt import getopt
import sys

# project imports
from GKmerhood import DummyTree, GKmerhood, GKHoodTree
from findmotif import find_motif_all_neighbours, multiple_layer_window_find_motif
from misc import brief_sequence, change_global_constant_py, log_it, make_compact_dataset, read_bundle, read_fasta, edit_distances_matrix, extract_from_fasta
from report import FastaInstance, OnSequenceAnalysis, aPWM, Ranking
from alignment import alignment_matrix
from twobitHandler import download_2bit
from onSequence import OnSequenceDistribution
from googledrive import connect_drive, download_checkpoint_from_drive, query_download_checkpoint, store_single_file
from checkpoint import load_checkpoint_file, load_collection, observation_checkpoint_name, save_checkpoint
from TrieFind import ChainNode, initial_chainNodes
from multi import END_EXIT, ERROR_EXIT, TIMESUP_EXIT, multicore_chaining_main
from mongo import run_mongod_server
from jaspar import read_pfm_save_pwm
from doctor import manual_initial

# importing constants
from constants import AUTO_DATABASE_SETUP, BRIEFING, BYTES_OR_PICKLE, CHECKPOINT, CHECKPOINT_TAG, CPLUS_WORKER, DATASET_NAME, DATASET_TREES, DEBUG_LOG, DEFAULT_COLLECTION, EXECUTION, EXTRACT_OBJ, FOUNDMAP_DISK, FOUNDMAP_MEMO, FOUNDMAP_MODE, GLOBAL_POOL_NAME, IMPORTANT_LOG, MAX_CORE, ON_SEQUENCE_ANALYSIS, PWM, P_VALUE, BINDING_SITE_LOCATION, ARG_UNSET, FIND_MAX, DELIMETER, SAVE_ONSEQUENCE_FILE, SEQUENCES, SEQUENCE_BUNDLES

# [WARNING] related to DATASET_TREES in constants 
# any change to one of these lists must be applied to another
TREES_TYPE = [DummyTree, GKHoodTree, GKHoodTree]

# default values for application arguments
class ARGS:
    def __init__(self) -> None:
        self.kmin = 5
        self.kmax = 8
        self.level = 6
        self.dmax = 1
        self.sequences = 'data/dm01r'
        self.gap = 3
        self.overlap = 2
        self.mask = None
        self.quorum = ARG_UNSET
        self.frame_size = 6
        self.gkhood_index = 0
        self.multilayer = False
        self.multicore = False
        self.ncores = MAX_CORE
        self.jaspar = ''
        self.name = None
        self.resume = False
        self.megalexa = 0
        self.onsequence = ''
        self.reference = 'hg18'
        self.disable_chaining = False
        self.nbank = 1
        self.pool = ''
        self.assist = None
        self.auto_order = b'00'
        self.path = ''
        self.compact_dataset = None
        self.manual_banking = False
        self.checkpoint = ''

def single_level_dataset(kmin, kmax, level, dmax):
    print('operation SLD: generating single level dataset\n\
        arguments -> kmin=%d, kmax=%d, level=%d, distance=%d'%(kmin, kmax, level, dmax))

    last_time = currentTime()
    gkhood = GKmerhood(kmin, kmax)
    print('GKhood instance generated in %s'%(strftime("%H:%M:%S", gmtime(currentTime() - last_time))))

    last_time =  currentTime()
    gkhood.single_level_dataset(dmax, level)
    print('dataset generated in %s'%(strftime("%H:%M:%S", gmtime(currentTime() - last_time))))


def FL_dataset(kmin, kmax, first_level, last_level, dmax):
    print('operation FLD: generating First-level-Last-level dataset\n\
        arguments -> kmin=%d, kmax=%d, first-level=%d, last-level=%d, distance=%d'%(kmin, kmax, first_level, last_level, dmax))

    last_time = currentTime()
    gkhood = GKmerhood(kmin, kmax)
    print('GKhood instance generated in %s'%(strftime("%H:%M:%S", gmtime(currentTime() - last_time))))

    last_time =  currentTime()
    gkhood.special_dataset_generate(dmax, first_level, last_level)
    print('dataset generated in %s'%(strftime("%H:%M:%S", gmtime(currentTime() - last_time))))


def motif_finding_chain(dataset_name, 
                        gkhood_index, 
                        frame_size, 
                        q, 
                        d, 
                        gap, 
                        overlap, 
                        multilayer=None, 
                        megalexa=None, 
                        chaining_disable=False,
                        manual_banking=False,
                        multicore=False, 
                        cores=1,
                        pfm=None,
                        banks=1,
                        resume=False,
                        on_sequence_compressed=None,
                        initial_pool='',
                        compact_dataset=None,
                        checkpoint:str=None):

    def observation(q, save_collection:str=None):

        if multilayer:
            assert isinstance(gkhood_index, list) and isinstance(d, list) and isinstance(frame_size, list)

            trees = [TREES_TYPE[index](DATASET_TREES[index][0], DATASET_TREES[index][1]) for index in gkhood_index]
            last_time = currentTime()
            motif_tree = multiple_layer_window_find_motif(trees, d, frame_size, sequences)
        else:
            assert isinstance(gkhood_index, int) and isinstance(d, int) and isinstance(frame_size, int)

            tree = TREES_TYPE[gkhood_index](DATASET_TREES[gkhood_index][0], DATASET_TREES[gkhood_index][1])
            last_time = currentTime()
            motif_tree = find_motif_all_neighbours(tree, d, frame_size, sequences)

        # nearly like SSMART objective function 
        if q == FIND_MAX:
            q = motif_tree.find_max_q()
            print('[find_max_q] q = %d'%q)

        motifs = motif_tree.extract_motifs(q, EXTRACT_OBJ)
        print('\nnumber of motifs->%d | execute time->%s'%(len(motifs), strftime("%H:%M:%S", gmtime(currentTime() - last_time))))

        while len(motifs) < megalexa:
            q = q - 1
            print('[lexicon] not enough (q--==%d)'%q)

            if q == 0:
                print('[lexicon] FAILED - exit with %d motifs'%(len(motifs)))
                break

            # adding new motifs with less frequency 
            # ONLY add new motifs with same q-value
            motifs += motif_tree.extract_motifs(q, EXTRACT_OBJ, greaterthan=False)

        print('[lexicon] lexicon size = %d'%len(motifs))

        # save collection may be refer to a file but we use it as collection, removing its name tag
        if save_collection == '':save_collection = observation_checkpoint_name(dataset_name, frame_size, d, multilayer, extention=False)
        elif save_collection.endswith(CHECKPOINT_TAG):save_collection = save_collection[:-len(CHECKPOINT_TAG)]

        print("[CHECKPOINT] saving observation? ", save_collection)

        # initialzed jobs should be returned as chain nodes
        # foundmaps will be stored in database or memory
        if save_collection:initial_jobs = initial_chainNodes([(motif.label, motif.foundmap) for motif in motifs], collection_name=save_collection)
        else              :initial_jobs = [ChainNode(motif.label, motif.foundmap) for motif in motifs]
        if not isinstance(initial_jobs, list):raise initial_jobs
        return initial_jobs


    print('operation MFC: finding motif using chain algorithm (tree_index(s):%s)\n\
        arguments -> f(s)=%s, q=%d, d(s)=%s, gap=%d, overlap=%d, dataset=%s\n\
        multi-layer=%s; megalexa=%d, resume=%s'%(
            str(gkhood_index), 
            str(frame_size), 
            q, 
            str(d), 
            gap, 
            overlap, 
            dataset_name,
            str(multilayer),
            megalexa,
            str(resume)))

    print('[FOUNDMAP] foundmap mode: %s'%FOUNDMAP_MODE)

    # reading sequences and its attachment including rank and summit
    sequences = read_fasta('%s.fasta'%(dataset_name))
    bundles = read_bundle('%s.bundle'%(dataset_name))

    if AUTO_DATABASE_SETUP:run_mongod_server()

    # make sequences shorter and ignore low score sequences for lower computations
    if BRIEFING:
        sequences, bundles = brief_sequence(sequences, bundles)
        assert len(sequences) == len(bundles)
        print('[BRIEFING] number of sequences = %d'%len(sequences))
        if __debug__:
            with open(DEBUG_LOG, 'a') as log:
                for seq, bundle in zip(sequences, bundles):
                    log.write('(len:%d,score:%f)'%(len(seq), bundle[P_VALUE]))
                log.write('\n')

    if q == ARG_UNSET:q = len(sequences)

    # assertion to catch error
    assert len(bundles) == len(sequences)
    assert q <= len(sequences) or q == FIND_MAX

    # ----------------------------------------------------------------------------------- #
    # [WARNING] in case of using previously calculated observation data
    #           you must set q argument as reported in observation report.
    # the program will set q to maximum but it could ignore many patterns in your lexicon
    #
    # [WARNING] it is recommended to specify q as argument for each run manually
    if q < 0 and resume:log_it(IMPORTANT_LOG, '[WARNING] argument q is not set to run on cached observation data - set to maximum');q = len(sequences)
    # ----------------------------------------------------------------------------------- #

    # search for observation checkpoint
    if not resume and CHECKPOINT:
        if checkpoint:
            if checkpoint.endswith(CHECKPOINT_TAG):motifs = load_checkpoint_file(checkpoint)
            else                                  :motifs = load_collection(checkpoint)
        else:
            checkpoint_collection = observation_checkpoint_name(dataset_name, frame_size, d, multilayer, extention=False)
            checkpoint_file = checkpoint_collection + CHECKPOINT_TAG

            # load from file if checkpoint file exist, otherwise load from database
            if os.path.isfile(checkpoint_file):motifs = load_checkpoint_file(checkpoint_file)
            else                              :motifs = load_collection(checkpoint_collection)

        if __debug__:log_it(DEBUG_LOG, f'[CHECKPOINT] observation data existed: {bool(motifs)}')

        # run and save observation data
        if not motifs:motifs = observation(q, save_collection=checkpoint)
    
    # run observation without checkpoint check
    elif not resume and not CHECKPOINT:motifs = observation(q)

    # # # # # # # #
    # - update motifs are reported as chain node from `observation()` 
    # chaining procedure required chain nodes instead of watch nodes 
    # zero_chain_nodes = [ChainNode(motif.label, motif.foundmap) for motif in motifs]
    # # # # # # # #

    if not resume and not motifs:print('[FATAL][ERROR] no observation data is available (error)');return

    ############### disable chaining? ###############
    if chaining_disable:
        # manual banking only works with disabled chaining
        if manual_banking:manual_initial(banks, motifs, dataset_name, on_sequence_compressed)
        print('[CHAINING] chaining is disabled - end of process')
        return
    ###############  start to chain   ###############

    # # # # # # # #  OnSequence data structure  # # # # # # # #
    # generate from motifs
    if not resume:
        try:
            generate_onsequence = OnSequenceDistribution(motifs, sequences)
            if CPLUS_WORKER:
                generate_onsequence.raw_file(filename=on_sequence_compressed)
                on_sequence = on_sequence_compressed
            else:
                on_sequence = generate_onsequence
        except Exception as error:print(f'[FATAL][ERROR] cant make OnSequence {error}');return
    # read compressed from file or just pass the compressed file location in case of cplus-worker
    else:
        if CPLUS_WORKER:on_sequence = on_sequence_compressed
        else           :on_sequence = OnSequenceDistribution(compressed_data=on_sequence_compressed)
    # save compressed for later (raw file for cplus-worker / compress uses python pickle)
    if SAVE_ONSEQUENCE_FILE:
        if BYTES_OR_PICKLE:on_sequence.raw_file(filename=on_sequence_compressed)
        else:              on_sequence.compress(filename=on_sequence_compressed)
    # reports for analysis
    if ON_SEQUENCE_ANALYSIS and isinstance(on_sequence, OnSequenceDistribution):print(on_sequence.analysis())
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # read pfm from jaspar and calculate pwm
    pwm = read_pfm_save_pwm(pfm)

    # making compact dataset for cplus-workers
    if compact_dataset:make_compact_dataset(compact_dataset, sequences, bundles, pwm)
    dataset_dict = {SEQUENCES:sequences, SEQUENCE_BUNDLES:bundles, PWM:pwm, DATASET_NAME:dataset_name}

    # load pool to start with
    if initial_pool:
        pool = AKAGIPool(get_AKAGI_pools_configuration(dataset_dict), collection_name='-'.join([EXECUTION, GLOBAL_POOL_NAME, 'resume']))
        pool.read_snap(filename=initial_pool)
    
    else:pool = None

    if multicore:
        last_time = currentTime()
        if not resume:code = multicore_chaining_main(cores, banks, motifs, on_sequence, dataset_dict, overlap, gap, q, compact_dataset=compact_dataset)
        else         :code = multicore_chaining_main(cores, banks, None, on_sequence, dataset_dict, overlap, gap, q, initial_flag=False, initial_pool=pool, compact_dataset=compact_dataset)

    else:        
        # changes must be applied
        raise NotImplementedError
        # last_time = currentTime()
        # chains = motif_chain(motifs, sequences, bundles, q, gap, overlap)
        
    print('chaining done in ', strftime("%H:%M:%S", gmtime(currentTime() - last_time)))
    print('finish code:', code)
    if   code == TIMESUP_EXIT:print(f'timsup for chaining')
    elif code == ERROR_EXIT  :print(f'something bad happened')
    elif code == END_EXIT    :print('all jobs done')


def auto_maintenance(args:ARGS):
    pass
    # sequences = read_fasta(args.sequences)

    # order = args.auto_order
    # if order & ORDER_COMPACT_BIT:
    #     make_compact_dataset(args.name, )


def sequences_distance_matrix(location):
    with open('%s.fasta'%location, 'r') as fasta, open('%s.matrix'%location, 'w') as matrix:
        sequences = []
        reading = False
        reading_pattern = False
        for line in fasta:
            if reading:
                if line[0] == '>':
                    reading = False
                    if len(sequences) != 0:
                        matrix.write(edit_distances_matrix(sequences))
                    sequences = []
                    matrix.write(line)
                    if 'pattern' in line:
                        reading_pattern = True
                else:
                    sequences += [line.split(',')[2]]
            else:
                if reading_pattern:
                    sequences += [line.replace('|', '')]
                    reading_pattern = False
                elif '>instances' in line:
                    reading = True
                matrix.write(line)
                
        if len(sequences) != 0:
            matrix.write(edit_distances_matrix(sequences))


def analysis_raw_statistics(dataset_name, results_location):

    # inner function for pattern analysis and ranking purposes
    def analysis_ranking_pattern():
        nonlocal pattern_analysis, alignment_set, pwm_ranking, current_pattern, analysis, sequences, binding_sites

        # pattern statistics extraction, score and ranking (*START*)
        pattern_statistics = pattern_analysis.extract_raw_statistics()

        # align all pattern instances for scoring
        align_matrix = alignment_matrix(alignment_set)
        alignment_set = []

        # measure score and ranking
        pwm_score = aPWM(align_matrix).score()
        pwm_ranking.add_entry(pwm_score, (current_pattern, pattern_statistics))

        # printing pattern statistics - and reset the analysis object
        analysis.write('>pattern\n%s\n>pattern statistics\n%s\n>pattern scores\n(aligned) PWM score -> %f\n'%(
            current_pattern, str(pattern_statistics), pwm_score))

        pattern_analysis = OnSequenceAnalysis(len(sequences), [len(seq) for seq in sequences], binding_sites=binding_sites)
        # pattern statistics extraction, score and ranking (*END*)


    sequences = read_fasta('data/%s.fasta'%(dataset_name))

    if dataset_name[-1] in 'rgm':
        dataset_name = dataset_name[:-1]

    binding_sites = [FastaInstance(instance_str) for instance_str in extract_from_fasta(open(BINDING_SITE_LOCATION, 'r'), dataset_name)]
    FSM = {'start':0, 'pattern':1, 'instances':2}

    # raw statistics -> result evaluation and validation using actual binding sites as answers
    overall_analysis = OnSequenceAnalysis(len(sequences), [len(seq) for seq in sequences], binding_sites=binding_sites)
    chain_analysis = OnSequenceAnalysis(len(sequences), [len(seq) for seq in sequences], binding_sites=binding_sites)
    pattern_analysis = OnSequenceAnalysis(len(sequences), [len(seq) for seq in sequences], binding_sites=binding_sites)

    # score metric -> ranking motif for filtering before evaluation
    pwm = aPWM()

    # ranking and alignment objects
    pwm_ranking = Ranking()
    alignment_set = []

    with open('%s.fasta'%results_location, 'r') as results, open('%s.analysis'%results_location, 'w') as analysis:
        mode = FSM['start']
        current_chain = 0
        current_pattern = ''
        for line in results:
            if mode == FSM['start']:
                if 'chain' in line:
                    current_chain += 1
                    analysis.write('>%d-chain\n'%current_chain)
                elif 'pattern' in line:
                    mode = FSM['pattern']
                elif 'instances' in line:
                    mode = FSM['instances']
            elif mode == FSM['pattern']:
                current_pattern = line[:-1]
                mode = FSM['start']
            elif mode == FSM['instances']:
                if 'chain' in line: # print pattern analysis and chain analysis

                    # pattern statistics extraction, score and ranking (*CALLING*)
                    analysis_ranking_pattern()

                    # printing chain statistics - use the predefined object and recreate it for next use
                    analysis.write('>%d-chain statistics\n%s\n'%(current_chain, str(chain_analysis.extract_raw_statistics())))
                    chain_analysis = OnSequenceAnalysis(len(sequences), [len(seq) for seq in sequences], binding_sites=binding_sites)

                    current_pattern = ''
                    current_chain += 1
                    mode = FSM['start']
                    analysis.write('>%d-chain\n'%current_chain)
                elif 'pattern' in line: # print only pattern analysis

                    # pattern statistics extraction, score and ranking (*CALLING*)
                    analysis_ranking_pattern()

                    mode = FSM['pattern']
                    current_pattern = ''
                else:
                    instance = FastaInstance(line)
                    pattern_analysis.add_motif(instance)
                    overall_analysis.add_motif(instance)
                    chain_analysis.add_motif(instance)

                    alignment_set += [instance.substring]

        # pattern last instances pattern statistics extraction, score and ranking (*CALLING*) 
        analysis_ranking_pattern()

        # print last chain and overall
        analysis.write('>%d-chain statistics\n%s\n'%(current_chain, str(chain_analysis.extract_raw_statistics())))
        analysis.write('>overall statistics\n%s\n'%(str(overall_analysis.extract_raw_statistics())))


def alignment_fasta(fasta_location):
    with open('%s.fasta'%fasta_location, 'r') as fasta, open('%s.align'%fasta_location, 'w') as align:
        read = False
        instances = []
        for line in fasta:
            if read:
                if '>' in line:
                    if instances:
                        alignments = alignment_matrix(instances)
                        for alignment in alignments:
                            align.write(alignment+'\n')
                    read = False
                    instances = []
                    align.write(line)
                else:
                    instances += [FastaInstance(line).substring]
            else:
                if 'instances' in line:
                    read = True
                align.write(line)


def download_observation_checkpoint(dataset_name, f, d, multilayer):

    checkpoint = observation_checkpoint_name(dataset_name, f, d, multilayer)

    for f in os.listdir():
        if f == checkpoint:
            print('[CHECKPOINT] already exist offline')
            return

    objects_file, drive = query_download_checkpoint(checkpoint)

    if objects_file == None:
        print('[CHECKPOINT] query not found')
        return

    # feed already exist drive instance
    download_checkpoint_from_drive(objects_file, drive=drive)
    

def upload_observation_checkpoint(dataset_name, f, d, multilayer, onsequence_name, checkpoint_file=''):

    checkpoint_collection = observation_checkpoint_name(dataset_name, f, d, multilayer, extention=False)
    if not checkpoint_file:checkpoint_file = checkpoint_collection + CHECKPOINT_TAG
    motifs = load_collection(checkpoint_collection)

    # check for offline check-points
    if not motifs:
        print('[CHECKPOINT] no checkpoint of interest was found, you need to run MFC operation first')
        print('[ERROR] upload failed')
        return
    
    # compact motifs and their observation data into a single file
    save_checkpoint(motifs, checkpoint_file, compact=True)

    # upload checkpoint into cloud
    google_drive = connect_drive()
    store_single_file(checkpoint_file, drive=google_drive)

    # upload compressed onsequence file into cloud if specified
    if(onsequence_name):store_single_file(onsequence_name, drive=google_drive)

    print(f"[UPLOAD] obseration {checkpoint_collection} is uploaded into cloud")
        

def testing(dataset_name):
    global FOUNDMAP_MODE

    sequences = read_fasta('%s.fasta'%(dataset_name))
    trees = [GKHoodTree(DATASET_TREES[index][0], DATASET_TREES[index][1]) for index in [1, 1]]

    FOUNDMAP_MODE = FOUNDMAP_MEMO
    motif_tree_disk = multiple_layer_window_find_motif(trees, [1, 1], [5, 6], sequences)

    FOUNDMAP_MODE = FOUNDMAP_DISK
    motif_tree_memo = multiple_layer_window_find_motif(trees, [1, 1], [5, 6], sequences)

    return motif_tree_memo, motif_tree_disk


if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise Exception('request command must be specified (read the description for supported commands)')

    # arguments and options
    shortopt = 'd:m:M:l:s:g:O:q:f:G:p:Qux:A:C:r:Xn:j:a:kh:b:RS:o:D:BP:'
    longopts = ['kmin=', 'kmax=', 'distance=', 'level=', 'sequences=', 'gap=', 'resume-chaining', 'manual-banking',
        'overlap=', 'mask=', 'quorum=', 'frame=', 'gkhood=', 'path=', 'find-max-q', 'bank=', 'auto-order=',
        'multi-layer', 'megalexa=', 'onsequence=', 'change=', 'reference=', 'disable-chaining', 'compact-dataset=',
        'multicore', 'ncores=', 'jaspar=', 'arguments=', 'check-point', 'name=', 'assist=', 'score-pool=', 'checkpoint=']

    # default values in ARGS object
    arguments = ARGS()

    command = sys.argv[1]

    opts, _ = getopt(sys.argv[2:], shortopt, longopts)
    for o, a in opts:
        if o in ['-m', '--kmin']:arguments.kmin = int(a)
        elif o in ['-M', '--kmax']:arguments.kmax = int(a)
        elif o in ['-l', '--level']:
            try:    arguments.level = int(a)
            except: arguments.level = [int(o) for o in a.split(DELIMETER)]
        elif o in ['-d', '--distance']:
            try:   arguments.dmax = int(a)
            except:arguments.dmax = [int(o) for o in a.split(DELIMETER)]
        elif o in ['-s', '--sequences']:arguments.sequences = a
        elif o in ['-g', '--gap']:arguments.gap = int(a)
        elif o in ['-O', '--overlap']:arguments.overlap = int(a)
        elif o == '--mask':arguments.mask = a
        elif o in ['-q', '--quorum']:arguments.quorum = int(a)
        elif o in ['-f', '--frame']: 
            try:   arguments.frame_size = int(a)
            except:arguments.frame_size = [int(o) for o in a.split(DELIMETER)]
        elif o in ['-G', '--gkhood']: 
            try:   arguments.gkhood_index = int(a)
            except:arguments.gkhood_index = [int(o) for o in a.split(DELIMETER)]
        elif o in ['-p', '--path']:arguments.path = a
        elif o in ['-Q', '--find-max-q']:arguments.quorum = FIND_MAX
        elif o in ['-u', '--multi-layer']:arguments.multilayer = True
        elif o in ['-x', '--megalexa']:arguments.megalexa = int(a)
        elif o in ['-A', '--onsequence']:arguments.onsequence = a
        elif o in ['-r', '--reference']:arguments.reference = a
        elif o == '--disable-chaining':arguments.disable_chaining = True
        elif o in ['-X', '--multicore']: arguments.multicore = True
        elif o in ['-n', '--ncores']:arguments.ncores = int(a)
        elif o in ['-j', '--jaspar']:arguments.jaspar = a
        elif o in ['-a', '--arguments']:
            with open(a, 'r') as arguments:opts += getopt(arguments.read().split(), shortopt, longopts)[0]
        elif o == '--name':arguments.name = a
        elif o in ['-h', '--assist']:arguments.assist = a
        elif o in ['-b', '--bank']:arguments.nbank = int(a)
        elif o in ['-R', '--resume-chaining']:arguments.resume = True
        elif o in ['-S', '--score-pool']:arguments.pool = a
        elif o in ['-o', '--auto-order']:arguments.auto_order = bytes.fromhex(a)
        elif o in ['-D', '--compact-dataset']:arguments.compact_dataset = a
        elif o in ['-B', '--manual-banking']:arguments.manual_banking = True
        elif o in ['-P', '--checkpoint']:arguments.checkpoint = a
        
        # only available with NOP command
        elif o in ['-C', '--change']:
            assert command == 'NOP'
            variable_name, new_value = a.split('=')
            change_global_constant_py(variable_name, new_value)


    if command == 'SLD':
        single_level_dataset(
            arguments.kmin, 
            arguments.kmax, 
            arguments.level, 
            arguments.dmax)
    elif command == 'MFC':
        motif_finding_chain(
            arguments.sequences, 
            arguments.gkhood_index, 
            arguments.frame_size, 
            arguments.quorum, 
            arguments.dmax, 
            arguments.gap, 
            arguments.overlap, 
            multilayer=arguments.multilayer,
            megalexa=arguments.megalexa,
            chaining_disable=arguments.disable_chaining,
            manual_banking=arguments.manual_banking,
            multicore=arguments.multicore,
            cores=arguments.ncores,
            pfm=arguments.jaspar,
            banks=arguments.nbank,
            resume=arguments.resume,
            on_sequence_compressed=arguments.onsequence,
            initial_pool=arguments.pool,
            compact_dataset=arguments.compact_dataset,
            checkpoint=arguments.checkpoint)
    elif command == 'SDM':
        sequences_distance_matrix(arguments.sequences)
    elif command == 'ARS':
        analysis_raw_statistics(arguments.sequences, arguments.path)
    elif command == 'ALG':
        alignment_fasta(arguments.path)
    elif command == 'FLD':
        assert isinstance(arguments.level, list)
        FL_dataset(
            arguments.kmin,
            arguments.kmax,
            arguments.level[0],
            arguments.level[1],
            arguments.dmax
        )
    elif command == '2BT':
        download_2bit(arguments.reference)
    elif command == 'TST':
        tree_m, tree_d = testing(arguments.sequences)
    elif command == 'DOC':
        download_observation_checkpoint(
            arguments.sequences, 
            arguments.frame_size, 
            arguments.dmax, 
            arguments.multilayer)
    elif command == 'UOC':
        upload_observation_checkpoint(
            arguments.sequences, 
            arguments.frame_size, 
            arguments.dmax, 
            arguments.multilayer,
            arguments.onsequence,
            checkpoint_file=arguments.checkpoint)
    elif command == 'IBM':
        pass
    elif command == 'MTH':
        auto_maintenance(arguments)
    elif command == 'NOP':
        pass
    else:
        print('[ERROR] command %s is not supported'%command)
