from GKmerhood import GKmerhood

class Nodmer:
    def __init__(self, gkhood, code, kmer, assertaion_flag=False):
        if assertaion_flag:
            assert gkhood.kmer2code(kmer) == code
            assert gkhood.code2kmer(code) == kmer
        self.graph = gkhood
        self.code = code
        self.kmer = kmer

    
    def generate_neighbours(self):
        pass