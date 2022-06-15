from cmath import inf
from io import BytesIO
import sys, os
import matplotlib.pyplot as plt
from numpy import linspace
from FoundMap import MemoryMap
from GKmerhood import GKHoodTree
from TrieFind import ChainNode, initial_chainNodes, pop_chain_node
from checkpoint import load_checkpoint_file, load_collection, save_checkpoint
from constants import BANK_NAME, BANK_PATH, CHECKPOINT_TAG, DATASET_TREES, DNA_ALPHABET, INT_SIZE, MONGOD_SHUTDOWN_COMMAND, QUEUE_COLLECTION, SUMMIT
from mongo import get_bank_client, initial_akagi_database
from onSequence import OnSequenceDistribution
from misc import ExtraPosition, binary_to_list, bytes_to_int, pwm_score_sequence, read_fasta, read_bundle, brief_sequence, read_pfm_save_pwm
from pool import AKAGIPool, get_AKAGI_pools_configuration

def test_gkhood_dataset_k(gkhood_index, k):
    tree = GKHoodTree(DATASET_TREES[gkhood_index][0], DATASET_TREES[gkhood_index][1])
    errors = 0

    for kmer in generate_possible_kmers(k):
        try:
            tree.dneighbours(kmer, 0)
        except:
            print("[DOCTOR-ERROR] kmer (%s:%d) couldn't resolve in tree (%s)"%(kmer, len(kmer), DATASET_TREES[gkhood_index][0]))
            errors += 1

    print("[DOCTOR] number of errors: %d"%errors)


def generate_possible_kmers(k):
    
    def recursive_helper(prefix, k):
        if k==0:
            return [prefix]

        result = []
        for l in DNA_ALPHABET:
            newPrefix = prefix + l
            result += recursive_helper(newPrefix, k-1)

        return result

    return recursive_helper('', k)


# initial banks and generate onsequence raw file for cplus-workers
def manual_initial(bank_order, initial_works_address:str, dataset, onsequence_name):

    if initial_works_address.endswith(CHECKPOINT_TAG):initial_works = load_checkpoint_file(initial_works_address)
    else                                             :initial_works = load_collection(initial_works_address)
    if not isinstance(initial_works, list):print(f"[ERROR] error loading from collection: {initial_works}");return
    if not initial_works:print("[ERROR] nothing found for initializing banks")                             ;return

    # initial onsequence, briefing uses constants parameters
    sequences = read_fasta(dataset + '.fasta')
    bundles = read_bundle(dataset + '.bundle')
    sequences, bundles = brief_sequence(sequences, bundles)
    onsequence = OnSequenceDistribution(initial_works, sequences)
    onsequence.raw_file(onsequence_name)

    # allocate ports
    manual_ports = []
    for i in range(bank_order):
        new_bank_port = 3038 + 20 + i*10
        manual_ports.append(new_bank_port)
        try:initial_akagi_database(BANK_NAME%i, BANK_PATH%i, new_bank_port, serve=True)
        except Exception as e:print(f'[FATAL][ERROR] something went wrong {e}');return 

    # -> static job distribution between banks
    bank_initial_lists = [[] for _ in range(bank_order)]
    for index, motif in enumerate(initial_works):
        bank_initial_lists[index%bank_order].append(motif)

    # -> insert jobs into banks
    for index, port in enumerate(manual_ports):
        bank_client = get_bank_client(port)
        result = initial_chainNodes([(m.label, m.foundmap) for m in bank_initial_lists[index]], QUEUE_COLLECTION, bank_client)
        if not isinstance(result, list):print(f'[FATAL][ERROR] something went wrong {result}');return
        bank_client.close()

    # shutdown banks after work
    for index in range(len(manual_ports)):os.system(MONGOD_SHUTDOWN_COMMAND%(BANK_PATH%index))


def pwm_score_doc(sequences, pa, pr):
    aggregated = 0
    for seq in sequences:
        a, _ = pwm_score_sequence(seq, pa)
        r, _ = pwm_score_sequence(seq, pr)
        aggregated+=max(a, r)
    return aggregated / len(sequences)


def restore_dumped_motifs(dumped='dumped.motifs', back_bank=None):
    with open(dumped, 'rb') as dumpy:
        restored = []
        corrupted = False
        while True:
            read = dumpy.read(INT_SIZE)
            if not read:break
            label_len = bytes_to_int(read, endian='little')
            label = str(dumpy.read(label_len), 'utf8')
            if not label:corrupted = True;break
            read = dumpy.read(INT_SIZE)
            if not read:corrupted = True;break
            data_size = bytes_to_int(read, endian='little')
            bin_data = dumpy.read(data_size)
            if not bin_data:corrupted = True;break
            found_list = binary_to_list(BytesIO(bin_data))
            restored.append(ChainNode(label, MemoryMap(initial=found_list)))
    
    if not back_bank:return restored, corrupted
    return initial_chainNodes([(m.label, m.foundmap) for m in restored], QUEUE_COLLECTION, get_bank_client(back_bank)), corrupted


