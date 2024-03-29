import os, sys

if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1] in ['-f', '--force']:ignore = True
    else                                                     :ignore = False

    cut_line = 37
    if os.path.isfile('constants.py') and not ignore: # merge
        
        # read configured as dictionary
        with open('constants.py', 'r') as configured:
            conf_dict = {}
            for line in configured:
                list_line = line.split('=')
                if   len(list_line) == 1:continue
                elif len(list_line) >  2:rest_of_the_line = "=".join(list_line[1:])
                else                    :rest_of_the_line = list_line[1]
                conf_dict.update({''.join(list_line[0].split()):rest_of_the_line})

        with open('constants_template.py', 'r') as template, open('constants.py', 'w') as merge:
            for _ in range(cut_line):template.readline() # ignore module functions
            for line in template:
                list_line = line.split('=')
                if   len(list_line) == 1:merge.write(line);continue
                else                    :rest_of_the_line = "=".join(list_line[1:])
                
                key = ''.join(list_line[0].split())
                if key in conf_dict:rest_of_the_line = conf_dict[key]
                merge.write(key + ' =' + rest_of_the_line)

    else: # create or force creating new one
        with open('constants_template.py', 'r') as template, open('constants.py', 'w') as module:
            for _ in range(cut_line):template.readline() # ignore module functions
            module.write(template.read())

# - - < - cut file - - - - - - - - - - - - - - - - - - - - 

# [WARNING] related to TREES_TYPE as global constant from app module
# any change to one of these lists must be applied to another
DATASET_TREES = [('', ''), ('gkhood56', 'cache56'), ('gkhood78', 'cache78')]

# ########################################## #
#                locations                   #
# ########################################## #

AKAGI_PATH = 'D:/Optic Lab/AKAGI/'

BINDING_SITE_LOCATION = f'{AKAGI_PATH}data/answers.fasta'
TWOBIT_LOCATION = f'{AKAGI_PATH}2bits/'
APPDATA_PATH = f'{AKAGI_PATH}appdata/'
SECRET_FILE_ADDRESS = f'{AKAGI_PATH}secret.json'
MONGO_SECRET_ADDRESS = f'{AKAGI_PATH}mongo.secret'
CR_FILE = f'{AKAGI_PATH}chaining_report.window'
PROCESS_REPORT_FILE = f'{AKAGI_PATH}OnE/process_%d.report'
PROCESS_ERRORS_FILE = f'{AKAGI_PATH}OnE/process_%d.error'
GOOGLE_CREDENTIALS_FILE = f'{AKAGI_PATH}cred.txt'
NETWORK_LOG = f'{AKAGI_PATH}network.log'
DATABASE_LOG = f'{AKAGI_PATH}database.log'
IMPORTANT_LOG = f'{AKAGI_PATH}IMPORTANTE.log'
DEBUG_LOG = f'{AKAGI_PATH}debug.log'
CHAINING_EXECUTION_STATUS = f'{AKAGI_PATH}status.report'
BANK_PORTS_REPORT = f'{AKAGI_PATH}bankports.report'
WORKERS_ID_REPORT = f'{AKAGI_PATH}workersid.report'
COMMAND_WHILE_CHAINING = f'{AKAGI_PATH}command.app'
MEMORY_BALANCING_REPORT = f'{AKAGI_PATH}queue.report'
COMPACT_DATASET_TEMP_LOCATION = f'{AKAGI_PATH}compact.temp'


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

MEMOMAP = b'\x00'
FILEMAP = b'\x01'
READMAP = b'\x02'

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
GLOBAL_POOL_NAME = 'global'


# ########################################## #
#              database mongo                #
# ########################################## #

DATABASE_NAME = 'akagidb'
MONGO_USERNAME = 'akagi'
DEFAULT_COLLECTION = 'working'
QUEUE_COLLECTION = 'queue'
POOLS_COLLECTION = 'pools'
MONGO_PORT = 2090
ID_LENGTH = 12
MAXIMUM_ORDER_SIZE = 10000
AUTORECONNECT_TRY = 5
DATABASE_ADDRESS = f'mongodb://%s:%s@localhost:{MONGO_PORT}/?authSource=' + DATABASE_NAME
BANKBASE_ADDRESS = 'mongodb://%s:%s@localhost:%d/?authSource=' + DATABASE_NAME
MONGOD_RUN_SERVER_COMMAND_LINUX = f'mongod --dbpath {APPDATA_PATH}mongod/ --fork --logpath {AKAGI_PATH}logs/mongo.log --auth --port {MONGO_PORT}'
RAW_MONGOD_SERVER_COMMAND_LINUX = f'mongod --dbpath %s --fork --logpath {AKAGI_PATH}logs/%s.log %s --port %d'
MONGOD_SHUTDOWN_COMMAND = 'mongod --dbpath %s --shutdown'

