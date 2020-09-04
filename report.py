from functools import reduce
from matplotlib import pyplot
from misc import Queue
import numpy


class FastaInstance:
    def __init__(self, instance_str):
        instance_lst = instance_str.split(',')
        self.start = int(instance_lst[1])
        self.length = int(instance_lst[3])
        self.end = self.start + self.length
        self.substring = instance_lst[2]
        self.seq_id = int(instance_lst[0])


class OnSequenceAnalysis:
    def __init__(self, sequence_count, sequence_lengths, binding_sites=[], motifs=[]):
        self.bps_tag = [[[0, 0, []] for _ in range(sequence_lengths[seq_index])] for seq_index in range(sequence_count)]
        self.bs_info = []
        self.sFP = 0

        if binding_sites:
            self.add_binding_sites(binding_sites)
        
        if motifs:
            self.add_motifs(motifs)


    def add_motif(self, motif):
        overlap = False
        gard = [True for _ in self.bs_info]
        for i in range(motif.start, motif.end):
            self.bps_tag[motif.seq_id][i][0] += 1
            if self.bps_tag[motif.seq_id][i][1]:
                overlap = True
                for bs_index in self.bps_tag[motif.seq_id][i][2]:
                    if gard[bs_index]:
                        self.bs_info[bs_index][1] += 1
                        gard[bs_index] = False
        if not overlap:
            self.sFP += 1
            

    def add_motifs(self, motifs):
        for motif in motifs:
            self.add_motif(motif)


    def add_binding_site(self, binding_site):
        for i in range(binding_site.start, binding_site.end):
            self.bps_tag[binding_site.seq_id][i][1] += 1
            self.bps_tag[binding_site.seq_id][i][2] += [len(self.bs_info)]
        self.bs_info += [[binding_site, 0]]


    def add_binding_sites(self, binding_sites):
        for bs in binding_sites:
            self.add_binding_site(bs)


    def extract_raw_statistics(self):
        boundle = {'nTP':0, 'nFN':0, 'nFP':0, 'nTN':0, 'sTP':0, 'sFN':0, 'sFP':self.sFP}

        for info in self.bs_info:
            if info[1]:
                boundle['sTP'] += 1
            else:
                boundle['sFN'] += 1

        for sequence in self.bps_tag:
            for bs_info in sequence:
                if bs_info[0] and bs_info[1]:
                    boundle['nTP'] += 1
                elif bs_info[0] and not bs_info[1]:
                    boundle['nFP'] += 1
                elif not bs_info[0] and bs_info[1]:
                    boundle['nFN'] += 1
                else:
                    boundle['nTN'] += 1
        
        return boundle


'''
    (a)lign (P)osition (W)aighted (M)atrix
'''
class aPWM:
    def __init__(self, motifs=[]):
        self.motif_set = motifs
        if motifs:
            self.length = len(motifs[0])
        else:
            self.length = -1

    def score(self):
        position_scores = []
        for position in range(self.length):
            counts = {'A':0, 'T':0, 'C':0, 'G':0, '-':0}
            for motif in self.motif_set:
                counts[motif[position]] += 1
            
            score = max(counts.values())
            if score == counts['-']: score = 0

            position_scores += [score/len(self.motif_set)]
        return (reduce(lambda a,b: a+b, position_scores)) / self.length

    def add_motif(self, motif):
        if self.length == -1:
            self.length = len(motif)
        self.motif_set += [motif]
        

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


def count_overlap(m, b):
    if m.start < b.start:
        if b.start < m.end:
            if m.end <= b.end:
                return m.end - b.start
            return b.length
        return 0
    elif m.start > b.start:
        if m.start < b.end:
            if m.end <= b.end:
                return m.length
            return b.end - m.start
        return 0
    return min(b.length, m.length)


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


def test_count_overlap():
    b = FastaInstance('0,-10,ATTCG,1')
    m = FastaInstance('0,-7,CGATT,2')

    print(count_overlap(m, b))


def test_analysis():
    analysis = OnSequenceAnalysis(3, [15, 15, 15])

    analysis.add_binding_site(FastaInstance('0,-13,nnnnn,5'))
    analysis.add_binding_site(FastaInstance('1,-9,nnnnnn,6'))
    analysis.add_binding_site(FastaInstance('2,-12,nnnn,4'))

    analysis.add_motif(FastaInstance('0,-14,nn,2'))
    analysis.add_motif(FastaInstance('0,-10,nnn,3'))
    analysis.add_motif(FastaInstance('0,-4,nnn,3'))
    analysis.add_motif(FastaInstance('2,-6,nnnn,4'))
    analysis.add_motif(FastaInstance('1,-8,nnnn,4'))
    analysis.add_motif(FastaInstance('2,-14,nnn,3'))

    print(analysis.extract_raw_statistics())


def test_apwm():
    test = aPWM()
    test.add_motif('AATTTCGGG')
    test.add_motif('AATTTCGGG')
    test.add_motif('AATTTCGGG')
    test.add_motif('AATTTCGGG')
    test.add_motif('AATTTCGGG')
    print(test.score())


if __name__ == "__main__":
    test_apwm()