from functools import reduce
import struct
from io import BufferedReader, BytesIO
from math import ceil, e, log2, inf
from datetime import datetime, timedelta
import os, platform, random, string
from typing import Dict, List
from time import time as currentTime
from multiprocessing.synchronize import Lock

from constants import APPDATA_PATH, BYTE_READ_INT_MODE, DEL, DISK_QUEUE_LIMIT, DISK_QUEUE_NAMETAG, END, MAX_SEQUENCE_COUNT, MAX_SEQUENCE_LENGTH, PATH_LENGTH, INT_SIZE, PSEUDOCOUNT, P_VALUE, RANK, SUMMIT, TYPES_OF, STR


# ########################################## #
#                 class part                 #
# ########################################## #

'''
    Queue structure implementation (FIFO) in memory
        First in (insert), first out (pop)
'''
class Queue:
    def __init__(self, items=[]):self.queue = items
    def insert(self, item):self.queue = [item] + self.queue
    def isEmpty(self):return len(self.queue) == 0
    def pop(self):
        item = self.queue[-1]
        self.queue = self.queue[:-1]
        return item

'''
    Interface Bytable for QueueDisk entities 
'''
class Bytable:
    def to_byte(self):raise NotImplementedError
    @staticmethod
    def byte_to_object(buffer: BufferedReader): raise NotImplementedError


# testing purpose only
class TestByte(Bytable):
    def __init__(self, number, st):
        self.number = number
        self.st = st

    def to_byte(self):
        return int_to_bytes(self.number) + int_to_bytes(len(self.st)) + bytes(self.st, encoding='ascii')

    @staticmethod
    def byte_to_object(buffer: BufferedReader):
        number = bytes_to_int(buffer.read(INT_SIZE))
        size = bytes_to_int(buffer.read(INT_SIZE))
        st = str(buffer.read(size), 'ascii')
        return TestByte(number, st)


class QueueDisk:

    class QueueEmpty(Exception):pass

    def __init__(self, item_class:Bytable, items=None):
        self.item_class = item_class
        self.files = []
        self.counter = 0

        if items:
            self.insert_all(items)


    def insert_all(self, items: List[Bytable]):
        if len(self.files) == 0 or self.counter == DISK_QUEUE_LIMIT:
            self.files += [get_random_free_path(DISK_QUEUE_NAMETAG)]
            self.counter = 0

        queue = open(self.files[-1], 'ab')
        for item in items:

            if self.counter == DISK_QUEUE_LIMIT:
                self.files += [get_random_free_path(DISK_QUEUE_NAMETAG)]
                self.counter = 0
                queue.close()
                queue = open(self.files[-1], 'ab')

            queue.write(item.to_byte())
            self.counter += 1

        queue.close()


    '''
        pop one or many item from disk queue
            - always return list of objects
            - return objects as much as possible to match how_many but may return
                a list less than how_many if queue gets empty
    '''
    def pop_many(self, lock:Lock=None, how_many=1):

        if not self.files:
            return None

        # thread profing
        if len(self.files) == 1 and lock:
            lock.acquire()
            locked = True
        else:
            locked = False

        # reading
        popy_list = []
        queue_read = open(self.files[0], 'rb')
        for _ in range(how_many):
            popy = self.item_class.byte_to_object(queue_read)

            if not popy:
                queue_read.close()
                os.remove(os.path.join(self.files[0]))
                self.files = self.files[1:]

                # no more file (queue got empty)
                if not self.files:
                    return popy_list

                queue_read = open(self.files[0])
                popy = self.item_class.byte_to_object(queue_read)

                # error checking
                assert popy

            popy_list.append(popy)
        
        rest = queue_read.read()    
        queue_read.close()

        if rest:
            # writing modification
            with open(self.files[0], 'wb') as queue_write:
                queue_write.write(rest)
        else:
            os.remove(os.path.join(self.files[0]))
            self.files = self.files[1:]

        if locked: lock.release()

        return popy_list


    def insert(self, item: Bytable, lock:Lock=None):

        if len(self.files)<=1 and lock:
            lock.acquire()
            locked = True
        else:
            locked = False

        if len(self.files) == 0 or self.counter == DISK_QUEUE_LIMIT:
            self.files += [get_random_free_path(DISK_QUEUE_NAMETAG)]
            self.counter = 0

        self.counter += 1
        with open(self.files[-1], 'ab') as queue:
            queue.write(item.to_byte())

        if locked: lock.release()


    def isEmpty(self) -> bool:
        return len(self.files) == 0


