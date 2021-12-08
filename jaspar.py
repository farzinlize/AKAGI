from math import log2
import os
import requests

from constants import PSEUDOCOUNT

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


# deprecated -> integrated into other functions
def pfm_to_pwm(pfm):

    sites_count = pfm[0]['A']+pfm[0]['C']+pfm[0]['G']+pfm[0]['T']
    pwm = [{'A':0, 'C':0, 'G':0, 'T':0} for i in range(len(pfm))]

    for i in range(len(pfm)):
        for letter in 'ACGT':
            pwm[i][letter] = log2( ( (pfm[i][letter]+(PSEUDOCOUNT/4) ) / (sites_count+PSEUDOCOUNT) )/0.25 )

    return pwm


def read_pfm(filename):

    with open(filename, 'r') as pfm:
        _ = pfm.readline()

        A = [int(float(a)) for a in pfm.readline().split()]
        C = [int(float(a)) for a in pfm.readline().split()]
        G = [int(float(a)) for a in pfm.readline().split()]
        T = [int(float(a)) for a in pfm.readline().split()]

        assert len(A) == len(C) and len(C) == len(G) and len(G) == len(T)

        # for some unknown reseon site count at each row is not equal in JASPAR dataset
        # sites_count = A[0]+C[0]+G[0]+T[0]
        # for i in range(1, len(A)): assert A[i]+C[i]+G[i]+T[i] == sites_count

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


def csv_pfm_and_pwm(filename, csv_filename):
    with open(csv_filename, 'w') as csv:
        pfm = read_pfm(filename)
        csv.write("Position Frequency Matrix\n")
        for alpha in 'ACGT':
            csv.write(alpha+',')
            for position in pfm:csv.write(str(position[alpha]) + ',')
            csv.write('\n')

        pwm = pfm_to_pwm(pfm)
        csv.write(f"Position Weight Matrix (using pseudocount={PSEUDOCOUNT})\n")
        for alpha in 'ACGT':
            csv.write(alpha+',')
            for position in pwm:csv.write(str(position[alpha]) + ',')
            csv.write('\n')


if __name__ == "__main__":
    csv_pfm_and_pwm(input(), input())