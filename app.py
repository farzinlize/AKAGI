# python libraries 
import os
from time import time as currentTime
from time import strftime, gmtime
from getopt import getopt
from typing import List
from pymongo.errors import ServerSelectionTimeoutError
import sys

# project imports
from FoundMap import initial_readonlymaps
from GKmerhood import DummyTree, GKmerhood, GKHoodTree
from findmotif import find_motif_all_neighbours, multiple_layer_window_find_motif
from misc import brief_sequence, change_global_constant_py, read_bundle, read_fasta, make_location, edit_distances_matrix, extract_from_fasta, read_pfm_save_pwm
from report import FastaInstance, OnSequenceAnalysis, aPWM, Ranking
from alignment import alignment_matrix
from twobitHandler import download_2bit
from jaspar import costume_table_jaspar, get_jaspar_raw
from peakseq import annotation_to_sequences
from pause import resume_any_cloud
from onSequence import OnSequenceDistribution
from googledrive import download_checkpoint_from_drive, query_download_checkpoint, store_checkpoint_to_cloud
from checkpoint import load_checkpoint, observation_checkpoint_name, save_checkpoint
from TrieFind import ChainNode
from multi import END_EXIT, ERROR_EXIT, TIMESUP_EXIT, multicore_chaining_main
from networking import AssistanceService
from mongo import run_mongod_server

# importing constants
from constants import APPDATA_PATH, AUTO_DATABASE_SETUP, BRIEFING, CHECKPOINT_TAG, DATASET_NAME, DATASET_TREES, DEFAULT_COLLECTION, EXTRACT_OBJ, FOUNDMAP_DISK, FOUNDMAP_MEMO, FOUNDMAP_MODE, LUCKY_SHOT, MAX_CORE, ON_SEQUENCE_ANALYSIS, PWM, P_VALUE, BINDING_SITE_LOCATION, ARG_UNSET, FIND_MAX, DELIMETER, SAVE_OBSERVATION_CLOUD, SEQUENCES, SEQUENCE_BUNDLES, BEST_PATTERNS_POOL, PC_NAME