'''
    File handler object -> accumulate data packages in seprated file with size limit
        at each line two value (neighbout-kmer and its distance) will be saved
        after inserting all d-neighbours lines, if line count exceededs the limit, 
        next set will be saved in another file
'''
class FileHandler:
    def __init__(self, directory_name=None, max_size=1000000, filename_prefix=''):

        self.prefix = filename_prefix

        # file address splitter is different in windows and linux
        operating_system = platform.system()
        if operating_system == 'Windows':
            splitter = '\\'
        else:   # operating_system == 'Linux'
            splitter = '/'

        if directory_name == None:
            self.directory = os.getcwd() + splitter + 'dataset' + splitter
        else:
            self.directory = os.getcwd() + splitter + directory_name + splitter

        try:
            os.mkdir(self.directory, 0o755)
        except:
            print('[WARNING] directory already exist')

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

        # progressing commend - BAD IDEA - never do this again
        # print('size ->', self.position - position)

        if self.position >= self.max_size:
            self.next_file()
        return data_index, position


    def close(self):
        self.current_file.close()
        return self.file_index, self.position


    def reopen(self):
        self.current_file = open(self.directory + self.prefix + str(self.file_index)+'.data', 'a')


class ExtraPosition:
    def __init__(self, position, size):
        self.start_position = position
        self.size = size
        # self.chain = chain

    def end_position(self):
        return self.start_position + self.size
    # def get_chain(self):
    #     return self.chain + [self.start_position]

    def __lt__(self, other):
        return self.start_position < other.start_position

    def __le__(self, other):
        return self.start_position <= other.start_position

    def __eq__(self, other):
        return self.start_position == other.start_position and self.size == other.size

    def __ne__(self, other):
        return self.start_position != other.start_position

    def __gt__(self, other):
        return self.start_position > other.start_position

    def __ge__(self, other):
        return self.start_position >= other.start_position

    def __repr__(self):
        return '(%d, %d)'%(self.start_position, self.size)

    def __str__(self):
        return '(%d, %d)'%(self.start_position, self.size)

    def __int__(self):
        return self.start_position + self.size


class ThatException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


# ########################################## #
#                 functions                  #
# ########################################## #

def time_has_ended(since, hours):
    return (datetime.now() - since) > timedelta(hours=hours)


def log_it(logfile, message):
    if message:
        with open(logfile, 'a') as log:
            log.write(message)
            if message[-1] != '\n':log.write('\n')


def GFF_to_fasta(gff_name, fasta_name):
    with open(gff_name, 'r') as gff, open(fasta_name, 'w') as fasta:
        _ = gff.readline() # gff version line
        for line in gff:
            for attribute in line.split()[8].split(';'):
                if attribute.startswith('sequence='):
                    fasta.write('>1\n%s\n'%attribute[9:])
                    break


def memechip_jaspar_evaluation(memehip_motif_sites, jaspar):
    sequences = read_fasta(memehip_motif_sites)
    pwm, rpwm = read_pfm_save_pwm(jaspar)
    
    aggregated = 0
    for sequence in sequences:
        score, _ = pwm_score_sequence(sequence, pwm)
        r_score, _ = pwm_score_sequence(sequence, rpwm)
        aggregated += max(score, r_score)
    
    print('jasper score of memechip motif -> %.2f'%(aggregated/len(sequences)))
    

def read_meme_motif_to_pwm(memechip_motif_address):

    pwm = []
    with open(memechip_motif_address, 'r') as memechip_file:

        for line in memechip_file:

            col = {}
            sum_col = 0
            index = 0
            for letter_count in [int(token) for token in line.split()]:
                meme_order = 'ACGT'
                sum_col += letter_count
                col.update({meme_order[index]:letter_count})
                
                index = (index+1)%4
            
            for letter in col.keys():
                col[letter] = log2( ( (col[letter]+(PSEUDOCOUNT/4)) / (sum_col+PSEUDOCOUNT) )/0.25 )

            pwm.append(col)
        
    return pwm


