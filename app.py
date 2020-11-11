from time import time as currentTime
from time import strftime, gmtime
from getopt import getopt
from functools import reduce

from GKmerhood import GKmerhood, GKHoodTree
from findmotif import find_motif_all_neighbours, motif_chain
from misc import read_fasta, make_location, edit_distances_matrix, extract_from_fasta
from report import motif_chain_report, FastaInstance, OnSequenceAnalysis, aPWM, Ranking, colored_neighbours_analysis
from alignment import alignment_matrix

import sys


# importing constants

from constants import DATASET_TREES
from constants import HISTOGRAM_LOCATION
from constants import RESULT_LOCATION
from constants import BINDING_SITE_LOCATION

from constants import ARG_UNSET
from constants import FIND_MAX

def single_level_dataset(kmin, kmax, level, dmax):
    print('operation SLD: generating single level dataset\n\
        arguments -> kmin=%d, kmax=%d, level=%d, distance=%d'%(kmin, kmax, level, dmax))

    last_time = currentTime()
    gkhood = GKmerhood(kmin, kmax)
    print('GKhood instance generated in %f seconds'%(currentTime() - last_time))

    last_time =  currentTime()
    gkhood.single_level_dataset(dmax, level)
    print(strftime("%H:%M:%S", gmtime(currentTime() - last_time)))


def motif_finding_chain(dataset_name, gkhood_index, frame_size, q, d, gap, overlap, report, s_mask=None, color_frame=ARG_UNSET):
    print('operation MFC: finding motif using chain algorithm (tree:%s)\n\
        arguments -> f=%d, q=%d, d=%d, gap=%d, overlap=%d, dataset=%s\n\
        operation mode: %s; coloring_frame=%d'%(
            DATASET_TREES[gkhood_index][0], 
            frame_size, 
            q, 
            d, 
            gap, 
            overlap, 
            dataset_name,
            str(report[1]),
            color_frame))

    sequences = read_fasta('%s.fasta'%(dataset_name))

    if q == ARG_UNSET:
        q = len(sequences)

    assert q <= len(sequences) or q == FIND_MAX

    if s_mask != None:
        assert len(sequences) == len(s_mask)

    tree = GKHoodTree(DATASET_TREES[gkhood_index][0], DATASET_TREES[gkhood_index][1])

    last_time = currentTime()
    motif_tree = find_motif_all_neighbours(tree, d, frame_size, sequences)

    # nearly like SSMART objective function 
    if q == FIND_MAX:
        q = motif_tree.find_max_q()
        print('[find_max_q] q = %d'%q)

    motifs = motif_tree.extract_motifs(q, 0)
    print('\nnumber of motifs->%d | execute time->%s'%(len(motifs), strftime("%H:%M:%S", gmtime(currentTime() - last_time))))

    last_time = currentTime()
    chains = motif_chain(
        motifs, 
        sequences,
        q=q, 
        gap=gap,
        overlap=overlap, 
        sequence_mask=s_mask, 
        report=report, 
        report_directory=HISTOGRAM_LOCATION%(dataset_name, frame_size, d, q, gap, overlap))
    print('chaining done in ', strftime("%H:%M:%S", gmtime(currentTime() - last_time)))

    make_location('%s%s'%(RESULT_LOCATION, dataset_name))

    if report[1]:
        colored_neighbours_analysis(chains, sequences, color_frame, '%s%s-colored/'%(RESULT_LOCATION, dataset_name))
    else:
        motif_chain_report(motifs, '%s%s/f%d-d%d-q%d-g%d-o%d'%(RESULT_LOCATION, dataset_name, frame_size, d, q, gap, overlap), sequences)


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

        # pattern statisics extraction, score and ranking (*START*)
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
        # pattern statisics extraction, score and ranking (*END*)


    sequences = read_fasta('data/%s.fasta'%(dataset_name))

    if dataset_name[-1] in 'rgm':
        dataset_name = dataset_name[:-1]

    binding_sites = [FastaInstance(instance_str) for instance_str in extract_from_fasta(open(BINDING_SITE_LOCATION, 'r'), dataset_name)]
    FSM = {'start':0, 'pattern':1, 'instances':2}

    # raw statistics -> result evaluation and validation using actual binding sites as answers
    overal_analysis = OnSequenceAnalysis(len(sequences), [len(seq) for seq in sequences], binding_sites=binding_sites)
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

                    # pattern statisics extraction, score and ranking (*CALLING*)
                    analysis_ranking_pattern()

                    # printing chain statistics - use the predefined object and recreate it for next use
                    analysis.write('>%d-chain statistics\n%s\n'%(current_chain, str(chain_analysis.extract_raw_statistics())))
                    chain_analysis = OnSequenceAnalysis(len(sequences), [len(seq) for seq in sequences], binding_sites=binding_sites)

                    current_pattern = ''
                    current_chain += 1
                    mode = FSM['start']
                    analysis.write('>%d-chain\n'%current_chain)
                elif 'pattern' in line: # print only pattern analysis

                    # pattern statisics extraction, score and ranking (*CALLING*)
                    analysis_ranking_pattern()

                    mode = FSM['pattern']
                    current_pattern = ''
                else:
                    instance = FastaInstance(line)
                    pattern_analysis.add_motif(instance)
                    overal_analysis.add_motif(instance)
                    chain_analysis.add_motif(instance)

                    alignment_set += [instance.substring]

        # pattern last instances pattern statisics extraction, score and ranking (*CALLING*) 
        analysis_ranking_pattern()

        # print last chain and overall
        analysis.write('>%d-chain statistics\n%s\n'%(current_chain, str(chain_analysis.extract_raw_statistics())))
        analysis.write('>overall statistics\n%s\n'%(str(overal_analysis.extract_raw_statistics())))


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



