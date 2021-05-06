# pyright: reportUnboundVariable=false
# ignoring false unbound reports

from io import BufferedWriter
from typing import List
from constants import AKAGI_PREDICTION_EXPERIMENTAL, AKAGI_PREDICTION_STATISTICAL, CHAINING_FOUNDMAP_MODE, CHAINING_REPORT_EACH, CHAINING_REPORT_PEND, CR_HEADER, CR_TABLE_HEADER_SSMART, CR_TABLE_HEADER_SUMMIT, EXTRACT_OBJ, FOUNDMAP_MEMO, PIXELS_ANALYSIS, QUEUE_DISK, QUEUE_MEMO, QUEUE_MODE
from pool import RankingPool, distance_to_summit_score, objective_function_pvalue
from TrieFind import ChainNode, WatchNode, WatchNodeC
from GKmerhood import GKmerhood, GKHoodTree
from misc import QueueDisk, clear_screen, heap_encode, alphabet_to_dictionary, lap_time, read_bundle, read_fasta, Queue, make_location, ExtraPosition
from onSequence import OnSequenceDistribution
from time import gmtime, strftime, time as currentTime
from report import location_histogram, motif_chain_report, report_print
import sys

'''
    motif finding function -> first version of motif-finding algorithm using gkhood
        an empty trie tree will save all seen kmers in sequence
        all frames of any sequences and its d-neighbours will be considered as seen kmers
        the trie will return motifs (kmers that are present in all sequences)

    [WARNING] function requires strings for d-neighbours kmer, but GKhoodTree class may provide Nodmers

    *************************** UPDATE *************************************
        function will return the whole motif tree for further processing
'''
# previous function definition :
# def find_motif_all_neighbours(gkhood_tree, dmax, frame_size, sequences, result_kmer=1, q=-1):

def find_motif_all_neighbours(gkhood_tree, dmax, frame_size, sequences):

    # define threshold to report progress
    PROGRESS_THRESHOLD = 100

    motifs_tree = WatchNode()
    for seq_id in range(len(sequences)):

        # progress value
        DSE_sum = 0
        A2T_sum = 0
        # progress_time = currentTime()
        progress = 0
        # print('processing sequence: ', seq_id)

        frame_start = 0
        frame_end = frame_size
        while frame_end < len(sequences[seq_id]):

            frame = sequences[seq_id][frame_start:frame_end]

            # dneighbours extraction
            now = currentTime()
            dneighbours = gkhood_tree.dneighbours(frame, dmax)
            dataset_extraction_time = currentTime() - now

            # adding motifs to tree
            now = currentTime()
            motifs_tree.add_frame(frame, seq_id, ExtraPosition(frame_start, len(frame)))
            for each in dneighbours:
                motifs_tree.add_frame(each[0], seq_id, ExtraPosition(frame_start, len(each[0])))
            add_to_tree_time = currentTime() - now

            frame_start += 1
            frame_end += 1

            # average time calculation
            DSE_sum += dataset_extraction_time
            A2T_sum += add_to_tree_time

            progress += 1
            if progress == PROGRESS_THRESHOLD:
                # print('progress checkout: ', currentTime() - progress_time, 'seconds')
                # print('> DSE average: ', DSE_sum/progress, '\tA2T average: ', A2T_sum/progress)
                DSE_sum = 0
                A2T_sum = 0
                progress = 0
                # progress_time = currentTime()

    # previous version return value
    # return motifs_tree.extract_motifs(q, result_kmer)

    return motifs_tree


def multiple_layer_window_find_motif(gkhood_trees, ldmax, lframe_size, sequences):
    motifs_tree = WatchNode()
    
    for seq_id in range(len(sequences)):
        lframe_start = [0 for _ in range(len(ldmax))]
        lframe_end = [frame_size for frame_size in lframe_size if frame_size <= len(sequences[seq_id])]

        while lframe_end:

            for frame, index in [(sequences[seq_id][lframe_start[i]:lframe_end[i]], i) for i in range(len(lframe_end))]:
                try:
                    dneighbours = gkhood_trees[index].dneighbours(frame, ldmax[index])
                except:
                    print('[findmotif] dneighbours extraction failed')
                    print('[+info] index=%d frame=%s dmax=%d'%(index, frame, ldmax[index]))
                    raise Exception('HALT')

                motifs_tree.add_frame(frame, seq_id, ExtraPosition(lframe_start[index], len(frame)))
                for each in dneighbours:
                    motifs_tree.add_frame(each[0], seq_id, ExtraPosition(lframe_start[index], len(each[0])))
            
            for i in range(len(lframe_start)):
                lframe_start[i] += 1
                lframe_end[i] += 1

            for end_index in range(len(lframe_end)):
                if lframe_end[end_index] >= len(sequences[seq_id]):
                    lframe_end = lframe_end[:end_index] + lframe_end[end_index+1:]
                    lframe_start = lframe_start[:end_index] + lframe_start[end_index+1:]
    
    return motifs_tree