def read_pfm(filename):

    with open(filename, 'r') as pfm:
        _ = pfm.readline()

        A = [int(float(a)) for a in pfm.readline().split()]
        C = [int(float(a)) for a in pfm.readline().split()]
        G = [int(float(a)) for a in pfm.readline().split()]
        T = [int(float(a)) for a in pfm.readline().split()]

        assert len(A) == len(C) and len(C) == len(G) and len(G) == len(T)
        sites_count = A[0]+C[0]+G[0]+T[0]
        for i in range(1, len(A)): assert A[i]+C[i]+G[i]+T[i] == sites_count

        return [{'A':A[i], 'C':C[i], 'G':G[i], 'T':T[i]} for i in range(len(A))]


def read_pfm_save_pwm(filename):

    cal = lambda col, row:log2( ( (col[row]+(PSEUDOCOUNT/4) ) / (A[row]+C[row]+G[row]+T[row]+PSEUDOCOUNT) )/0.25 )

    with open(filename, 'r') as pfm:
        _ = pfm.readline()

        A = [int(float(a)) for a in pfm.readline().split()]
        C = [int(float(a)) for a in pfm.readline().split()]
        G = [int(float(a)) for a in pfm.readline().split()]
        T = [int(float(a)) for a in pfm.readline().split()]

        rA = list(reversed(T))
        rC = list(reversed(G))
        rG = list(reversed(C))
        rT = list(reversed(A))

        assert len(A) == len(C) and len(C) == len(G) and len(G) == len(T)

        # for some unknown reseon site count at each row is not equal in JASPAR dataset
        # sites_count = A[0]+C[0]+G[0]+T[0]
        # for i in range(1, len(A)): assert A[i]+C[i]+G[i]+T[i] == sites_count

        return [{'A':cal(A, i), 'C':cal(C, i), 'G':cal(G, i), 'T':cal(T, i)} for i in range(len(A))], \
            [{'A':cal(rA, i), 'C':cal(rC, i), 'G':cal(rG, i), 'T':cal(rT, i)} for i in range(len(A))]


# deprecated -> integrated into other functions
def pfm_to_pwm(pfm):

    sites_count = pfm[0]['A']+pfm[0]['C']+pfm[0]['G']+pfm[0]['T']
    pwm = [{'A':0, 'C':0, 'G':0, 'T':0} for i in range(len(pfm))]

    for i in range(len(pfm)):
        for letter in 'ACGT':
            pwm[i][letter] = log2( ( (pfm[i][letter]+(PSEUDOCOUNT/4) ) / (sites_count+PSEUDOCOUNT) )/0.25 )

    return pwm


def pwm_score_sequence(sequence, pwm):
    
    max_score = -inf

    for i in range(1, len(sequence) + len(pwm)):

        seq_idx = max(0, i - len(pwm))
        ref_idx = max(0, len(pwm) - i)

        score = 0
        while seq_idx < len(sequence) and ref_idx < len(pwm):
            score += pwm[ref_idx][sequence[seq_idx]]
            ref_idx += 1; seq_idx += 1

        if score >= max_score:
            max_score = score
            max_position = seq_idx
    
    return max_score, max_position


# deprecated -> wrong score
def pwm_score_sequence_bad(sequence, pwm):

    if len(sequence) < len(pwm):
        return 0, -1

    max_score = -inf

    for start in range(len(sequence)-len(pwm)+1):

        score = 0
        for i in range(len(pwm)):
            score += pwm[i][sequence[start+i]]

        if score >= max_score:
            max_score = score
            max_position = start
    
    return max_score, max_position


def brief_sequence(sequences, bundles:List[Dict]):
    zipped = [(sequences[i], bundles[i]) for i in range(len(sequences))]
    zipped.sort(key=lambda x:x[1][P_VALUE], reverse=True)

    if len(zipped) > MAX_SEQUENCE_COUNT:
        zipped = zipped[:MAX_SEQUENCE_COUNT]

    brief_sequences = []
    brief_bundles = []
    for sequence, bundle in zipped:
        if len(sequence) > MAX_SEQUENCE_LENGTH:
            summit = bundle[SUMMIT]
            start = ceil((2*summit-MAX_SEQUENCE_LENGTH)/2)
            end = ceil((2*summit+MAX_SEQUENCE_LENGTH)/2)

            if start < 0:
                end += abs(start)
                start = 0

            brief_sequences += [sequence[start:end]]
            bundle.update({SUMMIT:summit-start})
        else:
            brief_sequences += [sequence]
        brief_bundles += [bundle]

    return brief_sequences, brief_bundles


