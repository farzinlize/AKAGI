from TrieFind import TrieNode
from Nodmer import Nodmer

class GKmerhood:
    def __init__(self, k_min, k_max, alphabet='ATCG'):
        self.kmin = k_min
        self.kmax = k_max
        self.alphabet = alphabet
        self.generate_dict(alphabet)
        self.nodes = self.initial_trie_nodes()


    def generate_dict(self, alphabet):
        self.dictionery = {}
        i = 0
        for letter in alphabet:
            self.dictionery.update({letter: i})
            i += 1


    def initial_trie_nodes(self):
        self.trie = TrieNode()
        return self.trie.child_birth(self)

    
    def initial_neighbourhood(self):
        pass




def test_main():
    pass

# test_main()