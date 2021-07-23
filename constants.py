# [WARNING] related to TREES_TYPE as global constant from app module
# any change to one of these lists must be applied to another
DATASET_TREES = [('', ''), ('gkhood56', 'cache56'), ('gkhood78', 'cache78')]

# ########################################## #
#                locations                   #
# ########################################## #

RESULT_LOCATION = './results/'
BINDING_SITE_LOCATION = './data/answers.fasta'
TWOBIT_LOCATION = './2bits/'
APPDATA_PATH = './appdata/'
SECRET_FILE_ADDRESS = 'secret.json'
MONGO_SECRET_ADDRESS = 'mongo.secret'
AKAGI_PREDICTION_STATISTICAL = 'akagi_1.fasta'
AKAGI_PREDICTION_EXPERIMENTAL = 'akagi_2.fasta'
CHAIN_REPORT_FILENAME = 'reporting.temp'
CR_FILE = 'chaining_report.window'
PROCESS_REPORT_FILE = 'process_%d.report'
GOOGLE_CREDENTIALS_FILE = 'cred.txt'
NETWORK_LOG = 'network.log'
DATABASE_LOG = 'database.log'
IMPORTANT_LOG = 'IMPORTANTE.log'
CHAINING_EXECUTION_STATUS = 'status.report'
BEST_PATTERNS_POOL = '%s_%d.pool'
MEMORY_BALANCING_REPORT = 'queue.report'


# ########################################## #
#                name tags                   #
# ########################################## #

FOUNDMAP_NAMETAG = '.byte'
QUEUE_NAMETAG = '.by2e'
DISK_QUEUE_NAMETAG = '.dq'
CHECKPOINT_TAG = '.checkpoint'
DATABASEFILE_TAG = '.database'
POOL_TAG = '.pool'


# ########################################## #
#            string constants                #
# ########################################## #

STR = b'\xFF'
DEL = b'\xDD'
END = b'\xFF'
PRT = b'\x00'

DNA_ALPHABET = 'ATCG'
DELIMETER = '-'
BYTE_READ_INT_MODE = 'big'
FOUNDMAP_DISK = 'disk'
FOUNDMAP_MEMO = 'memory'
QUEUE_DISK = 'qdisk'
QUEUE_MEMO = 'qmemory'
MAIL_SUBJECT = '[AKAGI][REPORT][AUTO-MAIL]'
MAIL_HEADER = \
'''
##################
Automatic report-mail from AKAGI
-> check attachments for additional files <-
##################
'''
CR_HEADER = '\n\tAKAGI - Chaining report window\n\n**details/warnings/errors**\n#######\n%s\n#######\n\n'
CR_TABLE_HEADER_SSMART = '\n\t\tSSMART SCORE TABLE\n\n'
CR_TABLE_HEADER_SUMMIT = '\n\t\tSUMMIT SCORE TABLE\n\n'
CR_TABLE_HEADER_JASPAR = '\n\t\tJASPAR SCORE TABLE\n\n'
TOP_TEN_REPORT_HEADER = '****** [AKAGI] TOP TEN REPORT ******\n'
PROCESS_REPORT_FILE_PATTERN = 'process_.*\.report'
PROCESS_ENDING_REPORT = \
'''
############ DONE ############
jobs done by me: %d
chaining done by me: %d
'''
LOCK_PREFIX = 'LOCK'
CLASSIC_MODE = '> id%d\n%s\n'
MEME_MODE = '>%d\n%s\n'


# ########################################## #
#              database mongo                #
# ########################################## #

DATABASE_NAME = 'akagidb'
DATABASE_ADDRESS = 'mongodb://%s:%s@localhost/?authSource=' + DATABASE_NAME
MONGO_USERNAME = 'akagi'
DEFAULT_COLLECTION = 'working'
MONGO_ID = '_id'
BINARY_DATA = 'data'
ID_LENGTH = 12
MAXIMUM_ORDER_SIZE = 10000

# commands
FIND_ONE = 'find'
CLEAR = 'clear'
INSERT_MANY = 'insert'


# ########################################## #
#              numeric values                #
# ########################################## #

BATCH_SIZE = 512
PATH_LENGTH = 10
TAG_LENGTH = 8
MAX_SEQUENCE_LENGTH = 400
MAX_SEQUENCE_COUNT = 200
INT_SIZE = 4
MINT_SIZE = 2
PSEUDOCOUNT = 1
AKAGI_PORT = 1090
POOL_HIT_SCORE = 2
CHAIN_REPORT_LINE_LIMIT = 15
INT_SIZE_BIT = 32
DISK_QUEUE_LIMIT = 100000
NEAR_FULL = 50000
NEAR_EMPTY = 1000
MEMORY_BALANCE_CHUNK_SIZE = 100
CHAINING_PERMITTED_SIZE = 30
TIMER_CHAINING_HOURS = 8
CHECK_TIME_INTERVAL = 5
TIMER_HELP_HOURS = 4
HELP_PORTION = 0.6
NEED_HELP = 50000
SOCKET_BUFFSIZE = 4096
LUCKY_SHOT = 1

POOL_SIZE = 100
GOOD_HIT_RATIO = 0.25
GOOD_HIT = POOL_SIZE * GOOD_HIT_RATIO


# ########################################## #
#             execution flags                #
#      and application configuration         #
# ########################################## #

BRIEFING = True
ON_SEQUENCE_ANALYSIS = True
MAIL_SERVICE = True
LIVE_REPORT = True
POOL_LIMITED = True
SAVE_OBSERVATION_CLOUD = False
CHAIN_REPORT_PRINT = False
MEME_FASTA_ID = True
PIXELS_ANALYSIS = True
PARENT_WORK = False
SAVE_THE_REST_CLOUD = True
HELP_CLOUD = True
HOPEFUL = True

FOUNDMAP_MODE = FOUNDMAP_DISK
QUEUE_MODE = QUEUE_DISK
CHAINING_FOUNDMAP_MODE = FOUNDMAP_MEMO

EMAIL_ACCOUNT = 'fantastic.farzin@gmail.com'
MAIL_TO = ['farzinlize@live.com', 'fmohammadi@ce.sharif.edu']
PC_NAME = 'Anakin'
EXECUTION = 'unnamed'


# ########################################## #
#                    enums                   #
# ########################################## #

ARG_UNSET = -1
FIND_MAX = -2
EXTRACT_KMER = 1
EXTRACT_OBJ = 0
FUNCTION_KEY = 0
ARGUMENT_KEY = 1
SIGN_KEY = 2
TABLE_HEADER_KEY = 3
MAX_CORE = -2
DB_TAG = 0
DB_LOCATION = 1
DB_PRT = 2
RANK = 'rank'
FDR_SCORE = 'FDR'
P_VALUE = 'maxlog2FC'
SUMMIT = 'summit'
SEQUENCES = 'seq'
SEQUENCE_BUNDLES = 'bundle'
PWM = 'pwm'
DATASET_NAME = 'name'
EXIT_SIGNAL = 'ex'

# encode column indexes
ENCODE_RANK = 0
ENCODE_CHR = 1
ENCODE_START = 2
ENCODE_END = 3
ENCODE_LEN = 5
ENCODE_FRD = 6
ENCODE_SUMMIT = 9
ENCODE_P = 14

# picture values
SEQUENCE_KEY = 0
POSITION_KEY = 1
MOTIF_KEY = 2
MARGIN_KEY = 3

TYPES_OF = {RANK:int, FDR_SCORE:float, P_VALUE:float, SUMMIT:int}