def clear_screen(): 

    # for windows 
    if os.name == 'nt': 
        _ = os.system('cls') 
  
    # for mac and linux(here, os.name is 'posix') 
    else: 
        _ = os.system('clear') 


def lap_time(last_time):
    now = currentTime()
    lap = now - last_time
    return lap, now


# generate a free path with random name and defined extension (like .byte)
def get_random_free_path(extension, length=PATH_LENGTH, directory=APPDATA_PATH) -> str:
    random_name = directory + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length)) + extension
    while os.path.isfile(random_name):
        random_name = directory + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length)) + extension
    return random_name


# deprecated - useing `get_random_free_path` instead
def get_random_path(length=PATH_LENGTH):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


# add an item to a sorted list using binary search
def binary_add(lst, item, allow_equal=False):
    start = 0
    end = len(lst)-1
    while start <= end:
        mid = (start+end)//2
        if lst[mid] == item:
            if allow_equal:
                return lst[:mid] + [item] + lst[mid:]
            else:
                return lst
        elif lst[mid] < item:
            start = mid + 1
        else:
            end = mid - 1
    return lst[:start] + [item] + lst[start:]


def binary_add_return_position(lst, item):
    start = 0
    end = len(lst)-1
    while start <= end:
        mid = (start+end)//2
        if lst[mid] == item:
            return lst[:mid] + [item] + lst[mid:], mid
        elif lst[mid] < item:
            start = mid + 1
        else:
            end = mid - 1
    return lst[:start] + [item] + lst[start:], start


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
    with open(filename, 'r') as fasta:
        for line in fasta:
            if line[0] == '>':
                continue
            sequences += [line[:-1]]
    return sequences


def read_bundle(filename):
    bundles = []
    with open(filename, 'r') as bundle:
        dictionary = {}
        for line in bundle:
            if line[0] == '>':
                if dictionary:
                    bundles += [dictionary]
                rank = int(line.split('=')[1])
                dictionary = {RANK:TYPES_OF[RANK](rank)}
            else:
                key, value = line.split(',')
                dictionary.update({key: TYPES_OF[key](value)})
    
    bundles += [dictionary]
    return bundles


def read_peak_fasta(filename):

    def bucket_sort(lst, second, ranks):
        buckets = [None for _ in range(len(lst))]
        second_buckets = [None for _ in range(len(lst))]
        for index, item in enumerate(lst):
            try:
                if buckets[ranks[index]] != None:
                    print('[error] rank position occupied (ignoring afterward policy) | ranks[index]=%d'%(
                        ranks[index]))
                    continue

                buckets[ranks[index]] = item
                second_buckets[ranks[index]] = second[index]

            except IndexError:
                print('[WARNING] rank out of range (ignoring entity) | ranks[index]=%d, size(limit)=%d'%(
                    ranks[index], len(lst)))

        # error detection
        errors = 0
        index = 0
        while index < len(buckets):

            # error found
            if buckets[index] == None:
                errors += 1

                # error handle
                buckets = buckets[:index] + buckets[index+1:]
                second_buckets = second_buckets[:index] + second_buckets[index+1:]

            # no need to increase index if deletion happend
            else:
                index += 1
                
        print('[SORT] number of errors in ranking data: %d (sequences with unknown rank are deleted)'%errors)
        return buckets, second_buckets


    sequences = []
    ranks_ids = []
    ranking_bundles = []
    virgin = True

    with open(filename, 'r') as fasta:
        read_sequence = False
        rank_info = {}
        for line in fasta:

            # fasta command
            if line[0] == '>':
                assert read_sequence == False

                if virgin:
                    virgin = False
                elif line.startswith('> scores'):
                    continue
                else:
                    assert rank_info
                    ranking_bundles += [rank_info]

                ranks_ids += [(int(line.split('=')[1])-1)]
                rank_info = {}
                read_sequence = True

            # data
            else:
                if read_sequence:
                    sequences += [line[:-1]]
                    read_sequence = False
                else:
                    title, score = line.split(',')
                    rank_info.update({title:float(score)})

        assert rank_info
        ranking_bundles += [rank_info]

    assert len(sequences) == len(ranking_bundles) and len(ranks_ids) == len(sequences)
    return bucket_sort(sequences, ranking_bundles, ranks_ids)