# ########################################## #
#          chaining motifs section           #
# ########################################## #

def motif_chain(zmotifs: List[WatchNode], sequences, bundles, q=-1, gap=0, overlap=0):

    # starting chaining report window
    clear_screen()
    DWE = '' # Details/Warnings/Errors
    print(CR_HEADER%DWE)


    # set default value of q
    if q == -1:
        q = len(sequences)

    on_sequence = OnSequenceDistribution(zmotifs, sequences)
    if PIXELS_ANALYSIS:
        DWE += on_sequence.analysis()
        clear_screen()
        print(CR_HEADER%DWE)


    if QUEUE_MODE == QUEUE_DISK:
        queue = QueueDisk(ChainNode, items=[ChainNode(motif.label, motif.foundmap) for motif in zmotifs])
    elif QUEUE_MODE == QUEUE_MEMO:
        # queue = Queue(items=[motif.make_chain() for motif in zmotifs])
        raise NotImplementedError

    pool_ssmart = RankingPool(bundles, objective_function_pvalue)
    pool_summit = RankingPool(bundles, distance_to_summit_score)

    ### FOR REPORT ONLY ###
    queue_size = len(zmotifs)
    last_time = currentTime()
    for_print = ''
    number_of_line = 0
    ### ############### ###
        

    while not queue.isEmpty():
        link: ChainNode = queue.pop()

        ### FOR REPORT ONLY ###
        queue_time, last_time = lap_time(last_time)
        
        bundle = link.foundmap.get_list()

        ### FOR REPORT ONLY ###
        foundmap_time, last_time = lap_time(last_time)

        next_tree = WatchNode()
        
        for index, seq_id in enumerate(bundle[0]):
            position: ExtraPosition
            for position in bundle[1][index]:
                for sliding in [i for i in range(-overlap, gap+1)]:
                    next_position = position.end_position() + sliding
                    if next_position >= len(sequences[seq_id]):
                        continue

                    for next_condidate in on_sequence.struct[seq_id][next_position]:
                        next_tree.add_frame(
                            next_condidate, 
                            seq_id, 
                            ExtraPosition(position.start_position, len(next_condidate) + sliding))
        
        ### FOR REPORT ONLY ###
        observation_time, last_time = lap_time(last_time)

        next_motif: WatchNode
        for next_motif in next_tree.extract_motifs(q, EXTRACT_OBJ):
            queue.insert(ChainNode(
                link.label + next_motif.label, 
                next_motif.foundmap.clone()))
        
        ### FOR REPORT ONLY ###
        next_generation_time, last_time = lap_time(last_time)
            
        pool_ssmart.add(link)
        pool_summit.add(link)

        clear_screen()
        print(CR_HEADER%DWE)
        print(CR_TABLE_HEADER_SSMART, pool_ssmart.top_ten_table())
        print(CR_TABLE_HEADER_SUMMIT, pool_summit.top_ten_table())

        ### FOR REPORT ONLY ###
        pool_time, last_time = lap_time(last_time)

        next_tree.clear()

        ### FOR REPORT ONLY ###
        clear_tree_time, last_time = lap_time(last_time)
        for_print, number_of_line = report_print(for_print, number_of_line, 
            '[CHAINING][REPORT] chain-done %s | queue %s (size=%d) | foundmap %s | add2tree %s | next-gen %s | pool %s | clear %s\n'%(
            strftime("%H:%M:%S", gmtime(queue_time + foundmap_time + observation_time + next_generation_time + pool_time + clear_tree_time)),
            strftime("%H:%M:%S", gmtime(queue_time)),
            queue_size,
            strftime("%H:%M:%S", gmtime(foundmap_time)),
            strftime("%H:%M:%S", gmtime(observation_time)),
            strftime("%H:%M:%S", gmtime(next_generation_time)),
            strftime("%H:%M:%S", gmtime(pool_time)),
            strftime("%H:%M:%S", gmtime(clear_tree_time))
        ))
        last_time = currentTime()
        ### ############### ###        

    pool_ssmart.all_ranks_report(AKAGI_PREDICTION_STATISTICAL, sequences)
    pool_summit.all_ranks_report(AKAGI_PREDICTION_EXPERIMENTAL, sequences)



