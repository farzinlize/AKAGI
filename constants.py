# [WARNING] related to TREES_TYPE as global constant from app module
# any change to one of these lists must be applied to another
DATASET_TREES = [('', ''), ('gkhood56', 'cache56'), ('gkhood78', 'cache78')]

# Global Variables
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

# execution mode flags
MULTICORE = False
SERVER = False
BRIEFING = True
ON_SEQUENCE_ANALYSIS = True

# briefing values
MAX_SEQUENCE_LENGTH = 400
MAX_SEQUENCE_COUNT = 200

# bytes streaming constants
STR = b'\xFF'
DEL = b'\xDD'
END = b'\xFF'
INT_SIZE = 4
BYTE_READ_INT_MODE = 'big'

FOUNDMAP_DISK = 'disk'
FOUNDMAP_MEMO = 'memory'
FOUNDMAP_NAMETAG = '.byte'
APPDATA_PATH = './appdata/'

QUEUE_DISK = 'qdisk'
QUEUE_MEMO = 'qmemory'
QUEUE_NAMETAG = '.by2e'

# default found-map/queue mode
FOUNDMAP_MODE = FOUNDMAP_DISK
QUEUE_MODE = QUEUE_DISK
CHAINING_FOUNDMAP_MODE = FOUNDMAP_MEMO

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

# ranking pool values
POOL_LIMITED = True
POOL_SIZE = 100
GOOD_HIT_RATIO = 0.25
GOOD_HIT = POOL_SIZE * GOOD_HIT_RATIO
POOL_HIT_SCORE = 2

CHAIN_REPORT_PRINT = False
CHAIN_REPORT_LINE_LIMIT = 15
CHAIN_REPORT_FILENAME = 'reporting.temp'

PIXELS_ANALYSIS = True

# chaining report window
CR_HEADER = '\n\tAKAGI - Chaining report window\n\n**details/warnings/errors**\n#######\n%s\n#######\n\n'
CR_TABLE_HEADER_SSMART = '\n\t\tSSMART SCORE TABLE\n\n'
CR_TABLE_HEADER_SUMMIT = '\n\t\tSUMMIT SCORE TABLE\n\n'
CR_TABLE_HEADER_JASPAR = '\n\t\tJASPAR SCORE TABLE\n\n'
CR_FILE = 'chaining_report.window'
LIVE_REPORT = True

# multicore values
TRY_DELAY = 5 # second
TRY_COUNT = 10 # times
PARENT_WORK = False

# picture values
SEQUENCE_KEY = 0
POSITION_KEY = 1
MOTIF_KEY = 2
MARGIN_KEY = 3
INT_SIZE_BIT = 32

# network
HOST_ADDRESS = '127.0.0.1'
REQUEST_PORT = 1250
AGENTS_PORT_START = 1251
AGENTS_MAXIMUM_COUNT = 10
ACCEPT_REQUEST = b'\xAA'
REJECT_REQUEST = b'\xBB'

PSEUDOCOUNT = 1

# dataset dictionary keys
SEQUENCES = 'seq'
SEQUENCE_BUNDLES = 'bundle'
PWM = 'pwm'

NEAR_FULL = 5000
NEAR_EMPTY = 1000

CHAINING_PERMITTED_SIZE = 30

FUNCTION_KEY = 0
ARGUMENT_KEY = 1
SIGN_KEY = 2
TABLE_HEADER_KEY = 3

TOP_TEN_REPORT_HEADER = '****** [AKAGI] TOP TEN REPORT ******\n'

MEME_FASTA_ID = True
CLASSIC_MODE = '> id%d\n%s\n'
MEME_MODE = '>%d\n%s\n'

CHECKPOINT_TAG = '.checkpoint'
GOOGLE_CREDENTIALS_FILE = 'cred.txt'

TIMER_CHAINING_HOURS = 8
SAVE_THE_REST_CLOUD = True