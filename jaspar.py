import os
import requests

def read_jaspar_formatted_pfm(pfm):raise NotImplementedError

def costume_table_jaspar(dataset_name):

    table = {
        'ENCODE_HAIB_GM12878_SRF_peak':     'MA0083.2',
        'ENCODE_Stanford_HepG2_CEBPB_peak': 'MA0466.1',
        'ENCODE_Yale_HepG2_SREBF1_peak':    'MA0829.2'
    }

    return table[dataset_name.split('/')[-1]]


def get_jaspar_raw(jaspar):
    # check local
    if os.path.exists(f'pfms/{jaspar}.pfm'):
        return f'pfms/{jaspar}.pfm'

    with open(f'pfms/{jaspar}.pfm', 'wb') as pfm:
        pfm.write(requests.get(f'http://jaspar.genereg.net/api/v1/matrix/{jaspar}.pfm').content)

    return f'pfms/{jaspar}.pfm'