'''
    finding next motifs to be chained on a single motif
    results are list of motifs represendting next generations

    [WARNING] procedure uses in memory dataset to store foundmaps
        motifs should convert their foundmap to disk mode for furthur use 
'''
def next_chain(motif, on_sequence, overlap, gap, q, report:BufferedWriter, chain_id):
    observation_size = 0
    bundle = motif.foundmap.get_list()
    next_tree = WatchNodeC(custom_foundmap_type=CHAINING_FOUNDMAP_MODE)
    for index, seq_id in enumerate(bundle[0]):
        position: ExtraPosition
        for position in bundle[1][index]:
            observation_size += 1
            for sliding in [i for i in range(-overlap, gap+1)]:
                next_position = position.end_position() + sliding
                if next_position >= len(on_sequence.struct[seq_id]):continue

                for next_condidate in on_sequence.struct[seq_id][next_position]:
                    
                    # ignoring candidates which doesn't extend the motif length
                    if next_position + len(next_condidate) <= position.end_position():continue

                    next_tree.add_frame(
                        next_condidate, 
                        seq_id, 
                        ExtraPosition(position.start_position, position.size + len(next_condidate) + sliding))
    
    report.write('OBSERVATION SIZE %d | CHAIN_ID %d | '%(observation_size, chain_id))

    return next_tree.extract_motifs_and_delete_childs(q, EXTRACT_OBJ)


# ########################################## #
#              other functions               #
# ########################################## #

'''
    extract which files in dataset are needed for a given set of sequences
'''
def sequence_dataset_files(filename, sequences, frame_size):
    tree = GKHoodTree('gkhood5_8', 'dataset')

    required_files_mask = [0 for i in range(tree.metadata['files'])]

    for sequence in sequences:
        frame_start = 0
        frame_end = frame_size
        while frame_end <= len(sequence):
            frame = sequence[frame_start:frame_end]
            file_index = int(tree.get_position(frame)[0])
            required_files_mask[file_index] += 1
            frame_start += 1
            frame_end += 1

    return [index for index in range(tree.metadata['files']) if required_files_mask[index] != 0]


# ########################################## #
#           main function section            #
# ########################################## #

def main_chain():
    # inputs
    s_mask = None

    if len(sys.argv) < 4:
        print('[ERROR] lack of argument found. use command template below to run this script')
        print('python findmotif.py [dataset_name] [distance] [overlap] [mask->optional]')
        return
    elif len(sys.argv) == 5:
        s_mask = sys.argv[4]
    elif len(sys.argv) > 5:
        print('[ERROR] too much argument found. use command template below to run this script')
        print('python findmotif.py [dataset_name] [distance] [overlap] [mask->optional]')
        return


    dataset_name = sys.argv[1]
    d = int(sys.argv[2]) ; overlap = int(sys.argv[3])

    print('[START] motif finding using gkhood is runing for %s dataset with d=%d and overlap=%d'%(dataset_name, d, overlap))

    sequences = read_fasta('data/Real/%s.fasta'%(dataset_name))

    if s_mask != None:
        assert len(sequences) == len(s_mask)

    tree = GKHoodTree('gkhood5_8', 'dataset')
    motif_tree = find_motif_all_neighbours(tree, d, 6, sequences)
    motifs = motif_tree.extract_motifs(len(sequences), 0)
    print('number of motifs->', len(motifs))

    report = motif_chain(motifs, sequences, overlap=overlap, sequence_mask=s_mask, report=True, report_directory='.\\results\\figures\\%s-masked\\'%(dataset_name))
    print(report)
    # motif_chain(motifs, sequences, overlap=overlap, report=False)

    make_location('.\\results\\%s'%dataset_name)
    motif_chain_report(motifs, '.\\results\\%s\\%s-6-%d-%d'%(dataset_name, dataset_name, d, overlap))


# real main function for finding motifs using a generated dataset
def main_find_motif():
    sequences = read_fasta('data/Real/dm01r.fasta')
    tree = GKHoodTree('gkhood5_8', 'dataset')
    motifs = find_motif_all_neighbours(tree, 2, 6, sequences).extract_motifs(len(sequences))
    print('number of motifs->', len(motifs))
    for motif in motifs:
        print(motif)


def main_required_files():
    sequences = read_fasta('data/Real/hm24r.fasta')
    req_files = sequence_dataset_files('dm01r.req', sequences, 7)
    print(len(req_files))
    print(req_files)


def test_main_2():
    tree = GKHoodTree('gkhood5_8', 'dataset')

    sample = 'GGGGGG'
    dn = tree.dneighbours(sample, 4)
    line = heap_encode(sample, tree.dictionary) - tree.metadata['bias']

    print('sample -> ', sample, ' line -> ', line)
    print(len(dn))
    for each in dn:
        if each[1] > 1:
            break
        print(each)

    print('##############################')

    sample_2 = 'AGCGCA'
    dn_2 = tree.dneighbours(sample_2, 1)
    line_2 = heap_encode(sample_2, tree.dictionary) - tree.metadata['bias']

    print('sample -> ', sample_2, ' line ->', line_2)
    print(len(dn_2))
    for each in dn_2:
        print(each)


# testing read_fasta
def test_main():
    sequences = sequences = read_fasta('data/Real/dm01r.fasta')
    print(sequences)


# ########################################## #
#           main function call               #
# ########################################## #

# main function call
if __name__ == "__main__":
    main_chain()