if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise Exception('request command must be specified (read the description for supported commands)')

    # arguments and options
    shortopt = 'd:m:M:l:s:g:O:hq:f:G:p:c:Qu'
    longopts = ['kmin=', 'kmax=', 'distance=', 'level=', 'sequences=', 'gap=', 'color-frame=',
        'overlap=', 'histogram', 'mask=', 'quorum=', 'frame=', 'gkhood=', 'path=', 'find-max-q', 'multi-layer']

    # default values
    args_dict = {'kmin':5, 'kmax':8, 'level':6, 'dmax':1, 'sequences':'data/dm01r', 'gap':3, 'color-frame':2,
        'overlap':2, 'mask':None, 'quorum':ARG_UNSET, 'frame_size':6, 'gkhood_index':0, 'histogram_report':False, 'multi-layer':False}

    command = sys.argv[1]

    opts, args = getopt(sys.argv[2:], shortopt, longopts)
    for o, a in opts:
        if o in ['-m', '--kmin']:
            args_dict.update({'kmin':int(a)})
        elif o in ['-M', '--kmax']:
            args_dict.update({'kmax':int(a)})
        elif o in ['-l', '--level']:
            args_dict.update({'level':int(a)})
        elif o in ['-d', '--distance']:
            args_dict.update({'dmax':int(a)})
        elif o in ['-s', '--sequences']:
            args_dict.update({'sequences':a})
        elif o in ['-g', '--gap']:
            args_dict.update({'gap':int(a)})
        elif o in ['-O', '--overlap']:
            args_dict.update({'overlap':int(a)})
        elif o == '--mask':
            args_dict.update({'mask':a})
        elif o in ['-h', '--histogram']:
            args_dict.update({'histogram_report':True})
        elif o in ['-q', '--quorum']:
            args_dict.update({'quorum':int(a)})
        elif o in ['-f', '--frame']:
            args_dict.update({'frame_size':int(a)})
        elif o in ['-G', '--gkhood']:
            args_dict.update({'gkhood_index':int(a)})
        elif o in ['-p', '--path']:
            args_dict.update({'path':a})
        elif o in ['-c', '--color-frame']:
            args_dict.update({'color-frame':int(a)})
        elif o in ['-Q', '--find-max-q']:
            args_dict.update({'quorum':FIND_MAX})
        elif o in ['-u', '--multi-layer']:
            args_dict.update({'multi-layer':True})


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
            s_mask=args_dict['mask'])
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
    else:
        print('[ERROR] command %s is not supported'%command)
