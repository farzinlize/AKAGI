from Nodmer import Nodmer

class GKmerhood:
    def __init__(self, k_min, k_max, alphabet='ATCG'):
        self.kmin = k_min
        self.kmax = k_max
        self.alphabet = alphabet
        self.generate_dict(alphabet)
        self.generate_nodes()
        self.edges = []


    def generate_dict(self, alphabet):
        self.dictionery = {}
        i = 0
        for letter in alphabet:
            self.dictionery.update({letter: i})
            i += 1
        

    def kmer2code(self, kmer):
        code = 0
        for i in range(len(kmer)):
            code += self.dictionery[kmer[i]] * (len(self.alphabet))**i
        return code


    def code2kmer(self, code):
        dividend = code
        kmer = ""
        while dividend >= len(self.alphabet):
            reminder = dividend % len(self.alphabet)
            dividend = dividend // len(self.alphabet)
            kmer += self.alphabet[reminder]
        kmer += self.alphabet[dividend]
        
        if len(kmer) < self.k:
            for _ in range(self.k-len(kmer)):
                kmer += self.alphabet[0]

        # assert code == self.kmer2code(kmer)
        return kmer


    def generate_nodes(self):
        self.nodes = []
        for code in range(len(self.alphabet)**self.k):
            self.nodes += [Nodmer(self, code, self.code2kmer(code))]

    
    def initial_neighbourhood(self):
        for _ in self.nodes:
            pass



def test_main():
    gk = GKmerhood(3)

    print("code:", 3, " | kmer:", gk.code2kmer(3))

    for node in gk.nodes:
        print(node)

# test_main()