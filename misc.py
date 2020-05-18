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


class FileHandler:
    def __init__(self, gkhood, directory=None, max_size=1000000):
        if directory == None:
            self.directory = 'find_file/'
        else:
            self.directory = directory+'/'
        self.heaparray = [None for i in range()]
        self.current_file = open('0.data', 'w')
        self.file_index = 0
        self.position = 0
        self.max_size = max_size


    def next_file(self):
        self.current_file.close()
        self.file_index += 1
        self.current_file = open(str(self.file_index)+'.data', 'w')


    def put(self, dneighbours):
        data_index, position = self.file_index, self.position
        for each in dneighbours:
            self.current_file.write(each[0].kmer + '\t' + str(each[1]) + '\n')
            self.position += 1
        if self.position >= self.max_size:
            self.next_file()
        return data_index, position


    def close(self):
        self.current_file.close()
        self.findfile.close()


    def reopen(self):
        self.current_file = open(str(self.file_index)+'.data', 'a')
        self.findfile = open(self.find_filename, 'a+')


    def goto(self, line):
        self.findfile.seek(0)
        for i in range(line):
            self.findfile.readline()


def edistance(kmer, lmer):
    if len(kmer) == 0:
        return len(lmer)
    if len(lmer) == 0:
        return len(kmer)
    if kmer[0] == lmer[0]:
        return edistance(kmer[1:], lmer[1:])
    return min(edistance(kmer[1:], lmer)+1, edistance(kmer, lmer[1:])+1, edistance(kmer[1:], lmer[1:])+1)

######################################################

# only works for DNA (4 letter alphabets)
# --------- #
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
######################################################

def test_main():
    kmer = 'GTCGCAGTCGCTGCC'
    lmer = 'CGCTGCCACCGCTG'
    pmer = 'CAGCGGCTGCGGA'

    print(edistance(pmer, lmer))
    print(edistance(pmer, kmer))


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


def test_main_2():
    f = open("test.data", 'w+')
    f.write('>5\t2\n>6\t2\n\n\n\n\n>7\t4\n')

    f.seek(0)

    f.readline()
    f.readline()
    f.readline()

    f.write('lol')

    f.close()

test_main_3()