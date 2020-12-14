from twobitreader import TwoBitFile
from getopt import getopt
import sys, os


TWOBITS_LOCATION = './2bits/'


def generate_all(directory, destination, reference):
    genome = TwoBitFile(TWOBITS_LOCATION+reference+'.2bit')
    for filename in os.listdir(directory):
        with open(directory + filename, 'r') as peakfile, open(destination + filename.split('.')[0]+'.fasta', 'w') as out:
            header = peakfile.readline().split()
            for peakline_str in peakfile:
                peakline = peakline_str.split()

                rank = int(peakline[0])
                chromosome = peakline[1]
                start = int(peakline[2])
                end = int(peakline[3])

                peak_seq = genome[chromosome][start:end]
                out.write('> peak_rak=%d\n%s\n'%(rank, peak_seq.upper()))


def generate_fasta(peakfile_address, reference, outputfile):
    genome = TwoBitFile(TWOBITS_LOCATION+reference+'.2bit')
    with open(peakfile_address, 'r') as peakfile, open(outputfile, 'w') as out:
        header = peakfile.readline().split()
        for peakline_str in peakfile:
            peakline = peakline_str.split()

            rank = int(peakline[0])
            chromosome = peakline[1]
            start = int(peakline[2])
            end = int(peakline[3])

            peak_seq = genome[chromosome][start:end]
            out.write('> peak_rak=%d\n%s\n'%(rank, peak_seq.upper()))

    
if __name__ == "__main__":
    if len(sys.argv) == 1:
        raise Exception('peak file name required')

    # arguments and options
    shortopt = 'o:r:a'
    longopts = ['output=', 'reference=', 'all']

    # default values
    args_dict = {'output':'./fasta/o.fasta', 'reference':'hg18', 'all':False}

    peakfile_address = sys.argv[1]

    opts, args = getopt(sys.argv[2:], shortopt, longopts)
    for o, a in opts:
        if o in ['-o', '--output']:
            args_dict.update({'output':a})
        if o in ['-r', '--reference']:
            args_dict.update({'reference':a})
        if o in ['-a', '--all']:
            args_dict.update({'all':True})
            
    if args_dict['all']:
        generate_all(peakfile_address, args_dict['output'], args_dict['reference'])
    else:
        generate_fasta(peakfile_address, args_dict['reference'], args_dict['output'])
            