# document enums
MONGO_ID = '_id'
BINARY_DATA = 'data'
LABEL = 'l'
POOL_NAME = 'name'
TABLES = 'tables'
BYTE_PATTERN = 'pattern'
SCORES = 'scores'

# commands
FIND_ONE = 'find'
CLEAR = 'clear'
POP = 'pop'
INSERT_MANY = 'insert'
INSERT_ONE = 'ione'
UPDATE = 'up'
COLLECTION = 'load'
DROP = 'drop'


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
MAXIMUM_MEMORY_BALANCE = 5000000
NEAR_FULL = 50000
NEAR_EMPTY = 1000
PERMIT_RESTORE_AFTER = 5
MINIMUM_CHUNK_SIZE = 100
CHAINING_PERMITTED_SIZE = 30
TIMER_CHAINING_HOURS = 8
CHECK_TIME_INTERVAL = 5
TIMER_HELP_HOURS = 4
HELP_PORTION = 0.6
NEED_HELP = 50000
SOCKET_BUFFSIZE = 4096
JUDGE_PORT = 2081

POOL_SIZE = 100
GOOD_HIT_RATIO = 0.25
GOOD_HIT = POOL_SIZE * GOOD_HIT_RATIO


# ########################################## #
#             execution flags                #
#      and application configuration         #
# ########################################## #

BRIEFING = True
ON_SEQUENCE_ANALYSIS = False
POOL_LIMITED = True
MEME_FASTA_ID = True
PIXELS_ANALYSIS = True
PARENT_WORK = False
AUTO_DATABASE_SETUP = True
SAVE_ONSEQUENCE_FILE = False
BYTES_OR_PICKLE = True
CHECKPOINT = True

FOUNDMAP_MODE = FOUNDMAP_DISK
QUEUE_MODE = QUEUE_DISK
CHAINING_FOUNDMAP_MODE = FOUNDMAP_MEMO

EMAIL_ACCOUNT = 'fantastic.farzin@gmail.com'
MAIL_TO = ['farzinlize@live.com', 'fmohammadi@ce.sharif.edu']
PC_NAME = 'Anakin'
EXECUTION = 'unnamed'

# cplus configuration
WORKER_NAME = 'worker'
WORKER_FAST = 'fworker'
CPLUS_WORKER = True
WORKER_MODE = WORKER_FAST
WORKER_EXECUTABLE = f'{AKAGI_PATH}cplus/build/{WORKER_MODE}'

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
SAVE_SIGNAL = 'sv'
REPORT_SIGNAL = 'rp'
REDIRECT_BANK = 'redirect'
RESET_BANK = 'reset'
BANK_NAME = 'BANK%d'
BANK_PATH = APPDATA_PATH + 'bank%d/'
CONTINUE_SIGNAL = 'co'
STATUS_RUNNING = 'running'
STATUS_SUSSPENDED = 'sus'

# cplus workers signals
C_TERMINATE_SIGNAL = b'T'
C_RESUME_SIGNAL = b'R'
C_CHANGE_BANK_SIGNAL = b'C'

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

# # # # # # # # # # # # # # # # # # # # #
#    DEPRECATED VARIABLES FOR ARCHIVE   #
# # # # # # # # # # # # # # # # # # # # #
# AKAGI_PREDICTION_STATISTICAL = 'akagi_1.fasta'
# AKAGI_PREDICTION_EXPERIMENTAL = 'akagi_2.fasta'
# CHAIN_REPORT_FILENAME = 'reporting.temp'
# BEST_PATTERNS_POOL = '%s_%d.pool'
# CHAIN_REPORT_PRINT = False
# # # # # # # # # # # # # # # # # # # # #