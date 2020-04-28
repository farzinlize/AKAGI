from Nodmer import Nodmer

class TrieNode:
    def __init__(self, lable='', level=0):
        self.label = lable
        self.childs = []
        self.level = level


    def is_root(self):
        return self.level == 0


    def child_birth(self, gkhood):
        if self.level == gkhood.kmax:
            return [Nodmer(gkhood, self.label)]
        self.childs = [TrieNode(self.label + letter, self.level+1) for letter in gkhood.alphabet]
        grandchildsNodmers = []
        for child in self.childs:
            grandchildsNodmers += child.child_birth(gkhood)
        if self.level >= gkhood.kmin:
            grandchildsNodmers += [Nodmer(gkhood, self.label)]
        return grandchildsNodmers