def all_into_bank_zero(zero_port, other_ports):
    zero = get_bank_client(zero_port)
    for port in other_ports:
        other = get_bank_client(port)

        # extract works
        stuff = []
        item = pop_chain_node(other)
        while item:
            if isinstance(item, ChainNode):stuff.append(item)
            else:break
            item = pop_chain_node(other)
        other.close()
        
        # move them into zero
        initial_chainNodes([(m.label, m.foundmap) for m in stuff], QUEUE_COLLECTION, zero)
    zero.close()


def clean_bank(bank_port, rest_file):
    bank = get_bank_client(bank_port)

    stuff = []
    item = pop_chain_node(bank)
    while item:
        if isinstance(item, ChainNode):stuff.append(item)
        else:break
        item = pop_chain_node(bank)
    bank.close()

    save_checkpoint(stuff, rest_file, compact=True)


def open_dataset(dataset, sequence_count, maximum_length):
    sequences = read_fasta(dataset + '.fasta')
    bundles = read_bundle(dataset + '.bundle')
    sequences, bundles = brief_sequence(sequences, bundles, max_seq=sequence_count, max_len=maximum_length)
    return sequences, bundles


def load_pool(address):
    pooly = AKAGIPool(get_AKAGI_pools_configuration())
    pooly.read_snap(address)
    return pooly


def centrality_plot(pattern:ChainNode, bundles, save=None):
    x_axis = linspace(-len(bundles), len(bundles), 2 * len(bundles)+1)
    hist = [0 for _ in range(-len(bundles), len(bundles)+1)]
    zero = len(bundles)
    bun = pattern.foundmap.remove_redundant().get_list()
    for index, seq_id in enumerate(bun[0]):
        position:ExtraPosition
        for position in bun[1][index]:
            end_index = position.end_position() # int(position) + len(pattern.label)
            start_index = position.start_position
            # if len(position.chain) != 0:
            #     start_index = position.chain[0]
            mid_index = (end_index + start_index)//2
            shifted_distance = (bundles[seq_id][SUMMIT] - mid_index) + zero
            if shifted_distance < 0 or shifted_distance >= len(hist):
                print("[DOCTOR][CENTRALITY] very far instaces")
                continue
            hist[shifted_distance] += 1
    plt.plot(x_axis, hist)
    plt.axvline(0, color='red')
    plt.xlabel('distance to summit')
    plt.ylabel('number of instances')
    if save:plt.savefig(save)
    else   :plt.show()
    plt.clf()


def one_instance_per_sequence_analysis(pattern:ChainNode, dataset, nseq, length, pwm):
    bundle = pattern.foundmap.get_list()
    s, b = open_dataset(dataset, nseq, length)
    pa, pr = read_pfm_save_pwm(pwm)

    total_j = 0             # total j scores
    total_distance = 0      # total distances
    total_distance_j = 0    # total j score of best distances
    total_j_distance = 0    # total distances of best j score
    j_positions = []
    distance_positions = []

    for index, seq_id in enumerate(bundle[0]):

        position: ExtraPosition
        best_j_position: ExtraPosition
        best_distance_position: ExtraPosition
        best_j = 0
        best_distance = inf

        for position in bundle[1][index]:

            # retrive data
            end_index = position.end_position() 
            start_index = position.start_position
            sequence = s[seq_id][start_index:end_index]
            score, _ = pwm_score_sequence(sequence, pa)
            r_score, _ = pwm_score_sequence(sequence, pr)
            mid_index = (end_index + start_index)//2

            # calculating score
            distance = abs(b[seq_id][SUMMIT] - mid_index)
            j = max(score, r_score)

            # choose the best
            if j > best_j:
                best_j = j
                best_j_position = position
                best_j_distance = distance

            if distance < best_distance:
                best_distance = distance
                best_distance_position = position
                best_distance_j = j
        
        # aggregated
        total_j += best_j
        total_distance += best_distance
        total_distance_j += best_distance_j
        total_j_distance += best_j_distance
        j_positions.append(best_j_position)
        distance_positions.append(best_distance_position)
    
    nseq = len(bundle[0])
    return {'j':total_j/nseq, 
            'j_summit':total_j_distance/nseq, 
            'summit':total_distance/nseq, 
            'summit_j':total_distance_j/nseq, 
            'j positions':j_positions, 
            'summit positions':distance_positions}

 
if __name__ == "__main__":
    print("manual initial procedure for chaining\nenter how many banks?")
    bank_order = int(input())
    print("enter checkpoint file location or mongo-collection for initial works:")
    initial_works_address = input()
    print("enter dataset address:")
    dataset = input()
    print("enter a name for onsequence file as result:")
    onseq_name = input()
    manual_initial(bank_order, initial_works_address, dataset, onseq_name)
    # test_gkhood_dataset_k(int(sys.argv[1]), int(sys.argv[2]))