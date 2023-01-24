from TrieFind import ChainNode
from misc import ExtraPosition, int_to_bytes, bytes_to_int
from constants import INT_SIZE

class JungleNode(ChainNode):
    def __init__(self, node:ChainNode, id=-1):
        self.label = node.label
        self.foundmap = node.foundmap
        self.id = id

        self.similars:list[JungleNode] = []
        self.bros:list[JungleNode]     = []

    def add_similar(self, similar):
        if similar not in self.similars:self.similars.append(similar)

    def add_bro(self, bro):
        if bro not in self.bros:self.bros.append(bro)


def jungle_to_file(the_jungle:list[JungleNode], filename='a.jungle'):
    with open(filename, 'wb') as result:
        result.write(int_to_bytes(len(the_jungle)))
        for node in the_jungle:
            result.write(int_to_bytes(len(node.bros)))
            for bro in node.bros:result.write(int_to_bytes(bro.id))


def reveal_jungle(motifs:list[ChainNode], filename):
    the_jungle = [JungleNode(each, id=idx) for idx, each in enumerate(motifs)]
    with open(filename, 'rb') as data:
        assert len(the_jungle) == bytes_to_int(data.read(INT_SIZE))
        for me in the_jungle:
            number_of_bros = bytes_to_int(data.read(INT_SIZE))
            for _ in range(number_of_bros):
                new_bro = bytes_to_int(data.read(INT_SIZE))
                me.bros.append(the_jungle[new_bro])
    return the_jungle


def make_jungle(motifs:list[ChainNode], sequences:list[str]) -> list[JungleNode]:
    the_jungle = [JungleNode(each, id=idx) for idx, each in enumerate(motifs)]
    print("jungle size: ", len(the_jungle))

    # similarity check
    for i, me in enumerate(the_jungle):
        for other in [not_me for not_me in the_jungle if not_me != me]:
            for me_instance in me.foundmap.instances_string_list(sequences):
                if me_instance == other.label:
                    me.add_similar(other)
                    break
        print(f'progress: {i}/{len(the_jungle)}', end='\r')
    print("similarity check done")

    # family check
    for i, me in enumerate(the_jungle):
        for other in [not_me for not_me in the_jungle if not_me != me]:
            if me in other.similars and other in me.similars:
                me.add_bro(other)
                other.add_bro(me)
                continue
        print(f'progress: {i}/{len(the_jungle)}', end='\r')
    print("family check done")
    
    return the_jungle