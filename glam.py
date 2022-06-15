from constants import SUMMIT

def read_sites(result_file):
    sites = []
    with open(result_file, 'r') as data:
        _ = data.readline() # ignore header line
        for line in data:
            tokens = line.split()
            sites.append(''.join([symbol.upper() for symbol in tokens[2:-3] if symbol != '.']))
    return sites


def centrality_glam(result_file, s_bundles):
    sum_distances = 0
    num_sites = 0
    with open(result_file, 'r') as data:
        _ = data.readline() # ignore header line
        for line in data:
            tokens = line.split()
            index = int(tokens[0])
            start = int(tokens[1])
            end = int(tokens[-3])
            mid_index = (end + start)//2
            sum_distances += abs(s_bundles[index][SUMMIT] - mid_index)
            num_sites += 1
    return sum_distances / num_sites


if __name__ == '__main__':
    print(SUMMIT)