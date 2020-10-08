from Bio import AlignIO
from Bio import SeqIO
from io import StringIO
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq
from Bio import Alphabet
from Bio.Align.Applications import MuscleCommandline

def alignment_matrix(sequences):
    records = [SeqRecord(Seq(sequence, Alphabet.generic_dna)) for sequence in sequences]
    muscle_cline = MuscleCommandline(clwstrict=True, cmd='./muscle')

    handle = StringIO()
    SeqIO.write(records, handle, "fasta")
    data = handle.getvalue()

    stdout, stderr = muscle_cline(stdin=data)
    align = AlignIO.read(StringIO(stdout), "clustal")

    length = align.get_alignment_length()

    # matrix = [[letter for letter in str(entry.seq)] for entry in align]
    return [str(entry.seq) for entry in align]


######################################

if __name__ == "__main__":
    print( alignment_matrix(['GCCGCTGCTGCTGCATCCGTCGACGTCG', 
    'CCGTCGACGTCGAC', 
    'GCAGCGCTGCCGTCGCCGGCTGAGCAGC', 
    'GTCGCAGTCGCTGCC', 
    'CGCTGTTGCGGCCGACGCTGACGCA',
    'CGCTGCCACCGCTG',
    'CAGCGGCTGCGGA']) )