# [WARNING] related to DATASET_TREES in constants 
# any change to one of these lists must be applied to another
TREES_TYPE = [DummyTree, GKHoodTree, GKHoodTree]


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
                        report, 
                        s_mask=None, 
                        color_frame=ARG_UNSET, 
                        multilayer=None, 
                        megalexa=None, 
                        additional_name='',
                        chaining_disable=False,
                        multicore=False, 
                        cores=1,
                        pfm=None,
                        checkpoint=None,
                        cloud=SAVE_OBSERVATION_CLOUD):

    def observation(q, save_collection=DEFAULT_COLLECTION):

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

        # only return label and foundmap for forthur use as chain node instead of watch node
        # make foundmap read-only afterward
        # may failed due to database operation but if its not about server being down, so it will just file another shot for luck
        may_fail = LUCKY_SHOT
        while may_fail:
            inserted_maps = initial_readonlymaps([motif.foundmap for motif in motifs], save_collection)
            if isinstance(inserted_maps, ServerSelectionTimeoutError):return
            if not isinstance(inserted_maps, list):may_fail -= 1

        if not isinstance(inserted_maps, list):return
        return [ChainNode(motif.label, foundmap) for motif, foundmap in zip(motifs, inserted_maps)]


    print('operation MFC: finding motif using chain algorithm (tree_index(s):%s)\n\
        arguments -> f(s)=%s, q=%d, d(s)=%s, gap=%d, overlap=%d, dataset=%s\n\
        operation mode: %s; coloring_frame=%d; multi-layer=%s; megalexa=%d'%(
            str(gkhood_index), 
            str(frame_size), 
            q, 
            str(d), 
            gap, 
            overlap, 
            dataset_name,
            str(report[1]),
            color_frame,
            str(multilayer),
            megalexa))

    print('[FOUNDMAP] foundmap mode: %s'%FOUNDMAP_MODE)

    # reading sequences and its attachment including rank and summit
    sequences = read_fasta('%s.fasta'%(dataset_name))
    bundles = read_bundle('%s.bundle'%(dataset_name))
    if not chaining_disable:
        pwm = read_pfm_save_pwm(pfm)
    # bundle_name = dataset_name.split('/')[-1]

    if AUTO_DATABASE_SETUP:run_mongod_server()

    # make sequences shorter and ignore low score sequences for lower computations
    if BRIEFING:
        sequences, bundles = brief_sequence(sequences, bundles)
        assert len(sequences) == len(bundles)
        print('[BRIEFING] number of sequences = %d'%len(sequences))
        for seq, bundle in zip(sequences, bundles):
            print('(len:%d,score:%f)'%(len(seq), bundle[P_VALUE]), end=' ', flush=True)
        print('')

    if q == ARG_UNSET:q = len(sequences)

    # assertion to catch error
    assert len(bundles) == len(sequences)
    assert q <= len(sequences) or q == FIND_MAX
    if s_mask != None:assert len(sequences) == len(s_mask)

    # search for observation checkpoint
    if checkpoint:
        checkpoint_file = observation_checkpoint_name(dataset_name, frame_size, d, multilayer)
        motifs = load_checkpoint(checkpoint_file, resumable=False)

        # run and save observation data
        if motifs == None:
            motifs = observation(q, save_collection=checkpoint_file.split('.')[0])
            save_checkpoint(motifs, checkpoint_file)
            # if cloud:store_checkpoint_to_cloud(checkpoint_file, protected_collection) #TODO: not working with mongo
    
    # run observation without checkpoint check
    else:
        motifs = observation(q)

    # # # # # # # #
    # - update motifs are reported as chain node from `observation()` 
    # chaining procedure required chain nodes instead of watch nodes 
    # zero_chain_nodes = [ChainNode(motif.label, motif.foundmap) for motif in motifs]

    if chaining_disable:print('[CHAINING] chaining is disabled - end of process');return
    if not motifs:print('[FATAL][ERROR] no observation data is available (error)');return

    try                      :on_sequence = OnSequenceDistribution(motifs, sequences)
    except Exception as error:print(f'[FATAL][ERROR] cant make OnSequence {error}');return

    # reports for analysis
    if ON_SEQUENCE_ANALYSIS:print(on_sequence.analysis())

    if multicore:
        dataset_dict = {SEQUENCES:sequences, SEQUENCE_BUNDLES:bundles, PWM:pwm, DATASET_NAME:dataset_name}
        last_time = currentTime()
        rest, code = multicore_chaining_main(cores, motifs, on_sequence, dataset_dict, overlap, gap, q)
    else:        
        # changes must be applied
        raise NotImplementedError
        # last_time = currentTime()
        # chains = motif_chain(motifs, sequences, bundles, q, gap, overlap)
        
    print('chaining done in ', strftime("%H:%M:%S", gmtime(currentTime() - last_time)))
    print('finish code:', code)
    if   code == TIMESUP_EXIT:print(f'timsup for chaining - rest is saved at {rest}')
    elif code == ERROR_EXIT  :print(f'something bad happened -> error was {rest}')
    elif code == END_EXIT    :print('all jobs done')

    # make_location('%s%s%s'%(RESULT_LOCATION, dataset_name, additional_name))

    if report[1]:
        pass
        # colored_neighbours_analysis(chains, sequences, color_frame, '%s%s-colored/'%(RESULT_LOCATION, dataset_name))
    else:
        pass
        # motif_chain_report(motifs, '%s%s%s/f%s-d%s-q%d-g%d-o%d'%(RESULT_LOCATION, dataset_name, additional_name, str(frame_size), str(d), q, gap, overlap), sequences)


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
    

def upload_observation_checkpoint(dataset_name, f, d, multilayer):

    checkpoint = observation_checkpoint_name(dataset_name, f, d, multilayer)

    motifs = load_checkpoint(checkpoint)

    # check for offline check-points
    if motifs == None:
        print('[CHECKPOINT] no checkpoint of interest was found, you need to run MFC operation first')
        print('[ERROR] upload failed')
        return

    directory_name = APPDATA_PATH + checkpoint.split('.')[0] + '/'
    
    store_checkpoint_to_cloud(checkpoint, directory_name)
        

