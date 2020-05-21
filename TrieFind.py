from Nodmer import Nodmer

class TrieNode:
    def __init__(self, lable='', level=0):
        self.label = lable
        self.childs = []
        self.level = level
        self.hasNode = False


    def is_root(self):
        return self.level == 0


    def get_node(self):
        if not self.hasNode:
            raise Exception("this trie has no node")
        return self.node


    def create_node(self, gkhood):
        self.node = Nodmer(gkhood, self.label)
        self.hasNode = True
        return self.node


    def child_birth(self, gkhood):
        if self.level == gkhood.kmax:
            return [self.create_node(gkhood)]
        self.childs = [TrieNode(self.label + letter, self.level+1) for letter in gkhood.alphabet]
        grandchildsNodmers = []
        for child in self.childs:
            grandchildsNodmers += child.child_birth(gkhood)
        if self.level >= gkhood.kmin:
            grandchildsNodmers += [self.create_node(gkhood)]
        return grandchildsNodmers


    def find(self, kmer):
        if len(kmer) == 0:
            return self.get_node()
        if len(self.childs) == 0:
            return None
        for child in self.childs:
            if child.label[-1] == kmer[0]:
                return child.find(kmer[1:])


    def add_frame(self, kmer, seq_id):
        if len(kmer) == 0:
            if not hasattr(self, 'found_list'):
                self.found_list = []
            self.found_list = binery_add(self.found_list, seq_id)
            return
        for child in self.childs:
            if child.label[-1] == kmer[0]:
                return child.add_frame(kmer[1:], seq_id)
        # proper child dose not exist
        new_child = TrieNode(self.label + kmer[0], self.level+1)
        self.childs += [new_child]
        return new_child.add_frame(kmer[1:], seq_id)

    
    def extract_motif(self, q):
        motifs = []
        if hasattr(self, 'found_list'):
            if len(self.found_list) >= q:
                motifs += [self.label]
        for child in self.childs:
            motifs += child.extract_motif(q)
        return motifs
        
        


def binery_add(lst, item):
    start = 0
    end = len(lst)-1
    while start <= end:
        mid = (start+end)//2
        if lst[mid] == item:
            return lst
        elif lst[mid] < item:
            start = mid + 1
        else:
            end = mid - 1
    return lst[:start] + [item] + lst[start:]


def test_main():
    lst = []
    lst = binery_add(lst, 5)
    lst = binery_add(lst, 8)
    lst = binery_add(lst, 2)
    lst = binery_add(lst, 3)
    lst = binery_add(lst, 10)
    lst = binery_add(lst, 3)
    print(lst)

# test_main()