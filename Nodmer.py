from GKmerhood import GKmerhood

class Nodmer:
    def __init__(self, gkhood, kmer):
        self.graph = gkhood
        self.kmer = kmer
        self.neighbours = []

    
    def generate_neighbours(self):
        result = []
        for i in range(len(self.kmer)):
            #delete
            result += [self.kmer[:i] + self.kmer[i+1:]]
            
            for letter in self.graph.alphabet:
                #insert
                result += [self.kmer[:i] + letter + self.kmer[i:]]
                #sub
                if letter != self.kmer[i]:
                    result += [self.kmer[:i] + letter + self.kmer[i+1:]]
        
        #last insertions
        return result + [self.kmer + letter for letter in self.graph.alphabet]
