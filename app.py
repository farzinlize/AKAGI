from time import time as currentTime
from time import strftime, gmtime
from getopt import getopt
from functools import reduce

from GKmerhood import GKmerhood, GKHoodTree
from findmotif import find_motif_all_neighbours, motif_chain
from misc import read_fasta, make_location
from report import motif_chain_report

import sys

# Global Variables
DATASET_TREES = [('gkhood5_8', 'dataset')]
HISTOGRAM_LOCATION = './results/figures/%s-f%d-d%d-q%d-g%d-o%d/'
RESULT_LOCATION = './results/'

def single_level_dataset(kmin, kmax, level, dmax):
    print('operation SLD: generating single level dataset\n\
        arguments -> kmin=%d, kmax=%d, level=%d, distance=%d'%(kmin, kmax, level, dmax))

    last_time = currentTime()
    gkhood = GKmerhood(kmin, kmax)
    print('GKhood instance generated in %f seconds'%(currentTime() - last_time))

    last_time =  currentTime()
    gkhood.single_level_dataset(dmax, level)
    print(strftime("%H:%M:%S", gmtime(currentTime() - last_time)))


def motif_finding_chain(dataset_name, gkhood_index, frame_size, q, d, gap, overlap, h_report, s_mask):
    print('operation MFC: finding motif using chain algorithm (tree:%s)\n\
        arguments -> f=%d, q=%d, d=%d, gap=%d, overlap=%d'%(DATASET_TREES[gkhood_index][0], frame_size, q, d, gap, overlap))

    sequences = read_fasta('data/%s.fasta'%(dataset_name))

    if q == -1:
        q = len(sequences)

    assert q <= len(sequences)

    if s_mask != None:
        assert len(sequences) == len(s_mask)


    tree = GKHoodTree(DATASET_TREES[gkhood_index][0], DATASET_TREES[gkhood_index][1])
    motif_tree = find_motif_all_neighbours(tree, d, frame_size, sequences)
    motifs = motif_tree.extract_motifs(q, 0)
    print('number of motifs->', len(motifs))

    report = motif_chain(
        motifs, 
        sequences,
        q=q, 
        gap=gap,
        overlap=overlap, 
        sequence_mask=s_mask, 
        report=h_report, 
        report_directory=HISTOGRAM_LOCATION%(dataset_name, frame_size, d, q, gap, overlap))
    
    if report != None:
        print(report)

    make_location('%s%s'%(RESULT_LOCATION, dataset_name))
    motif_chain_report(motifs, '%s%s/f%d-d%d-q%d-g%d-o%d'%(RESULT_LOCATION, dataset_name, frame_size, d, q, gap, overlap), sequences)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise Exception('request command must be specified (read the description for supported commands)')

    shortopt = 'd:m:M:l:s:g:O:hq:f:G:'
    longopts = ['kmin=', 'kmax=', 'distance=', 'level=', 'sequences=', 'gap=', 
        'overlap=', 'histogram', 'mask=', 'quorum=', 'frame=', 'gkhood=']

    args_dict = {'kmin':5, 'kmax':8, 'level':6, 'dmax':1, 'sequences':'dm01r', 
        'gap':3, 'overlap':2, 'mask':None, 'quorum':-1, 'frame_size':6, 'gkhood_index':0}
    histogram_report = False

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
            histogram_report = True
        elif o in ['-q', '--quorum']:
            args_dict.update({'quorum':int(a)})
        elif o in ['-f', '--frame']:
            args_dict.update({'frame_size':int(a)})
        elif o in ['-G', '--gkhood']:
            args_dict.update({'gkhood_index':int(a)})

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
            histogram_report, 
            args_dict['mask'])
    else:
        print('[ERROR] command %s is not supported'%command)
