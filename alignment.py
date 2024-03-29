from Bio import AlignIO
from Bio import SeqIO
from io import StringIO
from Bio.SeqRecord import SeqRecord
from Bio.Seq import Seq
from Bio.Align.Applications import MuscleCommandline

def alignment_strings(sequences):
    records = [SeqRecord(Seq(sequence)) for sequence in sequences]
    muscle_cline = MuscleCommandline(clwstrict=True, cmd='muscle')

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
    res = alignment_strings(['AGGAACAGAGTGTTC', 
    'AGGAACAGAGTGTGC', 
    'AGGAACAGAGTGTGC', 
    'AGGAACAGAGTGTTC', 
    'AGGAACAGAGTGTGC',
    'AGGAACAGCTTGTTA',
    'CAGCACAGAGTGCCC', 
    'GTACCAAAGAGAACAAGATGTCACAATTAT',
    'TGTAAAAAGGAACAGAGAGCATCCCATT',
    'AAAGAACAATCAGTACTGAAT',
    'TAGGGAACACAGTGCCAAG',
    'ATAAGCACATAGAGTAC', 
    'GGGAACACAGAGAAA',
    'GAGAACAAGAAGTTT'])

    for i in res:
        print(i)