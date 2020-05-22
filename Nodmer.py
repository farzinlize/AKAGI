# from GKmerhood import GKmerhood
from misc import Queue

'''
    Kmer-node object -> a node containing a specific kmer
        nodes are connected if their kmers are at one edit-distance apart
'''
class Nodmer:
    def __init__(self, gkhood, kmer):
        self.graph = gkhood
        self.kmer = kmer
        self.neighbours = []

    
    # [WARNING] inefficient function
    def is_neighbour(self, other):
        for neighbour in self.neighbours:
            if other.kmer == neighbour.kmer:
                return True
        return False


    '''
        adding neighbours using binery search-add algorithm
            neighbours list is sorted and each new neighbour will be added at right place
    '''
    def add_neighbour(self, other):

        # binery search on sorted neighbourhood list
        start = 0
        end = len(self.neighbours)-1
        while start <= end:
            decision_is_made = False
            mid = (end + start)//2
            neighbour = self.neighbours[mid]
            for i in range(min(len(neighbour.kmer), len(other.kmer))):
                if neighbour.kmer[i] < other.kmer[i]:
                    start = mid + 1
                    decision_is_made = True
                    break
                elif neighbour.kmer[i] > other.kmer[i]:
                    end = mid - 1
                    decision_is_made = True
                    break

            # if one of the kmers was a suffix of another one, the kmer with longer string will be puted first
            if not decision_is_made:
                if len(neighbour.kmer) == len(other.kmer):
                    return # found - already a neighbour
                elif len(neighbour.kmer) < len(other.kmer):
                    start = mid + 1
                elif len(neighbour.kmer) > len(other.kmer):
                    end = mid - 1

        # wasn't already a neighbour (add)
        self.neighbours = self.neighbours[:start] + [other] + self.neighbours[start:]
        other.add_neighbour(self)


    # inefficient neighbour managment (no order - linear search needed)
    def add_neighbour_inefficient(self, other):
        self.neighbours += [other]
        other.neighbours += [self]
    

    '''
        a function to generate kmers with one edit-distance apart of object's kmer
            [WARNING] this function may return redundant kmers but guarantees to cover all possible neighbours
    '''
    def generate_neighbours(self):
        result = []
        for i in range(len(self.kmer)):
            # delete
            result += [self.kmer[:i] + self.kmer[i+1:]]

            for letter in self.graph.alphabet:
                # insert
                result += [self.kmer[:i] + letter + self.kmer[i:]]

                # mutation
                if letter != self.kmer[i]:
                    result += [self.kmer[:i] + letter + self.kmer[i+1:]]

        # last insertions
        return result + [self.kmer + letter for letter in self.graph.alphabet]


    '''
        BFS algorithm with maximum depth of dmax
            extracting neighbours that are at most dmax distance with this node (self)
            result is a list of tuples with a format described here: (kmer, distance)

        note: algorithm assumes any node without level attribute an unseen node and will erase level attribute for next call
    '''
    def dneighbours(self, dmax):
        queue = Queue([self])
        dneighbours = []
        self.level = 0
        while not queue.isEmpty():
            current = queue.pop()
            if current.level == dmax:
                continue
            for child in current.neighbours:
                if hasattr(child, 'level'):
                    continue
                child.level = current.level + 1
                queue.insert(child)
                dneighbours += [(child, child.level)]
        for each in dneighbours:
            delattr(each[0], 'level')
        delattr(self, 'level')
        return dneighbours