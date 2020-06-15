import os, platform

# ########################################## #
#                 class part                 #
# ########################################## #

'''
    Queue structure implementation (FIFO)
        First in (insert), first out (pop)
'''
class Queue:
    def __init__(self, items=[]):
        self.queue = items


    def pop(self):
        item = self.queue[-1]
        self.queue = self.queue[:-1]
        return item


    def insert(self, item):
        self.queue = [item] + self.queue

    
    def isEmpty(self):
        return len(self.queue) == 0


'''
    File handler object -> accumulate data packages in seprated file with size limit
        at each line two value (neighbout-kmer and its distance) will be saved
        after inserting all d-neighbours lines, if line count exceededs the limit, 
        next set will be saved in another file
'''
class FileHandler:
    def __init__(self, directory_name=None, max_size=1000000, filename_prefix=''):

        self.prefix = filename_prefix

        # file address spliter is different in windows and linux
        operating_system = platform.system()
        if operating_system == 'Windows':
            spliter = '\\'
        else:   # operating_system == 'Linux'
            spliter = '/'

        if directory_name == None:
            self.directory = os.getcwd() + spliter + 'dataset' + spliter
        else:
            self.directory = os.getcwd() + spliter + directory_name + spliter

        try:
            os.mkdir(self.directory, 0o755)
        except:
            print('[WARNING] directory already excist')

        self.current_file = open(self.directory + self.prefix + '0.data', 'w')
        self.file_index = 0
        self.position = 0
        self.max_size = max_size


    '''
        initiate next file by reseting position value and opening new file
    '''
    def next_file(self):
        self.current_file.close()
        self.file_index += 1
        self.position = 0
        self.current_file = open(self.directory + self.prefix + str(self.file_index)+'.data', 'w')


    def put(self, dneighbours):
        data_index, position = self.file_index, self.position
        for each in dneighbours:
            self.current_file.write(each[0].kmer + '\t' + str(each[1]) + '\n')
            self.position += 1

        # progressing commend
        print('size ->', self.position - position)

        if self.position >= self.max_size:
            self.next_file()
        return data_index, position


    def close(self):
        self.current_file.close()
        return self.file_index+1


    def reopen(self):
        self.current_file = open(self.directory + self.prefix + str(self.file_index)+'.data', 'a')


# ########################################## #
#                 functions                  #
# ########################################## #


'''
    calculate edit-distance between two kmer
        [WARNING] take a lot of time due to calling 4 recursive at each level
'''
def edistance(kmer, lmer):
    if len(kmer) == 0:
        return len(lmer)
    if len(lmer) == 0:
        return len(kmer)
    if kmer[0] == lmer[0]:
        return edistance(kmer[1:], lmer[1:])
    return min(edistance(kmer[1:], lmer)+1, edistance(kmer, lmer[1:])+1, edistance(kmer[1:], lmer[1:])+1)


def alphabet_to_dictionary(alphabet):
    dictionary = {}
    for i in range(len(alphabet)):
        dictionary.update({alphabet[i]:i})
    return dictionary


# extract sequences from a fasta file
def read_fasta(filename):
    sequences = []
    fasta = open(filename, 'r')
    for line in fasta:
        if line[0] == '>':
            continue
        sequences += [line[:-1]]
    return sequences


# ########################################## #
#            heap array encoding             #
# ########################################## #

'''
    heap array encoding functions -> assign an index of an array to all kmers
        for each node in a trie as a complete tree (heap), it will line up each trie node
        heap_encode uses dictionary to measure letter indexes but heap_decode uses an alphabet

    [WARNING] it only works for DNA alphabet (or any 4 letter alphabet)
'''
def heap_encode(kmer, dictionary):
    code = 1
    for letter in kmer:
        code = code * 4 - (dictionary[letter] - 1)
    return code


def heap_decode(code, alphabet):
    kmer = ''
    while code>=2:
        kmer = alphabet[-((code+2)%4+1)] + kmer
        code = (code+2) // 4 # parent
    return kmer


# ########################################## #
#           main fucntion section            #
# ########################################## #

# testing edistance function
def test_main():
    kmer = 'GTCGCAGTCGCTGCC'
    lmer = 'CGCTGCCACCGCTG'
    pmer = 'CAGCGGCTGCGGA'

    print(edistance(pmer, lmer))
    print(edistance(pmer, kmer))


# testing heap array encoding
def test_main_3():
    d = {'A':0, 'C':1, 'T':2, 'G':3}
    alphabet = 'ACTG'
    user_kmer = input()
    while user_kmer:
        code = heap_encode(user_kmer, d)
        print('code: ', code, 'decode-> ', heap_decode(code, alphabet))
        user_kmer = input()

    kmer_1 = 'A'
    print(kmer_1, heap_decode(heap_encode(kmer_1, d), alphabet))
    kmer_2 = 'AT'
    print(kmer_2, heap_encode(kmer_2, d))
    kmer_3 = 'AA'
    print(kmer_3, heap_encode(kmer_3, d))
    kmer_4 = 'AAAAAAAA'
    print(kmer_4, heap_encode(kmer_4, d))


# testing
def test_main_2():
    f = open("test.data", 'w+')
    f.write('>5\t2\n>6\t2\n\n\n\n\n>7\t4\n')

    f.seek(0)

    f.readline()
    f.readline()
    f.readline()

    f.write('lol')

    f.close()


# testing how directory works in windows 
def test_main_4():
    o = os.getcwd()
    directory = '\\dataset\\'
    os.mkdir(o+directory, 0o755)
    f = open(o+directory + '0.data', 'w')
    f.write("hello")


def f(lst):
    for n in lst:
        n.label = 'ch'
    return lst


def workbench_tests():
    from TrieFind import TrieNode
    nodeA = TrieNode(lable='abc', level=7)
    nodeB = TrieNode(lable='zxc', level=10)
    lst = [nodeA, nodeB]
    print(lst[0].label)
    f(lst)
    print(lst[0].label)


# ########################################## #
#           main fucntion call               #
# ########################################## #

# main function call
if __name__ == "__main__":
    workbench_tests()