def resume_chaining(cores, overlap, gap, checkpoint_name, assist_network):

    # manual checkpoint input name
    if checkpoint_name:
        checkpoint = checkpoint_name

    # download helping package of work
    elif assist_network:
        master = AssistanceService.connect_to_master(assist_network, is_new=True)
        checkpoint = master.get_checkpoint(working_on_it=True)

    # auto-find resumable checkpoints local or cloud
    else:
        offline_checkpoints = [f for f in os.listdir() if f.endswith(CHECKPOINT_TAG) and f[0]=='R']

        if offline_checkpoints:
            checkpoint = offline_checkpoints[0]
        else:
            checkpoint = resume_any_cloud()
    
    if checkpoint == None:
        print('[APP] found nothing to resume - end')
        return

    motifs, on_sequence, q, dataset_name = load_checkpoint(checkpoint, resumable=True)
    pfm = get_jaspar_raw(costume_table_jaspar(dataset_name))

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
    # 
    # [AKAGI EXE] data prepartion for caught resumable checkpoint
    if not os.path.exists(f'{dataset_name}.fasta'): # or '.bundle'
        annotation_to_sequences(dataset_name+'.cod', '2bits/hg18.2bit')
    sequences = read_fasta('%s.fasta'%(dataset_name))
    bundles = read_bundle('%s.bundle'%(dataset_name))
    pwm = read_pfm_save_pwm(pfm)
    #
    dataset_dict = {SEQUENCES:sequences, SEQUENCE_BUNDLES:bundles, PWM:pwm, DATASET_NAME:dataset_name}
    rest_checkpoint, finish_code = multicore_chaining_main(cores, motifs, on_sequence, dataset_dict, overlap, gap, q)
    #
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 

    # report back to the main application
    if assist_network:
        master = AssistanceService.connect_to_master(assist_network, is_new=False)
        master.report_back(BEST_PATTERNS_POOL%(PC_NAME, os.getpid()), finish_code)
        if finish_code == TIMESUP_EXIT:
            master.copy_checkpoint(rest_checkpoint)



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

    # generating necessary paths for application to run 
    make_location(APPDATA_PATH)

    # arguments and options
    shortopt = 'd:m:M:l:s:g:O:hq:f:G:p:c:QuFx:t:C:r:Pn:j:a:kh:'
    longopts = ['kmin=', 'kmax=', 'distance=', 'level=', 'sequences=', 'gap=', 'color-frame=',
        'overlap=', 'histogram', 'mask=', 'quorum=', 'frame=', 'gkhood=', 'path=', 'find-max-q', 
        'multi-layer', 'feature', 'megalexa=', 'separated=', 'change=', 'reference=', 'disable-chaining',
        'multicore', 'ncores=', 'jaspar=', 'arguments=', 'check-point', 'name=', 'assist=']

    # default values
    args_dict = {'kmin':5, 'kmax':8, 'level':6, 'dmax':1, 'sequences':'data/dm01r', 'gap':3, 'color-frame':2,
        'overlap':2, 'mask':None, 'quorum':ARG_UNSET, 'frame_size':6, 'gkhood_index':0, 'histogram_report':False, 
        'multi-layer':False, 'megalexa':0, 'additional_name':'', 'reference':'hg18', 'disable_chaining':False,
        'multicore': False, 'ncores':MAX_CORE, 'jaspar':'', 'checkpoint':True, 'name':None, 'assist':None}

    feature_update = {'dmax':[1,1,1], 'frame_size':[6,7,8], 'gkhood_index':[0,0,1], 'multi-layer':True, 
        'megalexa':500, 'quorum':FIND_MAX}

    command = sys.argv[1]

    opts, _ = getopt(sys.argv[2:], shortopt, longopts)
    for o, a in opts:
        if o in ['-m', '--kmin']:args_dict.update({'kmin':int(a)})
        elif o in ['-M', '--kmax']:args_dict.update({'kmax':int(a)})
        elif o in ['-l', '--level']:
            try: args_dict.update({'level':int(a)})
            except: args_dict.update({'level':[int(o) for o in a.split(DELIMETER)]})
        elif o in ['-d', '--distance']:
            try:args_dict.update({'dmax':int(a)})
            except:args_dict.update({'dmax':[int(o) for o in a.split(DELIMETER)]})
        elif o in ['-s', '--sequences']:args_dict.update({'sequences':a})
        elif o in ['-g', '--gap']:args_dict.update({'gap':int(a)})
        elif o in ['-O', '--overlap']:args_dict.update({'overlap':int(a)})
        elif o == '--mask':args_dict.update({'mask':a})
        elif o in ['-h', '--histogram']:args_dict.update({'histogram_report':True})
        elif o in ['-q', '--quorum']:args_dict.update({'quorum':int(a)})
        elif o in ['-f', '--frame']: 
            try:args_dict.update({'frame_size':int(a)})
            except:args_dict.update({'frame_size':[int(o) for o in a.split(DELIMETER)]})
        elif o in ['-G', '--gkhood']: 
            try:args_dict.update({'gkhood_index':int(a)})
            except:args_dict.update({'gkhood_index':[int(o) for o in a.split(DELIMETER)]})
        elif o in ['-p', '--path']:args_dict.update({'path':a})
        elif o in ['-c', '--color-frame']:args_dict.update({'color-frame':int(a)})
        elif o in ['-Q', '--find-max-q']:args_dict.update({'quorum':FIND_MAX})
        elif o in ['-u', '--multi-layer']:args_dict.update({'multi-layer':True})
        elif o == '-F':args_dict.update(feature_update)
        elif o in ['-x', '--megalexa']:args_dict.update({'megalexa':int(a)})
        elif o in ['-t', '--separated']:args_dict.update({'additional_name':a})
        elif o in ['-r', '--reference']:args_dict.update({'reference':a})
        elif o == '--disable-chaining':args_dict.update({'disable_chaining':True})
        elif o in ['-P', '--multicore']: args_dict.update({'multicore':True})
        elif o in ['-n', '--ncores']:args_dict.update({'ncores':int(a)})
        elif o in ['-j', '--jaspar']:args_dict.update({'jaspar':a})
        elif o in ['-a', '--arguments']:
            with open(a, 'r') as arguments:opts += getopt(arguments.read().split(), shortopt, longopts)[0]
        elif o == '--name':args_dict.update({'name':a})
        elif o in ['-h', '--assist']:args_dict.update({'assist':a})
        
        # only available with NOP command
        elif o in ['-C', '--change']:
            assert command == 'NOP'
            variable_name, new_value = a.split('=')
            change_global_constant_py(variable_name, new_value)


    if command == 'SLD':
        single_level_dataset(
            args_dict['kmin'], 
            args_dict['kmax'], 
            args_dict['level'], 
            args_dict['dmax'])
    elif command == 'MFC':
        motif_finding_chain(
            args_dict['sequences'], 
            args_dict['gkhood_index'], 
            args_dict['frame_size'], 
            args_dict['quorum'], 
            args_dict['dmax'], 
            args_dict['gap'], 
            args_dict['overlap'], 
            report=(args_dict['histogram_report'], False),
            s_mask=args_dict['mask'],
            multilayer=args_dict['multi-layer'],
            megalexa=args_dict['megalexa'],
            additional_name=args_dict['additional_name'],
            chaining_disable=args_dict['disable_chaining'],
            multicore=args_dict['multicore'],
            cores=args_dict['ncores'],
            pfm=args_dict['jaspar'],
            checkpoint=args_dict['checkpoint'])
    elif command == 'SDM':
        sequences_distance_matrix(args_dict['sequences'])
    elif command == 'ARS':
        analysis_raw_statistics(args_dict['sequences'], args_dict['path'])
    elif command == 'ALG':
        alignment_fasta(args_dict['path'])
    elif command == 'CNM':
        motif_finding_chain(
            args_dict['sequences'], 
            args_dict['gkhood_index'], 
            args_dict['frame_size'], 
            args_dict['quorum'], 
            args_dict['dmax'], 
            args_dict['gap'], 
            args_dict['overlap'], 
            report=(False, True),
            color_frame=args_dict['color-frame'])
    elif command == 'FLD':
        assert isinstance(args_dict['level'], list)
        FL_dataset(
            args_dict['kmin'],
            args_dict['kmax'],
            args_dict['level'][0],
            args_dict['level'][1],
            args_dict['dmax']
        )
    elif command == '2BT':
        download_2bit(args_dict['reference'])
    elif command == 'TST':
        tree_m, tree_d = testing(args_dict['sequences'])
    elif command == 'DOC':
        download_observation_checkpoint(
            args_dict['sequences'], 
            args_dict['frame_size'], 
            args_dict['dmax'], 
            args_dict['multi-layer'])
    elif command == 'UOC':
        upload_observation_checkpoint(
            args_dict['sequences'], 
            args_dict['frame_size'], 
            args_dict['dmax'], 
            args_dict['multi-layer'])
    elif command == 'RCH':
        resume_chaining(
            args_dict['ncores'], 
            args_dict['overlap'], 
            args_dict['gap'],
            args_dict['name'],
            args_dict['assist'])
    elif command == 'NOP':
        pass
    else:
        print('[ERROR] command %s is not supported'%command)
