from functools import reduce
from matplotlib import pyplot
from misc import Queue
import numpy

def location_histogram_main(motifs, sequences, frame_size):

    print('number of motifs->', len(motifs))
    
    bins = numpy.linspace(0, max([len(s) for s in sequences]), max([len(s) for s in sequences]))

    histogram_lists = [reduce((lambda x,y:x+y), [motif.found_list[1][i] for motif in motifs]) for i in range(len(sequences))]

    alpha = 1 / len(sequences)
    for i in range(len(sequences)):
        pyplot.hist(histogram_lists[i], bins, alpha=alpha, label='seq_'+str(i))

    # pyplot.hist(histogram_lists[0], bins, alpha=0.5, label='seq_1')

    pyplot.legend(loc='upper right')
    pyplot.show()


def location_histogram(motifs, sequences, sequence_mask):
    print('starting to show location histogram (length of lst is %d )'%len(motifs))
    bins = numpy.linspace(0, max([len(s) for s in sequences]), max([len(s) for s in sequences]))
    histogram_lists = [reduce((lambda x,y:x+y), [motif.found_list[1][i] for motif in motifs]) for i in range(len(sequences))]
    alpha = 1 / (reduce((lambda x,y:x+y), sequence_mask))
    for i in range(len(sequences)):
        if sequence_mask[i]:
            pyplot.hist(histogram_lists[i], bins, alpha=alpha, label='seq_'+str(i))
    pyplot.legend(loc='upper right')
    pyplot.show()
    print('exiting the plot function')


def motif_chain_report(motifs, filename):
    with open(filename, 'w') as report:
        queue = Queue(motifs)
        current_level = 0
        report.write('> 1-chained\n')
        while not queue.isEmpty():
            link = queue.pop()
            if current_level < link.chain_level:
                current_level = link.chain_level
                report.write('> %d-chained\n'%(current_level+1))
            report.write(link.chain_sequence()+'\n')
            for child in link.next_chains:
                queue.insert(child)


if __name__ == "__main__":
    location_histogram(1, 6)