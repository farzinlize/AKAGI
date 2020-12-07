from GKmerhood import GKmerhood
from misc import FileHandler, heap_decode

# repairing dataset
def repair():
    print("[REPAIR] generating GKmerHood (it will take a while)")
    gkhood = GKmerhood(5, 8)
    print("finished!")
    dmax = 4
    handler = FileHandler('repair', filename_prefix='R')
    real_first_code = (4**(gkhood.kmin) - 1)//3 + 1
    last_remaining_code = (4**(gkhood.kmin+1) - 1)//3
    with open('head_repair.tree', 'w+') as head_tree:
        for code in range(real_first_code, last_remaining_code+1):
            node = gkhood.trie.find(heap_decode(code, gkhood.alphabet))
            if node == None:
                print("ERROR: node couldn't be found, code -> " + code)
                continue
            dneighbourhood = node.dneighbours(dmax)
            file_index, position = handler.put(dneighbourhood)
            head_tree.write(str(file_index) + '\t' + str(position) + '\n')

    dataset_last_code = len(gkhood.nodes)
    real_last_code = (4**(gkhood.kmax+1) - 1)//3
    with open('tail_repair.tree', 'w+') as tail_tree:
        for code in range(dataset_last_code, real_last_code+1):
            node = gkhood.trie.find(heap_decode(code, gkhood.alphabet))
            if node == None:
                print("ERROR: node couldn't be found, code -> " + code)
                continue
            dneighbourhood = node.dneighbours(dmax)
            file_index, position = handler.put(dneighbourhood)
            tail_tree.write(str(file_index) + '\t' + str(position) + '\n')


# merge tree (tested)
def merge_tree():
    original_tree = open('gkhood5_8.tree', 'r')
    head = open('head_repair.tree', 'r')
    tail = open('tail_repair.tree', 'r')

    merged = open('gkhood5_8_REPAIRED.tree', 'w+')
    for line in head:
        merged.write('R'+line)
    for line in original_tree:
        merged.write(line)
    for line in tail:
        merged.write('R'+line)

    original_tree.close()
    head.close()
    tail.close()
    merged.close()


def test_main():
    print("[TEST] generating GKmerHood (it will take a while)")
    gkhood = GKmerhood(5, 8)
    print("finished!")

    real_first_code = (4**(gkhood.kmin) - 1)//3 + 1
    last_remaining_code = (4**(gkhood.kmin+1) - 1)//3

    dataset_last_code = len(gkhood.nodes)
    real_last_code = (4**(gkhood.kmax+1) - 1)//3

    print('head tree')
    print('start with -> real_first_code = ', real_first_code, ' (kmer = ', heap_decode(real_first_code, gkhood.alphabet), ')')
    print('end with -> last_remaining_code = ', last_remaining_code, '(kmer = ', heap_decode(last_remaining_code, gkhood.alphabet), ')')

    print('tail tree')
    print('start with -> dataset_last_code = ', dataset_last_code, ' (kmer = ', heap_decode(dataset_last_code, gkhood.alphabet), ')')
    print('end with -> real_last_code = ', real_last_code, '(kmer = ', heap_decode(real_last_code, gkhood.alphabet), ')')


# ########################################## #
#           main function call               #
# ########################################## #

# main function call
if __name__ == "__main__":
    repair()