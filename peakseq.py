from constants import ENCODE_CHR, ENCODE_END, ENCODE_FRD, ENCODE_LEN, ENCODE_P, ENCODE_RANK, ENCODE_START, ENCODE_SUMMIT, FDR_SCORE, P_VALUE, SUMMIT
from twobitreader import TwoBitFile
from getopt import getopt
import sys, os


'''
    convert peak-calling application results as annotation to reference sub-sequences in fasta format
    ENCODE peak format column title are stored at '/AKAGI/hmchipdata/Human_hg18_peakcod/contro_peak.cod'
        (directory) -> specific function is implemented to convert all COD files in same directory
'''
def annotation_to_sequences_directory(directory, destination, reference, chipxpress=None):

    def chipxpress_check(filename):
        if chipxpress:
            return filename in chipxpress
        return True            


    genome = TwoBitFile(reference)
    for cod in [f for f in os.listdir(directory) if f.endswith('.cod') and chipxpress_check(f)]:
        with open(directory + cod, 'r') as peakfile, open(destination + cod[:-4]+'.fasta', 'w') as out:
            _ = peakfile.readline().split()
            for peakline_str in peakfile:
                peakline = peakline_str.split()

                # peak-sequence
                chromosome = peakline[1]
                start = int(peakline[2])
                end = int(peakline[3])
                peak_seq = genome[chromosome][start:end]

                # peak-scores
                rank = int(peakline[0])
                fdr = float(peakline[6])
                maxlog2FC = float(peakline[14])

                out.write('> id=%d\n%s\n> scores\nFDR,%f\nmaxlog2FC,%f'%(
                    rank, peak_seq.upper(), fdr, maxlog2FC))


def annotation_to_sequences(cod, reference, fasta:str = ''):
    print('[peakseq] making fasta file from cod-annotation peaks (cod=%s)'%cod)

    if fasta == '':
        fasta = cod[:-4] + '.fasta'

    assert fasta.endswith('.fasta')
    bundle = fasta[:-6] + '.bundle'

    genome = TwoBitFile(reference)
    with open(cod, 'r') as peakfile, open(fasta, 'w') as out, open(bundle, 'w') as out_bundle:
        _ = peakfile.readline().split()
        for peakline_str in peakfile:
            peakline = peakline_str.split()
            
            # peak-sequence
            chromosome = peakline[ENCODE_CHR]
            start = int(peakline[ENCODE_START])
            end = int(peakline[ENCODE_END])
            length = int(peakline[ENCODE_LEN])
            peak_seq = genome[chromosome][start:end+1]

            if length != len(peak_seq):
                print("[ERROR][peakseq] length (%d) and start/end (%d/%d) doesn't match"%(
                    length, start, end
                ))

            # peak-bundle
            rank = int(peakline[ENCODE_RANK])
            fdr = float(peakline[ENCODE_FRD])
            maxlog2FC = float(peakline[ENCODE_P])
            summit = int(peakline[ENCODE_SUMMIT]) - start

            out.write('> id=%d\n%s\n'%(rank, peak_seq.upper()))
            out_bundle.write('> id=%d\n%s,%f\n%s,%f\n%s,%d\n'%(
                rank, FDR_SCORE, fdr, P_VALUE, maxlog2FC, SUMMIT, summit
            ))
    

if __name__ == "__main__":
    # if len(sys.argv) == 1:
    #     raise Exception('peak file name required')

    # arguments and options
    shortopt = 'f:r:asc:d:D:'
    longopts = ['fasta=', 'reference=', 'all', 'special', 'cod=', 'directory=', 'destination=']

    # default values
    args_dict = {'fasta':'', 'reference':'./2bits/hg18.2bit', 'mode':'one', 'directory':'./hmchipdata/Human_hg18_peakcod/',
                    'cod':'./hmchipdata/Human_hg18_peakcod/ENCODE_Broad_GM12878_H3K4me1_peak.cod'}

    opts, args = getopt(sys.argv[1:], shortopt, longopts)
    for o, a in opts:
        if o in ['-f', '--fasta']:
            args_dict.update({'output':a})
        elif o in ['-r', '--reference']:
            args_dict.update({'reference':a})
        elif o in ['-a', '--all']:
            args_dict.update({'mode':'directory'})
        elif o in ['-s', '--special']:
            args_dict.update({'mode':'special'})
        elif o in ['-c', '--cod']:
            args_dict.update({'cod':a})
        elif o in ['-d', '--directory']:
            args_dict.update({'directory':a})
        elif o in ['-D', '--destination']:
            args_dict.update({'destination':a})

            
    if args_dict['mode'] == 'one':
        annotation_to_sequences(args_dict['cod'], args_dict['reference'], args_dict['fasta'])
    elif args_dict['mode'] == 'directory':
        annotation_to_sequences_directory(args_dict['directory'], args_dict['destination'], args_dict['reference'])
    elif args_dict['mode'] == 'special':
        annotation_to_sequences_directory(
            args_dict['directory'], 
            args_dict['destination'], 
            args_dict['reference'])
            