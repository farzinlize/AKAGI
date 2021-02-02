
# Global Variables
DATASET_TREES = [('gkhood5_8', 'dataset'), ('gkhood56', 'cache56'), ('gkhood78', 'cache78')]
HISTOGRAM_LOCATION = './results/figures/%s-f%s-d%s-q%d-g%d-o%d/'
RESULT_LOCATION = './results/'
BINDING_SITE_LOCATION = './data/answers.fasta'
TWOBIT_LOCATION = './2bits/'

ARG_UNSET = -1
FIND_MAX = -2

DELIMETER = '-'
DNA_ALPHABET = 'ATCG'
BATCH_SIZE = 512
PATH_LENGTH = 10

# bytes streaming constants
STR = b'\xFF'
DEL = b'\xDD'
END = b'\xFF'
INT_SIZE = 4
BYTE_READ_INT_MODE = 'big'

FOUNDMAP_DISK = 'disk'
FOUNDMAP_MEMO = 'memory'
FOUNDMAP_NAMETAG = '.byte'

QUEUE_DISK = 'qdisk'
QUEUE_MEMO = 'qmemory'
QUEUE_NAMETAG = '.by2e'

# default found-map/queue mode
FOUNDMAP_MODE = FOUNDMAP_DISK
QUEUE_MODE = QUEUE_DISK

SECRET_FILE_ADDRESS = 'secret.json'

MAIL_SUBJECT = '[AKAGI][REPORT][AUTO-MAIL]'
MAIL_HEADER = \
'''
##################
Automatic report-mail from AKAGI
-> check attachments for additional files <-
##################
'''

EMAIL_ACCOUNT = 'fantastic.farzin@gmail.com'
MAIL_TO = ['farzinlize@live.com', 'fmohammadi@ce.sharif.edu']

# encode column indexes
ENCODE_RANK = 0
ENCODE_CHR = 1
ENCODE_START = 2
ENCODE_END = 3
ENCODE_LEN = 5
ENCODE_FRD = 6
ENCODE_SUMMIT = 9
ENCODE_P = 14

# peak bundle
RANK = 'rank'
FDR_SCORE = 'FDR'
P_VALUE = 'maxlog2FC'
SUMMIT = 'summit'
TYPES_OF = {RANK:int, FDR_SCORE:float, P_VALUE:float, SUMMIT:int}

AKAGI_PREDICTION_STATISTICAL = 'akagi_1.fasta'
AKAGI_PREDICTION_EXPERIMENTAL = 'akagi_2.fasta'

# each file of DiskQueue contains fixed number of Byteable items
DISK_QUEUE_LIMIT = 1000
DISK_QUEUE_NAMETAG = '.dq'

EXTRACT_KMER = 1
EXTRACT_OBJ = 0

# chaining report
CONSOLE = '\r'
REMOTE = '\n'
CHAINING_REPORT_PEND = REMOTE

CHAINING_REPORT_EACH = True

POOL_LIMITED = True
POOL_LIMIT = 100

CHAIN_REPORT_LINE_LIMIT = 15
CHAIN_REPORT_FILENAME = 'reporting.temp'