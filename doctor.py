from io import BytesIO
import sys, os
from FoundMap import MemoryMap
from GKmerhood import GKHoodTree
from TrieFind import ChainNode, initial_chainNodes
from checkpoint import load_checkpoint_file, load_collection
from constants import BANK_NAME, BANK_PATH, CHECKPOINT_TAG, DATASET_TREES, DNA_ALPHABET, INT_SIZE, MONGOD_SHUTDOWN_COMMAND, QUEUE_COLLECTION
from mongo import get_bank_client, initial_akagi_database
from onSequence import OnSequenceDistribution
from misc import binary_to_list, bytes_to_int, pwm_score_sequence, read_fasta, read_bundle, brief_sequence

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