from math import log2, log
from TrieFind import ChainNode
from alignment import alignment_strings
from logomaker import Logo, alignment_to_matrix
from pandas import DataFrame
from misc import maxSubArraySum, make_location
import matplotlib.pyplot as plt

from constants import PSEUDOCOUNT

def make_pattern_report(name, pattern:ChainNode, sequences, directory=''):

    def no_negative(data_frame):
        for alphabet in 'ATCG':
            for i in range(len(data_frame)):
                if data_frame[alphabet][i] < 0:data_frame[alphabet][i] = 0

    make_location(directory)
    cal = lambda col, row, count:log2( ( (col[row]+(PSEUDOCOUNT/4) ) / (count+PSEUDOCOUNT) )/0.25 )
    
    binding_sites = pattern.instances_list(sequences)
    aligned_sites = alignment_strings(binding_sites)
    aligned_matrix = alignment_to_matrix(aligned_sites)

    position_counts = [sum(aligned_matrix[alphabet][i] for alphabet in 'ACGT') for i in range(len(aligned_matrix))]
    average_count = sum(position_counts) / len(position_counts)
    shifted_counts = [c-average_count for c in position_counts]
    log_shifted_counts = [log(c/average_count) for c in position_counts]
    
    _, start, end         = maxSubArraySum(shifted_counts)
    _, log_start, log_end = maxSubArraySum(log_shifted_counts)

    plt.plot(position_counts)
    plt.ylabel('position counts')
    plt.xlabel('alignment positions')
    plt.savefig(f'{directory}{name}_bs_alignment_positioncount.png')
    plt.clf()

    plt.plot(shifted_counts)
    plt.ylabel('shifted position counts by average')
    plt.xlabel('alignment positions')
    plt.axhline(0, color='red')
    plt.axvline(start, color='red')
    plt.axvline(end, color='red')
    plt.savefig(f'{directory}{name}_bs_alignment_positioncount_shifted.png')
    plt.clf()

    plt.plot(log_shifted_counts)
    plt.ylabel('log shifted position counts by average')
    plt.xlabel('alignment positions')
    plt.axhline(0, color='red')
    plt.axvline(log_start, color='red')
    plt.axvline(log_end, color='red')
    plt.savefig(f'{directory}{name}_bs_alignment_positioncount_logshifted.png')
    plt.clf()

    alignment_logo = Logo(aligned_matrix)
    alignment_logo.draw()
    plt.xlabel('alignment by muscle')
    plt.savefig(f'{directory}{name}_bs_alignment.png')
    plt.clf()

    A = list(aligned_matrix['A'][start:end+1])
    C = list(aligned_matrix['C'][start:end+1])
    T = list(aligned_matrix['T'][start:end+1])
    G = list(aligned_matrix['G'][start:end+1])

    Al = list(aligned_matrix['A'][log_start:log_end+1])
    Cl = list(aligned_matrix['C'][log_start:log_end+1])
    Tl = list(aligned_matrix['T'][log_start:log_end+1])
    Gl = list(aligned_matrix['G'][log_start:log_end+1])

    # r_start     = len(aligned_matrix) - end
    # r_end       = len(aligned_matrix) - start
    # r_log_start = len(aligned_matrix) - log_end
    # r_log_end   = len(aligned_matrix) - log_start

    rA = list(reversed(list(aligned_matrix['T'][start:end+1])))
    rC = list(reversed(list(aligned_matrix['G'][start:end+1])))
    rG = list(reversed(list(aligned_matrix['C'][start:end+1])))
    rT = list(reversed(list(aligned_matrix['A'][start:end+1])))

    rAl = list(reversed(list(aligned_matrix['T'][log_start:log_end+1])))
    rCl = list(reversed(list(aligned_matrix['G'][log_start:log_end+1])))
    rGl = list(reversed(list(aligned_matrix['C'][log_start:log_end+1])))
    rTl = list(reversed(list(aligned_matrix['A'][log_start:log_end+1])))

    data = {'A':[cal(A, i, A[i]+T[i]+C[i]+G[i]) for i in range(len(A))], 
            'T':[cal(T, i, A[i]+T[i]+C[i]+G[i]) for i in range(len(T))], 
            'C':[cal(C, i, A[i]+T[i]+C[i]+G[i]) for i in range(len(C))], 
            'G':[cal(G, i, A[i]+T[i]+C[i]+G[i]) for i in range(len(G))]}
    
    rdata = {'A':[cal(rA, i, rA[i]+rT[i]+rC[i]+rG[i]) for i in range(len(rA))], 
             'T':[cal(rT, i, rA[i]+rT[i]+rC[i]+rG[i]) for i in range(len(rT))], 
             'C':[cal(rC, i, rA[i]+rT[i]+rC[i]+rG[i]) for i in range(len(rC))], 
             'G':[cal(rG, i, rA[i]+rT[i]+rC[i]+rG[i]) for i in range(len(rG))]}

    datal = {'A':[cal(Al, i, Al[i]+Tl[i]+Cl[i]+Gl[i]) for i in range(len(Al))], 
             'T':[cal(Tl, i, Al[i]+Tl[i]+Cl[i]+Gl[i]) for i in range(len(Tl))], 
             'C':[cal(Cl, i, Al[i]+Tl[i]+Cl[i]+Gl[i]) for i in range(len(Cl))], 
             'G':[cal(Gl, i, Al[i]+Tl[i]+Cl[i]+Gl[i]) for i in range(len(Gl))]}
    
    rdatal = {'A':[cal(rAl, i, rAl[i]+rTl[i]+rCl[i]+rGl[i]) for i in range(len(rAl))], 
              'T':[cal(rTl, i, rAl[i]+rTl[i]+rCl[i]+rGl[i]) for i in range(len(rTl))], 
              'C':[cal(rCl, i, rAl[i]+rTl[i]+rCl[i]+rGl[i]) for i in range(len(rCl))], 
              'G':[cal(rGl, i, rAl[i]+rTl[i]+rCl[i]+rGl[i]) for i in range(len(rGl))]}

    df   = DataFrame(data)  ;no_negative(df)
    rdf  = DataFrame(rdata) ;no_negative(rdf)
    dfl  = DataFrame(datal) ;no_negative(dfl)
    rdfl = DataFrame(rdatal);no_negative(rdfl)

    pwm_logo = Logo(df)
    pwm_logo.draw()
    plt.savefig(f'{directory}{name}_bs_shorten_pwm.png')
    plt.clf()

    rpwm_logo = Logo(rdf)
    rpwm_logo.draw()
    plt.savefig(f'{directory}{name}_bs_shorten_rpwm.png')
    plt.clf()

    pwml_logo  = Logo(dfl)
    pwml_logo.draw()
    plt.savefig(f'{directory}{name}_bs_shorten_pwml.png')
    plt.clf()
    
    rpwml_logo = Logo(rdfl)
    rpwml_logo.draw()
    plt.savefig(f'{directory}{name}_bs_shorten_rpwml.png')
    plt.clf()