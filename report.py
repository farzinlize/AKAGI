from functools import reduce
from matplotlib import pyplot
from misc import Queue
import numpy

def location_histogram(motifs, sequences, sequence_mask, save=True, savefilename='figure.png'):
    bins = numpy.linspace(0, max([len(s) for s in sequences]), max([len(s) for s in sequences]))

    histogram_lists = [[] for _ in range(len(sequences))]

    for motif in motifs:
        for index, seq_id in enumerate(motif.found_list[0]):
            for position in motif.found_list[1][index]:
                histogram_lists[seq_id] += [position.start_position]

    alpha = 1 / (reduce((lambda x,y:int(x)+int(y)), sequence_mask))
    for i in range(len(sequences)):
        if int(sequence_mask[i]):
            pyplot.hist(histogram_lists[i], bins, alpha=alpha, label='seq_'+str(i))
    pyplot.legend(loc='upper right')
    
    if save:
        pyplot.savefig(savefilename)
    else:
        pyplot.show()

    pyplot.clf()


def motif_chain_report(motifs, filename, sequences):
    report_kmer = open(filename + '.labels', 'w')
    report_locations = open(filename + '.locations', 'w')
    fasta_result = open(filename + '.fasta', 'w')

    queue = Queue(motifs)
    current_level = 0
    report_kmer.write('> 1-chained\n')
    report_locations.write('> 1-chained\n')
    fasta_result.write('>1-chained\n')
    while not queue.isEmpty():
        link = queue.pop()
        if current_level < link.chain_level:
            current_level = link.chain_level
            report_kmer.write('> %d-chained\n'%(current_level+1))
            report_locations.write('> %d-chained\n'%(current_level+1))
            fasta_result.write('>%d-chained\n'%(current_level+1))
        report_kmer.write(link.chain_sequence()+'\n')
        report_locations.write(link.chain_locations_str()+'\n')
        fasta_result.write(link.instances_str(sequences))
        for child in link.next_chains:
            queue.insert(child)

    report_kmer.close()
    report_locations.close()
    fasta_result.close()

# ########################################## #
#           main fucntion section            #
# ########################################## #

def test_reduce():
    # mask = '110011111000021'
    mask = [1, 0, 0, 1, 0, 1, 1, 0]
    print(reduce(lambda x,y:int(x)+int(y), mask))

def test_savefig():
    # line 1 points 
    x1 = [1,2,3] 
    y1 = [2,4,1] 
    # plotting the line 1 points  
    pyplot.plot(x1, y1, label = "line 1") 
  
    # line 2 points 
    x2 = [1,2,3] 
    y2 = [4,1,3] 
    # plotting the line 2 points  
    pyplot.plot(x2, y2, label = "line 2") 
    
    # naming the x axis 
    pyplot.xlabel('x - axis') 
    # naming the y axis 
    pyplot.ylabel('y - axis') 
    # giving a title to my graph 
    pyplot.title('Two lines on same graph!') 
    
    # show a legend on the plot 
    pyplot.legend() 
    
    # function to show the plot 
    import os
    os.mkdir('.\\results\\new')
    pyplot.savefig('.\\results\\new\\s.png') 

if __name__ == "__main__":
    test_reduce()