def make_location(location):
    if location == '':
        return
    try:
        os.makedirs(location)
    except:
        pass


# A Dynamic Programming based Python program for edit  distance problem 
def editDistDP(str1, str2): 
    m = len(str1); n = len(str2)

    # Create a table to store results of subproblems 
    dp = [[0 for x in range(n + 1)] for x in range(m + 1)] 
  
    # Fill d[][] in bottom up manner 
    for i in range(m + 1): 
        for j in range(n + 1): 
  
            # If first string is empty, only option is to 
            # insert all characters of second string 
            if i == 0: 
                dp[i][j] = j    # Min. operations = j 
  
            # If second string is empty, only option is to 
            # remove all characters of second string 
            elif j == 0: 
                dp[i][j] = i    # Min. operations = i 
  
            # If last characters are same, ignore last char 
            # and recur for remaining string 
            elif str1[i-1] == str2[j-1]: 
                dp[i][j] = dp[i-1][j-1] 
  
            # If last character are different, consider all 
            # possibilities and find minimum 
            else: 
                dp[i][j] = 1 + min(dp[i][j-1],        # Insert 
                                   dp[i-1][j],        # Remove 
                                   dp[i-1][j-1])    # Replace 
    
    # for e in dp:
    #     for r in e:
    #         if len(str(r)) == 2:
    #             print(r, end=' ')
    #         else:
    #             print(r, end='  ')
    #     print()

    return dp[m][n] 


def edit_distances_matrix(sequences):
    result = '\n'
    for a in sequences:
        for b in sequences:
            d = editDistDP(a, b)
            result += ' ' + str(d) + ' '*(4-len(str(d)))
        result += '\n\n'
    return result


def extract_from_fasta(fasta, dataset):
    read = False
    binding_sites = []
    for line in fasta:
        if dataset in line:
            read = True
        elif read:
            if '>' in line:
                if 'instances' in line:
                    continue
                return binding_sites
            else:
                binding_sites += [line]
    return binding_sites


def change_global_constant_py(variable_name: str, new_value: str):
    with open('constants.py', 'r') as f:
        content = f.readlines()
    
    with open('constants.py', 'w') as f:
        for line in content:
            list_line = line.split('=')

            if len(list_line) == 1:
                f.write(line)
                continue

            if len(list_line) > 2:rest_of_the_line = "=".join(list_line[1:])
            else                 :rest_of_the_line = list_line[1]
            
            f.write(list_line[0] + '=')

            if "".join(list_line[0].split()) == variable_name:
                f.write(' ' + new_value + '\n')
            else:
                f.write(rest_of_the_line)


def make_compact_dataset(filename, sequences, bundles, pwm):
    with open(filename, 'wb') as compact:
        compact.write(int_to_bytes(len(sequences)))
        for sequence, bundle in zip(sequences, bundles):
            compact.write(int_to_bytes(len(sequence)))
            compact.write(bytes(sequence, 'utf8'))
            compact.write(int_to_bytes(bundle[SUMMIT]))
            compact.write(struct.pack('d', bundle[P_VALUE]))
        
        pwm_a = pwm[0]
        pwm_r = pwm[1]
        assert len(pwm_a) == len(pwm_r)

        lm = len(pwm_a) # Length of the Motif
        flattern = lambda a, b:([ai for ai in a] + [bi for bi in b])
        
        compact.write(int_to_bytes(lm))
        for alphabet in 'ACGT':
            compact.write(struct.pack('d'*lm*2, *reduce(flattern, [(pwm_a[i][alphabet], pwm_r[i][alphabet]) for i in range(lm)])))



# ########################################## #
#           foundmap list binary             #
# ########################################## #

def binary_to_list(reader:BytesIO):

    sequences = []
    positions_vector = []

    # check header byte signature
    assert reader.read(1) == STR

    # reading sequence vector
    for _ in range(bytes_to_int(reader.read(INT_SIZE))):
        sequences += [bytes_to_int(reader.read(INT_SIZE))]
                    
    assert reader.read(1) == DEL

    # reading 2D-position vector
    for _ in range(len(sequences)):
        positions = []
        for _ in range(bytes_to_int(reader.read(INT_SIZE))):
            position = bytes_to_int(reader.read(INT_SIZE))
            size = bytes_to_int(reader.read(INT_SIZE))
            positions += [ExtraPosition(position, size)]
        positions_vector += [positions[:]]

        assert reader.read(1) == DEL
                
    assert reader.read(1) == END

    return [sequences, positions_vector]


