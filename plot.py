from findmotif import read_fasta, GKHoodTree, find_motif_all_neighbours
from functools import reduce
from matplotlib import pyplot
import numpy

def location_histogram(d, frame_size):
    sequences = read_fasta('data/Real/dm01r.fasta')
    tree = GKHoodTree('gkhood5_8', 'dataset')
    motifs = find_motif_all_neighbours(tree, d, frame_size, sequences, result_kmer=0)
    print('number of motifs->', len(motifs))
    
    bins = numpy.linspace(0, max([len(s) for s in sequences]), max([len(s) for s in sequences]))

    histogram_lists = [reduce((lambda x,y:x+y), [motif.found_list[1][i] for motif in motifs]) for i in range(len(sequences))]

    alpha = 1 / len(sequences)
    for i in range(len(sequences)):
        pyplot.hist(histogram_lists[i], bins, alpha=alpha, label='seq_'+str(i))

    # pyplot.hist(histogram_lists[0], bins, alpha=0.5, label='seq_1')

    pyplot.legend(loc='upper right')
    pyplot.show()

if __name__ == "__main__":
    location_histogram(1, 6)