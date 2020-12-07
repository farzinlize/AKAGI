import sys

from GKmerhood import GKHoodTree

from constants import DATASET_TREES, DNA_ALPHABET

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


if __name__ == "__main__":
    test_gkhood_dataset_k(int(sys.argv[1]), int(sys.argv[2]))