
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
BATCH_SIZE = 100
PATH_LENGTH = 10

# bytes streaming constants
STR = b'\xFF'
DEL = b'\xDD'
END = b'\xFF'
INT_SIZE = 2
BYTE_READ_INT_MODE = 'big'

FOUNDMAP_DISK = 'disk'
FOUNDMAP_MEMO = 'memory'
FOUNDMAP_NAMETAG = '.byte'

QUEUE_NAMETAG = '.by2e'

# default found-map mode
FOUNDMAP_MODE = FOUNDMAP_MEMO

SECRET_FILE_ADDRESS = 'secret.json'

FOUNDMAP_MAIL_SUBJECT = '[AKAGI][REPORT][AUTO-MAIL] Memory usage problem of observation phase'
FOUNDMAP_MAIL_HEADER = \
'''
############################################
Automatic report-mail from AKAGI
-> check attachments for additional files <-
############################################
'''