def list_to_binary(found_list):

    writer = BytesIO()
    sequences = found_list[0]
    positions_vector = found_list[1]

    # header byte signature
    writer.write(STR)

    # writing sequence vector
    writer.write(int_to_bytes(len(sequences)))
    for seq_id in sequences:
        writer.write(int_to_bytes(seq_id))
                
    writer.write(DEL)

    # writing 2D-position vector
    for index in range(len(sequences)):
        writer.write(int_to_bytes(len(positions_vector[index])))
        position: ExtraPosition
        for position in positions_vector[index]:
            writer.write(int_to_bytes(position.start_position))
            writer.write(int_to_bytes(position.size))
                
        writer.write(DEL)

    writer.write(END)

    return writer.getvalue()


# ########################################## #
#            byte read functions             #
# ########################################## #

# functions consider unsigned integer if not mentioned
def bytes_to_int(b :bytes, signed=False, endian=BYTE_READ_INT_MODE):
    return int.from_bytes(b, endian, signed=signed)


def int_to_bytes(i, int_size=INT_SIZE, signed=False):
    return i.to_bytes(int_size, BYTE_READ_INT_MODE, signed=signed)


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
#           main function section            #
# ########################################## #

def test_diskQueue():
    items = [TestByte(5, 'Bee_salam'), TestByte(55, 'start')]

    queue = QueueDisk(TestByte, items)

    bee = queue.pop()
    print('bee -> number=%d,string=%s'%(bee.number, bee.st))

    for i in range(100000):
        random_name = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
        queue.insert(TestByte(i+1, random_name))

    index = 0
    while not queue.isEmpty():
        popy = queue.pop()
        print('index:%d,number=%d,string=%s'%(index, popy.number, popy.st))
        index += 1


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


def outer_f(a, b, c):
    def inner_f(h):
        nonlocal lst
        print('a', a)
        # print('inner:',lst)
        if h:
            # print('here')
            lst = []
        else:
            lst = [100000]

    y = 10
    lst = [5, 6]
    print(lst)
    inner_f(1)
    print(lst)
    inner_f(0)
    print(lst)


def workbench_tests():
    seq = ['TACAATTTTATATGTATATTTTTATTTTATTTTTTTTAAAT', 'TACATTTACTATATGTATTTATTTATTTCTTTAGAT', 'TACAACTTTTATGTTTATTTCATTTTAAAGATTTTTAAAAT', 'AACAATTTATTTATATTTAAATTTATTTTAATTTGTTTCAAT']
    print(edit_distances_matrix(seq))


def test_binary_add():
    l = [1, 3, 6, 8, 12, 56, 89]
    item = 0

    l, index = binary_add_return_position(l, item, allow_equal=True)
    print(l)
    print(index)


# ########################################## #
#           main function call               #
# ########################################## #

# main function call
if __name__ == "__main__":
    # test = read_pfm('./pfms/test2.pfm')
    # pwm = pfm_to_pwm(test)
    change_global_constant_py('SEQUENCE_KEY', '56')
    # memechip_jaspar_evaluation('./memechip/SRF.fasta', './pfms/MA0083.2.pfm')
    # GFF_to_fasta('./memechip/SRF.gff', './memechip/SRF.fasta')
    # pwm_2 = read_pfm_save_pwm('./pfms/meme_my.pfm')
    # pwm_1 = read_meme_motif_to_pwm('./memechip/motif_3_counts.txt')
    # print(pwm_1)
    # print('-------------------')
    # print(pwm_2)
    # test_binary_add()
    # test_diskQueue()
    # b = read_bundle('./hmchipdata/Human_hg18_peakcod/ENCODE_Broad_GM12878_H3K4me1_peak.bundle')
    # seq, rank = read_peak_fasta('./hmchipdata/Human_hg18_peakcod/ENCODE_Broad_GM12878_H3K4me1_peak.fasta')
    # print(rank)
    # print(bytes_to_int(int_to_bytes(-1, signed=True), signed=True))
    # change_global_constant_py('FOUNDMAP_DISK', "'fuck'")
    # test_main_3()
    # outer_f(5, 6, 2)