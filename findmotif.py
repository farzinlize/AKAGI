from TrieFind import TrieNode
from GKmerhood import GKmerhood, GKHoodTree
from misc import heap_encode, alphabet_to_dictionary, read_fasta, Queue, make_location
from time import time as currentTime
from report import location_histogram, motif_chain_report

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

    motifs_tree = TrieNode()
    for seq_id in range(len(sequences)):

        # progress value
        DSE_sum = 0
        A2T_sum = 0
        progress_time = currentTime()
        progress = 0
        print('processing sequence: ', seq_id)

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
            motifs_tree.add_frame(frame, seq_id, frame_start)
            for each in dneighbours:
                motifs_tree.add_frame(each[0], seq_id, frame_start)
            add_to_tree_time = currentTime() - now

            frame_start += 1
            frame_end += 1

            # average time calculation
            DSE_sum += dataset_extraction_time
            A2T_sum += add_to_tree_time

            progress += 1
            if progress == PROGRESS_THRESHOLD:
                print('progress checkout: ', currentTime() - progress_time, 'seconds')
                print('> DSE average: ', DSE_sum/progress, '\tA2T average: ', A2T_sum/progress)
                DSE_sum = 0
                A2T_sum = 0
                progress = 0
                progress_time = currentTime()

    # previous version return value
    # return motifs_tree.extract_motifs(q, result_kmer)

    return motifs_tree


# ########################################## #
#          chaining motifs section           #
# ########################################## #

'''
    generate a 3-dimentional list to access motifs that occures at a specific location
        dimentions are described below:
            1. sequence_id -> there is a list for any sequence
            2. position -> there is a list of motifs for any position on a specific sequence
            3. motif -> refrence for motifs that occures at a pecific location (position) and a specific sequence
'''
def on_sequence_found_structure(motifs, sequences):

    struct = [[[] for _ in range(len(sequence))] for sequence in sequences]

    for motif in motifs:
        for seq_id in motif.found_list[0]:
            for position in motif.found_list[1][seq_id]:
                struct[seq_id][position] += [motif]

    return struct


def motif_chain(motifs, sequences, q=-1, overlap=0, sequence_mask=None, report=False, report_directory=''):

    if report and sequence_mask == None:
        sequence_mask = [1 for _ in range(len(sequences))]

    # set defualt value of q
    if q == -1:
        q = len(sequences)

    on_sequence = on_sequence_found_structure(motifs, sequences)
    queue = Queue(items=[motif.make_chain() for motif in motifs])

    if report:
        # reporting variables
        current_level = 0
        level_count = [0]
        current_level_list = []
        make_location(report_directory)

    while not queue.isEmpty():
        link = queue.pop()
        next_tree = TrieNode()

        if report:
            # updating report variables
            if current_level == link.chain_level:
                level_count[current_level] += 1
                current_level_list += [link]
            elif link.chain_level > current_level:
                # plot each chain level locations
                location_histogram(current_level_list, sequences, sequence_mask, savefilename=report_directory+'%d-chain-%d.png'%((current_level+1), level_count[current_level]))

                level_count += [0 for _ in range(link.chain_level-current_level)]
                current_level = link.chain_level
                current_level_list = []
            else:
                raise Exception('queue error: a node with lower chain level found in queue')

        for seq_id in link.end_chain_positions[0]:
            for end_position in link.end_chain_positions[1][seq_id]:
                for distance in [i for i in range(-overlap, overlap+1)]:
                    next_position = end_position + link.level + distance # link.level == len(link.label) == kmer-length
                    if next_position >= len(sequences[seq_id]):
                        continue
                    for next_condidate in on_sequence[seq_id][next_position]:
                        next_tree.add_frame(next_condidate.label, seq_id, next_position)
        for next_motif in next_tree.extract_motifs(q, 0):
            link.add_chain(next_motif.make_chain(chain_level=link.chain_level+1, up_chain=link))
            queue.insert(next_motif)
        link.chained_done()

    if report:
        # plot last chain level locations
        location_histogram(current_level_list, sequences, sequence_mask, savefilename=report_directory+'%d-chain-%d.png'%(current_level, level_count[current_level]))

        # return reporting variable
        return level_count


def chains_sort(chains):
    pass


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
#           main fucntion section            #
# ########################################## #

def main_chain():
    # inputs
    dataset_name = 'mus11r'
    d = 1 ; overlap = 3
    s_mask = '010010000000'

    sequences = read_fasta('data/Real/%s.fasta'%(dataset_name))
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
#           main fucntion call               #
# ########################################## #

# main function call
if __name__ == "__main__":
    main_chain()